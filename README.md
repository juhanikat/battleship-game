Client:

The client uses remote procedure calls to join a game, start the game, fire at a coordinate on the map and to periodically get the status of the game from the server.

The client should be available at `https://sauce-tennis-used-profession.trycloudflare.com/`. If it's unavailable, the client program can also be hosted locally:

1. Download the client directory from the GitHub repository and open it
2. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install required packages: `pip install -r requirements.txt`
4. The .env file in the client directory contains a list of game server URLs. You can optionally add your local server on the list, and it will appear in the server dropdown list in the client. Example: `SERVERLIST=http://localhost:8000,https://battleship.example.com`
5. Start the client: `python battleship_client.py`

Server:

When the GameServer is started, it checks if the database file `statistics_database.db` exists, and creates it if not.
