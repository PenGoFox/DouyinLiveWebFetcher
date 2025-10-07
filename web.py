from flask import Flask, jsonify
import threading

from logger import msgLogger
import Global

class Web:
    def __init__(self, host, port):
        self._web = Flask(__name__)
        self._host = host
        self._port = port

        self._setup_routes()

    def run(self, threaded=True, debug=False):
        msgLogger.info(f"web 服务启动在 http://{self._host}:{self._port}")
        self._web.run(host=self._host, port=self._port, threaded=threaded,debug=debug)

    def runInThread(self, daemon=True):
        t = threading.Thread(
            target=self.run,
            daemon=daemon
        )
        t.start()
        return t

    def _setup_routes(self):
        @self._web.route('/')
        def page_home():
            return jsonify({
                "enable": "true"
            })

        @self._web.route('/streaming')
        def page_streaming():
            return jsonify({
                "streaming": Global.isLiveStreaming
            })

        @self._web.route('/recording')
        def page_recording():
            return jsonify({
                "recording": Global.isRecording
            })