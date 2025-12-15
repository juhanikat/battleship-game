# pylint: disable=broad-except,unused-argument,missing-module-docstring,fixme,missing-docstring
# pylint: disable=missing-function-docstring,missing-class-docstring,import-error
import os
import sys
import traceback
import xmlrpc.client
from xmlrpc.client import ServerProxy

from dotenv import find_dotenv, load_dotenv
from flask import Flask, Response, jsonify, make_response, request, send_file

load_dotenv(find_dotenv() or None)


class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=5, use_datetime=False):
        super().__init__(use_datetime=use_datetime)
        self.timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        if hasattr(conn, 'timeout'):
            conn.timeout = self.timeout
        return conn


def handle_error(error, message: str, error_code: int = 500) -> Response:
    """Prints information about an error and return a json Response."""
    print(message, error)
    print(traceback.format_exc())
    return jsonify({'error': f"{message}: {error}"}), error_code


def _new_proxy(timeout=5):
    return ServerProxy(request.cookies.get("server_url"),
                       allow_none=True,
                       transport=TimeoutTransport(timeout=timeout))


app = Flask(__name__, static_folder=None)


@app.route('/', methods=['GET'])
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))


@app.route('/api/join', methods=['POST'])
def api_join():
    """Called once the user presses the Join Game button."""
    player_name = request.json["playerName"].strip()
    try:
        proxy = _new_proxy()
        res = proxy.register_player(player_name)
        print(res)
        if res[0] == 1 or res[0] == 2:
            response = make_response(jsonify(res))
            response.set_cookie("player_id", str(res[0]))
            response.set_cookie("game_id", str(res[1]))
            return response
        return handle_error(res, "Error in /api/join", 400)
    except Exception as error:
        return handle_error(error, "Error in /api/join")


@app.route('/api/start', methods=['POST'])
def api_start():
    """Called once the user presses the Srart New Game button."""
    try:
        proxy = _new_proxy()
        # server exposes `new_game`; call that RPC
        res = proxy.new_game()
    except Exception as error:
        return handle_error(error, "Error in /api/start")
    return jsonify(res)


@app.route('/api/fire', methods=['POST'])
def api_fire():
    """Called when the user clicks a coordinate on their opponent's grid."""
    data = request.get_json(force=True)
    row = data.get('row')
    col = data.get('col')
    try:
        proxy = _new_proxy()
        game_id = request.cookies.get("game_id")
        player_id = int(request.cookies.get("player_id")
                        ) if request.cookies.get("player_id") else None
        res = proxy.fire(game_id, player_id, row, col)
    except Exception as error:
        return handle_error(error, "Error in /api/fire")
    return jsonify(res)


@app.route('/api/state', methods=['GET'])
def api_state():
    """Called automatically every 2 seconds once the game has started."""
    try:
        proxy = _new_proxy()
        game_id = request.cookies.get("game_id")
        res = proxy.get_state(game_id)
    except Exception as error:
        return handle_error(error, "Error in /api/state")
    return jsonify(res)


def _proxy_for(server_url: str, timeout=2):
    """Create a ServerProxy for a given server URL (adds http:// if missing)."""
    if not server_url:
        raise ValueError("server_url required")
    s = server_url.strip()
    if not s.startswith("http://") and not s.startswith("https://"):
        s = "http://" + s
    return ServerProxy(s, allow_none=True, transport=TimeoutTransport(timeout=timeout))


def fetch_servers() -> dict:
    """Called internally by the client to fetch a server list.
    Loops through servers in SERVERLIST env variable and tries to fetch the server dict from them.
    Remember to call this in a try-except block!"""
    servers = []
    for env_server in (os.getenv("SERVERLIST")).split(","):
        try:
            proxy = _proxy_for(env_server)
            servers = list(proxy.send_server_dict().keys())
            break
        except Exception as _:
            continue

    if not servers:
        raise RuntimeError(
            "Could not get the server dict from any known server")

    return servers


@app.route('/api/ping_all', methods=['GET'])
def api_ping_all():
    """Ping every server from fetch_servers() and return success/error for each."""
    servers = []
    try:
        try:
            servers = fetch_servers()
        except Exception as fetch_servers_error:
            return handle_error(fetch_servers_error, "Error in fetch_servers()")

        results = []
        for s in servers:
            try:
                proxy = _proxy_for(s, timeout=2)
                # call a lightweight RPC (ping). If you want full state, call get_state()
                pong = proxy.ping()
                results.append({"server": s, "ok": True, "pong": pong})
            except Exception as e:
                results.append({"server": s, "ok": False, "error": str(e)})
        return jsonify(results)
    except Exception as e:
        return handle_error(e, "Error in /api/ping_all")


@app.route('/api/config', methods=['GET'])
def api_config() -> Response:
    """Returns server configuration such as available servers."""
    try:
        servers = fetch_servers()
        config = {'servers': servers, 'default': servers[0]}
        return jsonify(config)
    except Exception as e:
        return handle_error(e, "Error in /api/config")


@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    try:
        proxy = _new_proxy()
        res = proxy.get_statistics()
    except Exception as error:
        return handle_error(error, "Error in /api/statistics")
    return jsonify(res)


@app.route('/api/quit', methods=['POST'])
def api_quit():
    """Resets cookies and sends player back to server select screen. 
    Once one player quits the game, the other will be shown a message 
    that tells them to refresh the page to join a new game."""
    try:
        game_id = request.cookies.get("game_id")
        player_id = request.cookies.get("player_id")
        proxy = _new_proxy()
        res = proxy.quit(game_id, player_id)
        response = make_response(jsonify(res))
        response.set_cookie("player_id", "", expires=0)
        response.set_cookie("game_id", "", expires=0)
    except Exception as e:
        return handle_error(e, "Error in /api/quit")
    return response


try:
    # get the port number from the env
    port_number = int(os.getenv("LOCALHOST_PORT_NUMBER"))
except Exception as e:
    print("Invalid or missing LOCALHOST_PORT_NUMBER env variable!")
    sys.exit()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=port_number, debug=True, threaded=True)
