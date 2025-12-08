# pylint: disable=broad-except,unused-argument,missing-module-docstring,fixme,missing-docstring
# pylint: disable=missing-function-docstring,missing-class-docstring
import threading
from socketserver import ThreadingMixIn
from uuid import uuid4
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import os
import database as DB
from battleship_game import BattleshipGame
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

        # updated after a bully algorithm run, the default value
        # must be set to current main server address before running!
        self.main_server_address = os.getenv("MAIN_SERVER_ADDRESS")
        self.address = os.getenv("SERVER_ADDRESS")
        self.ba_number = os.getenv(
            "BA_NUMBER"
        )
        self.server_address_to_server_ba_number[self.address] = self.ba_number

        self.connection_created = False
        self.election_underway = False

        # fetch server dict from main server on startup
        self._sync_server_dict_from_main()

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
        """Checks if players exist in the database and creates 
        an entry for them if needed, then increases games_lost or games_won."""
        if len(winning_player_name) > 0:
            if DB.get_player_stats(winning_player_name) is None:
                DB.create_database_entry(winning_player_name)
            DB.record_game_results(winning_player_name, won=True)
        if len(losing_player_name) > 0:
            if DB.get_player_stats(losing_player_name) is None:
                DB.create_database_entry(losing_player_name)
            DB.record_game_results(losing_player_name, won=False)

    def get_statistics(self):
        return DB.get_all_stats()

    def _sync_server_dict_from_main(self) -> None:
        """Fetch the server dictionary from the main server on startup."""
        try:
            proxy = self._new_proxy(self.main_server_address, timeout=3)
            server_dict = proxy.send_server_dict()
            if server_dict:
                self.server_address_to_server_ba_number.update(server_dict)
                print(f"[{self.address}] Synced server dict from main: "
                      f"{self.server_address_to_server_ba_number}")
            else:
                print(f"[{self.address}] Main server returned empty dict.")
        except Exception as e:
            print(f"[{self.address}] Failed to sync server dict from main: {e}")
            print(f"[{self.address}] Using local dict only: "
                  f"{self.server_address_to_server_ba_number}")

    def update_server_dict(self, address: str, ba_number: int) -> None:
        """Adds address and ba_number to this game server's dictionary 
        and propagates to all other servers."""
        self.server_address_to_server_ba_number[address] = ba_number
        print("Updated server_address_to_server_ba_number:",
              self.server_address_to_server_ba_number)
        # Broadcast updated dict to all other servers
        self._broadcast_server_dict()

    def _broadcast_server_dict(self) -> None:
        """Send the current server_address_to_server_ba_number to all other servers."""
        for other_addr in self.server_address_to_server_ba_number:
            if other_addr == self.address:
                continue
            try:
                proxy = self._new_proxy(other_addr, timeout=2)
                proxy.receive_server_dict(self.server_address_to_server_ba_number)
            except Exception as e:
                print(f"[{self.address}] Failed to broadcast dict to {other_addr}: {e}")

    def receive_server_dict(self, server_dict: dict) -> str:
        """Receive server_address_to_server_ba_number from another server."""
        self.server_address_to_server_ba_number.update(server_dict)
        print(f"[{self.address}] Updated server dict from peer: "
              f"{self.server_address_to_server_ba_number}")
        return "OK"

    def ping(self, address: str = "", ba_number: int = 0):
        """Receive a ping from another server. Register if new."""
        if (address not in self.server_address_to_server_ba_number) and (address != ""):
            print("Ping received from", address, "with ba_number", ba_number)
            self.update_server_dict(address, ba_number)
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
            result = proxy.ping(self.address, self.ba_number)
            print("Main server reply:", result)
            self.connection_created = True
        except Exception as e:
            print("Error in poll_main_server:", e)
            if self.connection_created and self.election_underway is False:
                print("Lost connection to main server.")
                print("Starting bully algorithm...")
                self.start_bully_algorithm()

        threading.Timer(10, self.poll_main_server).start()

    def send_server_dict(self) -> dict:
        """Returns this game server's dictionary of known servers."""
        return self.server_address_to_server_ba_number

    def start_bully_algorithm(self) -> None:
        """Initiates bully election by sending ELECTION 
        to all LOWER-numbered servers (reverse bully)."""
        if self.election_underway:
            print(f"[{self.address}] Election already underway, not starting another.")
            return
        self.election_underway = True
        lower_nodes_contacted = False

        for other_addr, other_ba in self.server_address_to_server_ba_number.items():
            if other_addr == self.address:
                continue
            if int(other_ba) >= int(self.ba_number):
                continue
            try:
                print(f"[{self.address}] Sending ELECTION to {other_addr} (ba_number {other_ba})")
                proxy = self._new_proxy(other_addr, timeout=3)
                response = proxy.handle_bully_election_msg(int(self.ba_number))
                if response == "OK":
                    lower_nodes_contacted = True
                    print(f"[{self.address}] Received OK from {other_addr}")
            except Exception as e:
                print(f"[{self.address}] Failed to reach {other_addr}: {e}")

        if not lower_nodes_contacted:
            # No lower node responded
            print(f"[{self.address}] No lower nodes found. I am the new coordinator!")
            self.main_server_address = self.address
            self.election_underway = False
            self._announce_coordinator()

    def _announce_coordinator(self) -> None:
        """Announce this server as the new coordinator to all other servers."""
        print(f"[{self.address}] Announcing new coordinator: {self.address}")
        for other_addr in self.server_address_to_server_ba_number:
            print(f"[{self.address}] Announcing to {other_addr}")
            if other_addr == self.address:
                continue
            try:
                proxy = self._new_proxy(other_addr, timeout=3)
                answer = proxy.handle_bully_coordinator_msg(self.address, int(self.ba_number))
                print(f"[{self.address}] {other_addr} replied: {answer}")
            except Exception as e:
                print(f"[{self.address}] Failed to announce to {other_addr}: {e}")


    def handle_bully_coordinator_msg(self, new_coordinator_address:
                                     str, new_coordinator_ba: int) -> str:
        """Receive COORDINATOR announcement. Accept only 
        if sender has LOWER BA (higher priority)."""
        if int(new_coordinator_ba) < int(self.ba_number):
            print(f"[{self.address}] New coordinator announced: {new_coordinator_address}")
            self.main_server_address = new_coordinator_address
            self.election_underway = False
            return "OK"
        print(f"[{self.address}] Ignoring higher-priority coordinator "
              f"{new_coordinator_address} ({new_coordinator_ba})")
        return "IGNORED"

    def handle_bully_election_msg(self, ba_number: int) -> str:
        """Receive ELECTION from another node. Reply OK immediately, 
        then start our own election in background."""
        print(f"[{self.address}] Received ELECTION message from ba_number {ba_number}")
        if int(self.ba_number) < int(ba_number):
            # Start election in background thread
            threading.Thread(target=self.start_bully_algorithm, daemon=True).start()
        return "OK"


server = ThreadedXMLRPCServer(("localhost", 8000), allow_none=True)
server.allow_reuse_address = True
server.register_instance(GameServer())
print("Battleship XML-RPC server running on port 8000...")
server.serve_forever()
