import errno
import http.server
import functools
import socketserver
import threading
from typing import Callable, Dict


class QuietHander(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence all logs
        return


def _start_server_on_port(
    handler: Callable[..., http.server.SimpleHTTPRequestHandler], port: int
):
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at localhost:{port}")
        httpd.serve_forever()


def run_server(config: Dict):
    Handler = functools.partial(QuietHander, directory=config["output"])

    if config.get("port") is None:
        current_port = 8080
        while current_port <= 65535:
            try:
                _start_server_on_port(Handler, current_port)
            except OSError as e:
                # errno 48: Address already in use
                if e.errno == errno.EADDRINUSE:
                    current_port += 1
                    continue
                else:
                    raise e

    else:
        _start_server_on_port(Handler, config["port"])


def run(config: Dict):
    server_thread = threading.Thread(target=run_server, args=(config,), daemon=True)
    server_thread.start()
