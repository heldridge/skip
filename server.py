import http.server
import functools
import socketserver
import threading


class QuietHander(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence all logs
        return


def run_server(directory, port):
    Handler = functools.partial(QuietHander, directory=directory)
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"Serving at localhost:{port}")
        httpd.serve_forever()


def run(directory, port):
    server_thread = threading.Thread(
        target=run_server, args=(directory, port), daemon=True
    )
    server_thread.start()
