import sqlite3
from typing import TypedDict


class Stats(TypedDict):
    player_id: int
    player_name: str
    matches_won: int
    matches_lost: int


def database_entry_to_stats(result: tuple) -> Stats:
    """Converts a database entry into a Stats dict."""
    stats: Stats = {
        "player_id": result[0],
        "player_name": result[1],
        "games_won": result[2],
        "games_lost": result[3]
    }
    return stats


def init_database(insert_test_data: bool = False):
    """Called when a game server starts to create the database and the statistics table."""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    # this seems to be automatically committed, resulting in weird behavior if the function fails after this line
    cur.execute(
        "CREATE TABLE statistics(player_id INTEGER PRIMARY KEY AUTOINCREMENT, player_name UNIQUE, games_won, games_lost)")

    if insert_test_data:
        cur.execute(
            "INSERT INTO statistics(player_name, games_won, games_lost) VALUES('Juhani', 0, 0)")
        cur.execute(
            "INSERT INTO statistics(player_name, games_won, games_lost) VALUES('VP', 1, 2)")

    con.commit()
    con.close()


def scores_exist():
    """Returns True if the statistics table exists (init_database() has been called), or False otherwise."""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='statistics'")
    table_name = cur.fetchone()
    con.close()

    if table_name == None:
        return False
    return True


def get_all_stats() -> list[Stats] | None:
    """Returns a list of Stats dicts for all players in database, or None if the database is empty."""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    cur.execute(
        "SELECT player_id, player_name, games_won, games_lost FROM statistics")
    result = cur.fetchall()
    con.commit()
    con.close()

    if result:
        all_statistics = []
        for entry in result:
            all_statistics.append(database_entry_to_stats(entry))
        return all_statistics
    return None


def get_player_stats(player_id: int) -> Stats | None:
    """Returns the Stats dict of a player if found, or None otherwise."""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    cur.execute(
        "SELECT player_id, player_name, games_won, games_lost FROM statistics WHERE player_id = ?", [(player_id)])
    result = cur.fetchone()
    con.commit()
    con.close()

    if result:
        return database_entry_to_stats(result)
    return None


def create_database_entry(player_name: str) -> None:
    """Adds a new player into the statistics table, and returns their ID. Creating a player with an existing name results in an error!"""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO statistics(player_name, games_won, games_lost) VALUES(?, 0, 0)", [
                player_name])
    cur.execute("SELECT player_id FROM statistics WHERE player_name = ?", [
                player_name])
    result = cur.fetchone()
    con.commit()
    con.close()

    return result[0]


def record_game_results(player_id: int, won: bool) -> None:
    """Increases either games_won or games_lost."""
    con = sqlite3.connect("statistics_database.db")
    cur = con.cursor()
    if won:
        cur.execute(
            "UPDATE statistics SET games_won = games_won + 1 WHERE player_id = ?", [(player_id)])
    else:
        cur.execute(
            "UPDATE statistics SET games_lost = games_lost + 1 WHERE player_id = ?", [(player_id)])
    con.commit()
    con.close()
