import random
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class BattleshipGame:
    def __init__(self):
        self.grid_size = 5
        self.ship_sizes = [3, 2]
        self.reset()

    def reset(self):
        self.p1_grid = self.create_grid()
        self.p2_grid = self.create_grid()
        self.p1_tracking = self.create_grid()
        self.p2_tracking = self.create_grid()
        self.current_player = 1
        self.winner = None

    def create_grid(self):
        return [["~" for _ in range(self.grid_size)] for _ in range(self.grid_size)]

    def _place_ship_coords(self, grid, size, r, c, direction):
        coords = []
        for i in range(size):
            rr = r + (i if direction == "V" else 0)
            cc = c + (i if direction == "H" else 0)
            if rr < 0 or rr >= self.grid_size or cc < 0 or cc >= self.grid_size:
                return False
            if grid[rr][cc] == "S":
                return False
            coords.append((rr, cc))
        for rr, cc in coords:
            grid[rr][cc] = "S"
        return True

    def _auto_place_for(self, grid):
        for size in self.ship_sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 200:
                r = random.randrange(self.grid_size)
                c = random.randrange(self.grid_size)
                direction = random.choice(["H", "V"])
                if self._place_ship_coords(grid, size, r, c, direction):
                    placed = True
                attempts += 1
            if not placed:
                for _ in range(10):
                    pass
        return True

    def start_game(self):
        self.reset()
        self._auto_place_for(self.p1_grid)
        self._auto_place_for(self.p2_grid)
        return True

    def _all_ships_sunk(self, grid):
        for row in grid:
            if "S" in row:
                return False
        return True

    def fire(self, row, col):
        if self.winner is not None:
            return {"error": "game over", "winner": self.winner}

        try:
            row = int(row)
            col = int(col)
        except:
            return {"error": "invalid coordinates"}

        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return {"error": "out of bounds"}

        if self.current_player == 1:
            opponent_grid = self.p2_grid
            tracking = self.p1_tracking
        else:
            opponent_grid = self.p1_grid
            tracking = self.p2_tracking

        if tracking[row][col] in ["X", "O"]:
            return {"error": "already fired"}

        if opponent_grid[row][col] == "S":
            tracking[row][col] = "X"
            opponent_grid[row][col] = "X"
            result = "hit"
        else:
            tracking[row][col] = "O"
            opponent_grid[row][col] = "O"
            result = "miss"

        if self._all_ships_sunk(opponent_grid):
            self.winner = self.current_player
            return {"result": result, "winner": self.winner, "next_player": None}

        self.current_player = 2 if self.current_player == 1 else 1
        return {"result": result, "winner": None, "next_player": self.current_player}

    def get_state(self):
        return {
            "p1_grid": self.p1_grid,
            "p2_grid": self.p2_grid,
            "p1_tracking": self.p1_tracking,
            "p2_tracking": self.p2_tracking,
            "current_player": self.current_player,
            "winner": self.winner,
            "grid_size": self.grid_size,
            "ship_sizes": self.ship_sizes,
        }


server = ThreadedXMLRPCServer(("localhost", 8000), allow_none=True)
server.allow_reuse_address = True
server.register_instance(BattleshipGame())
print("Battleship XML-RPC server running on port 8000...")
server.serve_forever()
