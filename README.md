Client:

The client might be available at `https://decorating-species-newfoundland-organize.trycloudflare.com/`. If it's unavailable, the client program can also be hosted locally:

1. Download the client directory from the GitHub repository and open it
2. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install required packages: `pip install -r requirements.txt`
4. The .env file in the client directory contains a list of game server URLs. You can optionally add your local server on the list, and it will appear in the server dropdown list in the client. Example: `SERVERLIST=http://localhost:8000,https://battleship.example.com`. You can also change the `LOCALHOST_PORT_NUMBER` to change what port the client runs on.
5. Start the client: `python battleship_client.py`

Server:

When the GameServer is started, it checks if the database file `statistics_database.db` exists, and creates it if not. To host the server locally:

1. Download the server directory from the GitHub repository and open it
2. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install required packages: `pip install -r requirements.txt`
4. Create a .env file in the root folder and:
    - set the `LOCALHOST_PORT_NUMBER` env variable to the port that you want the server to run on (e.g. 8000)
    - set the `SERVER_ADDRESS` env variable to the address of this server, for example `http://localhost:8000` or `https://battleship.example.com`.
    - set the `SERVERLIST` env variable to the address of one or more other servers (if no servers are given, this server becomes the main server). For example, `http://localhost:8001` or `https://battleship.example2.com`.
    - set the `BA_NUMBER` env variable to the integer that is used on the Bully Algorithm for this server (make sure this is different for all servers). This is used to determine a new main server in case none exists yet or the previous one goes offline. The lowest ID wins.
5. Run the file: `python battleship_server.py`
