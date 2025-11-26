Client setup:

1. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`.
2. Install required packages: `pip install -r requirements.txt`
3. Create a .env file in the folder with `battleship_client.py` and set the `MAIN_SERVER_CLOUDFLARED_ADDRESS` env variable to the cloudflared given address of the **main** game server.
4. Start the client: `python battleship_client.py`.

Server setup:

1. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`.
2. Install required packages: `pip install -r requirements.txt`
3. Create a .env file in the folder with `battleship_server.py` and set the `CLOUDFLARED_ADDRESS` env variable to the cloudflared given address of the server (or use `"localhost:<port>"` if testing).
4. Also set the `MAIN_SERVER_CLOUDFLARED_ADDRESS` env variable to the cloudflared given address of the **main** game server.
5. Start the server: `python battleship_server.py`.

To run `example_database_connection.py`:

1. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
2. Install required packages: `pip install -r requirements.txt`
3. Create a .env file in the root folder and set the `DATABASE_PASSWORD` env variable to the password of the database
4. Run the file: `python example_database_connection.py`
5. Add `SERVERLIST` variable to .env file and list all available servers under that.

    Example: ```SERVERLIST=http://localhost:8000,https://battleship.example.com```
