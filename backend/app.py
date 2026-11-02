"""Servidor web backend del clúster.

Responde con el nombre del nodo para poder ver qué backend atendió cada
petición, y simula un tiempo de procesamiento variable en /api/work para
que la diferencia entre algoritmos de balanceo sea medible.
Solo usa la biblioteca estándar de Python.
"""
import json
import os
import random
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

NODE = os.environ.get("BACKEND_NAME") or socket.gethostname()
PORT = int(os.environ.get("PORT", "8080"))
WORK_MIN_MS = int(os.environ.get("WORK_MIN_MS", "20"))
WORK_MAX_MS = int(os.environ.get("WORK_MAX_MS", "200"))

# Un color distinto por nodo para reconocerlo de un vistazo en el navegador
COLORS = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c", "#0891b2", "#ca8a04"]
COLOR = COLORS[sum(map(ord, NODE)) % len(COLORS)]

PAGE = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>{node}</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 0; display: flex; align-items: center;
        justify-content: center; height: 100vh; background: {color}; color: #fff; }}
 .card {{ text-align: center; }}
 h1 {{ font-size: 3.5rem; margin: 0 0 .5rem 0; }}
 p {{ font-size: 1.2rem; margin: .3rem 0; }}
</style></head>
<body><div class="card">
 <h1>{node}</h1>
 <p>Esta respuesta la atendió el servidor <b>{node}</b></p>
 <p>Contenedor: {host}</p>
 <p>Recarga la página para ver cómo NGINX reparte las peticiones.</p>
</div></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # permite conexiones persistentes con NGINX
    server_version = "lb-backend"

    def _send(self, code, body, content_type):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Backend", NODE)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, "ok\n", "text/plain; charset=utf-8")
        elif path == "/api/work":
            work_ms = random.randint(WORK_MIN_MS, WORK_MAX_MS)
            time.sleep(work_ms / 1000)
            self._send(200, json.dumps({"backend": NODE, "work_ms": work_ms}),
                       "application/json")
        elif path == "/":
            self._send(200, PAGE.format(node=NODE, host=socket.gethostname(), color=COLOR),
                       "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}), "application/json")

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, fmt, *args):
        pass  # los logs de acceso los lleva NGINX


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 1024   # cola de conexiones pendientes para soportar picos


if __name__ == "__main__":
    print(f"[{NODE}] escuchando en el puerto {PORT}", flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
