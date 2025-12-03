from socketserver import ThreadingMixIn
from uuid import uuid4
from xmlrpc.server import SimpleXMLRPCServer

import database as DB
from battleship_game import BattleshipGame


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class GameServer():
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

    def new_game(self):
        create_game = (BattleshipGame())
        create_game.start_game()
        self.games[self.new_game_id] = create_game
        self.game_to_player_name[self.new_game_id] = {
            1: self.first_player_name, 2: self.second_player_name}
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
            self.record_statistics(
                winning_player_name, losing_player_name)

        return result
    
    def quit(self, game_id, player_id: int):
        result = self.games[game_id].cancel_game(player_id)
        return result

    def record_statistics(self, winning_player_name: str, losing_player_name: str) -> None:
        """Checks if players exist in the database and creates an entry for them if needed, then increases games_lost or games_won."""
        if len(winning_player_name) > 0:
            if DB.get_player_stats(winning_player_name) == None:
                DB.create_database_entry(winning_player_name)
            DB.record_game_results(winning_player_name, won=True)
        if len(losing_player_name) > 0:
            if DB.get_player_stats(losing_player_name) == None:
                DB.create_database_entry(losing_player_name)
            DB.record_game_results(losing_player_name, won=False)

    def ping(self):
        return "pong"


server = ThreadedXMLRPCServer(("localhost", 8000), allow_none=True)
server.allow_reuse_address = True
server.register_instance(GameServer())
print("Battleship XML-RPC server running on port 8000...")
server.serve_forever()
