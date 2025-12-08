Client:

The client uses remote procedure calls to join a game, start the game, fire at a coordinate on the map and to periodically get the status of the game from the server.

The client should be available at `https://sauce-tennis-used-profession.trycloudflare.com/`. If it's unavailable, the client program can also be hosted locally:

1. Download the client directory from the GitHub repository and open it
2. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install required packages: `pip install -r requirements.txt`
4. The .env file in the client directory contains a list of game server URLs. You can optionally add your local server on the list, and it will appear in the server dropdown list in the client. Example: `SERVERLIST=http://localhost:8000,https://battleship.example.com`
5. Start the client: `python battleship_client.py`

Server:

When the GameServer is started, it checks if the database file `statistics_database.db` exists, and creates it if not. To host the server locally:

1. Download the server directory from the GitHub repository and open it
2. Create a virtual environment `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install required packages: `pip install -r requirements.txt`
4. Create a .env file in the root folder and:
    - set the `MAIN_SERVER_ADDRESS` env variable to the address of the main server (same as this server's address if this is the main server)
    - set the `SERVER_ADDRESS` env variable to the address of this server (e.g. https://battleship.example.com)
    - set the `BA_NUMBER` env variable to the integer that is used on the Bully Algorithm for this server (make sure this is different for all servers)
5. Run the file: `python battleship_server.py`

# Main Server and Bully Algorithm

One of the nodes is designated as a main server. When a new node is added to the system, the current main server's IP address is hardcoded into it. Then:

1. The new server sends the main server a message containing it's IP address and its bully algorithm number. The main server keeps a dictionary mapping each server's address to it's BA number.
2. All other servers periodically poll the main server, and get the new server's address and BA number in this way.

## Bully Algorithm

When the main server goes offline, the servers vote for a new a main server using a bully algorithm. Note that no new servers can be added to the system while the algorithm is in progress.

NOTE: This algorithm will result in multiple main servers unless every server knows about each other!

Let's say we have nodes with BA numbers 1, 2, 3 and 4. The algorithm chooses the lowest BA number as the main server, so node 1 is currently the leader.

1. Node 1 goes offline, and node 3 notices this (due to the periodic polling for IP addresses described above).
2. Node 3 sends an election message to each node that has a BA number lower than 3 (Node 2). (In this implementation, there is no need for OK messages. If a node does not know any nodes that have lower BA numbers, then that node becomes the leader.)
3. Since there are no online nodes with a BA number lower than 2, node 2 becomes the new leader and sends a Coordinator message to nodes 3 and 4. It also keeps checking node 1's status periodically.
4. Nodes 3 and 4 updated their main_server_address variable to node 2's address.
5. When node 1 comes back online, node 2 will notice this and start a new election, which will result in node 1 becoming the leader. Node 2 will then send its copy of the statistics table to node 1, which will replace its local copy with that table.
