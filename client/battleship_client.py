import os
import traceback
import xmlrpc.client
from xmlrpc.client import ServerProxy

from flask import Flask, jsonify, make_response, request, send_file


class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=5, use_datetime=False):
        super().__init__(use_datetime=use_datetime)
        self.timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        if hasattr(conn, 'timeout'):
            conn.timeout = self.timeout
        return conn


def _new_proxy(timeout=5):
    return ServerProxy("http://localhost:8000", allow_none=True, transport=TimeoutTransport(timeout=timeout))


app = Flask(__name__, static_folder=None)


@app.route('/', methods=['GET'])
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))


@app.route('/api/join', methods=['POST'])
def api_join():
    try:
        proxy = _new_proxy()
        res = proxy.register_player()
        if res == 1 or res == 2:
            response = make_response(jsonify(res))
            response.set_cookie("player_id", str(res))
            return response
        else:
            return jsonify({'error': + res}), 500
    except Exception as e:
        print("RPC start error:", e)
        print(traceback.format_exc())
        return jsonify({'error': 'rpc error: ' + str(e)}), 500


@app.route('/api/start', methods=['POST'])
def api_start():
    try:
        proxy = _new_proxy()
        res = proxy.start_game()
    except Exception as e:
        print("RPC start error:", e)
        print(traceback.format_exc())
        return jsonify({'error': 'rpc error: ' + str(e)}), 500
    return jsonify(res)


@app.route('/api/fire', methods=['POST'])
def api_fire():
    data = request.get_json(force=True)
    row = data.get('row')
    col = data.get('col')
    try:
        proxy = _new_proxy()
        res = proxy.fire(int(request.cookies.get("player_id")), row, col)
    except Exception as e:
        print("RPC fire error:", e)
        print(traceback.format_exc())
        return jsonify({'error': 'rpc error: ' + str(e)}), 500
    return jsonify(res)


@app.route('/api/state', methods=['GET'])
def api_state():
    try:
        proxy = _new_proxy()
        res = proxy.get_state()
    except Exception as e:
        print("RPC state error:", e)
        print(traceback.format_exc())
        return jsonify({'error': 'rpc error: ' + str(e)}), 500
    return jsonify(res)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
