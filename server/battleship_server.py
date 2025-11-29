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
        self.wait_for_second = False
        self.new_game_id = 0
        if not DB.scores_exist():
            DB.init_database(insert_test_data=True)
        print(DB.create_database_entry("kolmas"))
        print(DB.get_all_stats())
        print(DB.get_player_stats(1))
        print(DB.get_player_stats(2))
        print(DB.get_player_stats(3))

    def new_game(self):
        create_game = (BattleshipGame())
        create_game.start_game()
        self.games[self.new_game_id] = create_game
        return True

    def register_player(self):
        if not self.wait_for_second:
            self.wait_for_second = True
            self.new_game_id = str(uuid4())
            print(1, self.new_game_id)
            return (1, self.new_game_id)
        elif self.wait_for_second:
            self.wait_for_second = False
            self.new_game()
            print(2, self.new_game_id)
            return (2, self.new_game_id)

    def get_state(self, game_id):
        return self.games[game_id].get_state()

    def fire(self, game_id, player_id: int, row, col):
        return self.games[game_id].fire(player_id, row, col)

    def ping(self):
        return "pong"


server = ThreadedXMLRPCServer(("localhost", 8000), allow_none=True)
server.allow_reuse_address = True
server.register_instance(GameServer())
print("Battleship XML-RPC server running on port 8000...")
server.serve_forever()
