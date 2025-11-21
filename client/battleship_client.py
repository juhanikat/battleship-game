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
        if res == 1 or res == 2:
            response = make_response(jsonify(res))
            response.set_cookie("player_id", str(res))
            return response
        return handle_error(res, "Error in /api/join", 400)
    except Exception as error:
        return handle_error(error, "Error in /api/join")


@app.route('/api/start', methods=['POST'])
def api_start():
    """Called once the user presses the Srart New Game button."""
    try:
        proxy = _new_proxy()
        res = proxy.start_game()
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
        res = proxy.fire(int(request.cookies.get("player_id")), row, col)
    except Exception as error:
        return handle_error(error, "Error in /api/fire")
    return jsonify(res)


@app.route('/api/state', methods=['GET'])
def api_state():
    """Called automatically every 2 seconds once the game has started."""
    try:
        proxy = _new_proxy()
        res = proxy.get_state()
    except Exception as error:
        return handle_error(error, "Error in /api/state")
    return jsonify(res)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
