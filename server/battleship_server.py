from socketserver import ThreadingMixIn
from uuid import uuid4
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import os
import database as DB
from battleship_game import BattleshipGame
import threading
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv() or None)


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=5, use_datetime=False):
        super().__init__(use_datetime=use_datetime)
        self.timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        if hasattr(conn, "timeout"):
            conn.timeout = self.timeout
        return conn


class GameServer:
    def __init__(self):
        self.games = {}
        # matches game_id to a dictionary containing both players' name and player number
        # Example:
        # 9f2a0d11-2efd: {1: "Juhani", 2: "VP"}
        self.game_to_player_name = {}

        self.wait_for_second = False
        self.new_game_id = 0

        self.first_player_name = ""
        self.second_player_name = ""

        if not DB.scores_exist():
            DB.init_database(insert_test_data=True)

        # matches every known server's address to their Bully Algorithm number
        # Example:
        # { https://server1.trycloudflare.com: "12", https://server2.trycloudflare.com: "3" }
        self.server_address_to_server_ba_number = {}

        # updated after a bully algorithm run, the default value must be set to current main server address before running!
        self.main_server_address = os.getenv("MAIN_SERVER_ADDRESS")
        self.address = os.getenv("SERVER_ADDRESS")
        self.ba_number = os.getenv(
            "BA_NUMBER"
        )  # number used for ID in the Bully Algorithm

        # polls main server every 10 seconds
        self.poll_main_server()

    def new_game(self):
        create_game = BattleshipGame()
        create_game.start_game()
        self.games[self.new_game_id] = create_game
        self.game_to_player_name[self.new_game_id] = {
            1: self.first_player_name,
            2: self.second_player_name,
        }
        return True

    def register_player(self, player_name: str):
        if not self.wait_for_second:
            self.wait_for_second = True
            self.first_player_name = player_name
            self.new_game_id = str(uuid4())
            print(1, self.new_game_id)
            return (1, self.new_game_id)
        elif self.wait_for_second:
            self.wait_for_second = False
            self.second_player_name = player_name
            self.new_game()
            print(2, self.new_game_id)
            return (2, self.new_game_id)

    def get_state(self, game_id):
        return self.games[game_id].get_state()

    def fire(self, game_id, player_id: int, row, col):
        result = self.games[game_id].fire(player_id, row, col)
        if "winner" in result.keys() and result["winner"] is not None:
            # game is over, record statistics for both players
            winner = result["winner"]
            loser = 1 if winner == 2 else 2
            winning_player_name = self.game_to_player_name[game_id][winner]
            losing_player_name = self.game_to_player_name[game_id][loser]
            self.record_statistics(winning_player_name, losing_player_name)

        return result
    
    def quit(self, game_id, player_id: int):
        result = self.games[game_id].cancel_game(player_id)
        return result

    def record_statistics(
        self, winning_player_name: str, losing_player_name: str
    ) -> None:
        """Checks if players exist in the database and creates an entry for them if needed, then increases games_lost or games_won."""
        if len(winning_player_name) > 0:
            if DB.get_player_stats(winning_player_name) == None:
                DB.create_database_entry(winning_player_name)
            DB.record_game_results(winning_player_name, won=True)
        if len(losing_player_name) > 0:
            if DB.get_player_stats(losing_player_name) == None:
                DB.create_database_entry(losing_player_name)
            DB.record_game_results(losing_player_name, won=False)

    def get_statistics(self):
        return DB.get_all_stats()

    def ping(self):
        return "pong"

    def _new_proxy(self, address: str, timeout=5):
        """Used for server-to-server communication."""
        return ServerProxy(
            address, allow_none=True, transport=TimeoutTransport(timeout=timeout)
        )

    def is_main_server(self) -> bool:
        """Return True if this server is the current main server, or False otherwise."""
        return self.main_server_address == self.address

    def poll_main_server(self):
        """Periodically requests addresses and statistics data from the main server."""
        try:
            proxy = self._new_proxy(self.main_server_address)
            result = proxy.ping()
            print("Main server reply:", result)
        except Exception as e:
            print("Error in poll_main_server:", e)

        threading.Timer(10, self.poll_main_server).start()

    def update_server_dict(self, address: str, ba_number: int) -> None:
        """Adds address and ba_number to this game server's dictionary."""
        self.server_address_to_server_ba_number[address] = ba_number
        if self.is_main_server():
            # propagate update to each other server
            for server_address in self.server_address_to_server_ba_number.keys():
                if server_address == self.address or server_address == address:
                    continue
                proxy = self._new_proxy(server_address)
                proxy.update_server_dict(address, ba_number)

    def handle_bully_election_msg(self) -> None:
        """Calls handle_bully_election_msg() in each known server with a lower ba_number than this server's own ba_number.
        If no nodes with lower ba_numbers are known, then this server becomes the new main server.
        """
        lower_node_found = False
        for (
            other_server_address,
            other_server_ba_number,
        ) in self.server_address_to_server_ba_number.items():
            if (
                other_server_address == self.address
                or other_server_ba_number > self.ba_number
            ):
                continue
            proxy = self._new_proxy(other_server_address)
            proxy.handle_bully_election_msg(
                self.address
            )  # send Election messages to each lower node
            lower_node_found = True

        if not lower_node_found:
            # this server becomes the new main server
            for other_server_address in self.server_address_to_server_ba_number.keys():
                if other_server_address == self.address:
                    continue
            proxy = self._new_proxy(other_server_address)
            proxy.handle_bully_coordinator_msg(
                self.address
            )  # send Coordinator messages to each other node

    def handle_bully_coordinator_msg(self, new_coordinator_address: str) -> None:
        """Sets the caller as the new main server."""
        self.main_server_address = new_coordinator_address

    def start_bully_algorithm(self) -> None:
        """Starts the bully algorithm, see handle_bully_election_msg."""
        self.handle_bully_election_msg("")


server = ThreadedXMLRPCServer(("localhost", 8000), allow_none=True)
server.allow_reuse_address = True
server.register_instance(GameServer())
print("Battleship XML-RPC server running on port 8000...")
server.serve_forever()
