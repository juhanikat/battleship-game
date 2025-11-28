import os
import traceback
import xmlrpc.client
from xmlrpc.client import ServerProxy

from flask import Flask, Response, jsonify, make_response, request, send_file


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
    return ServerProxy("http://localhost:8000", allow_none=True, transport=TimeoutTransport(timeout=timeout))


app = Flask(__name__, static_folder=None)


@app.route('/', methods=['GET'])
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))


@app.route('/api/join', methods=['POST'])
def api_join():
    """Called once the user presses the Join Game button."""
    try:
        proxy = _new_proxy()
        res = proxy.register_player()
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
        player_id = int(request.cookies.get("player_id")) if request.cookies.get("player_id") else None
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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
