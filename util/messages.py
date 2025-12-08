# pylint: disable=broad-except,unused-argument,missing-module-docstring,fixme,missing-docstring
# pylint: disable=missing-function-docstring,missing-class-docstring,too-few-public-methods
from typing import TypedDict


class FireRequestMsg:
    """Sent from a client to the game server when the user fires at a coordinate."""

    def __init__(self, game_id: int, player_id: int, coordinate: tuple[int, int]):
        self.game_id = game_id
        self.player_id = player_id
        self.coordinate = coordinate


class GameStatus(TypedDict):
    p1_grid: list[list[str]]
    p2_grid: list[list[str]]
    p1_tracking: list[list[str]]
    p2_tracking: list[list[str]]
    current_player: int
    winner: int | None
    grid_size: int
    ship_sizes: list[int]


class GameStatusMsg:
    """Contains the current status of the game. Sent from a game server to a client."""

    def __init__(self, status: GameStatus):
        self.status = status


class ScoreboardUpdateMsg:
    """Sent to and from the main game server to update scoreboard information."""

    def __init__(self):
        pass


class IPShareMsg:
    """Sent to clients and game servers to share the IP addresses of every machine."""

    def __init__(self):
        pass


class BullyElectionMsg:

    def __init__(self):
        pass


class BullyOKMsg:

    def __init__(self):
        pass


class BullyCoordinatorMsg:

    def __init__(self):
        pass
