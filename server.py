"""Simple HTTP server for the Kanban board.

Serves the Vue frontend and provides JSON API endpoints.
No third-party dependencies required - uses Python's built-in http.server.
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from db import init_db
import models


class KanbanHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with API endpoints for the Kanban board."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/kanban":
            self._handle_kanban_api()
        elif path == "/api/orders":
            self._handle_orders_api(parsed)
        elif path == "/" or path == "/kanban":
            self._serve_file("kanban.html", "text/html")
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            # Try to serve static files
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/move":
            self._handle_move_api()
        else:
            self.send_error(404)

    def _handle_kanban_api(self):
        """Return all kanban data grouped by status."""
        data = models.get_kanban_data()
        # Convert Row objects to dicts for JSON serialization
        serializable = {}
        for status, orders in data.items():
            serializable[status] = [dict(order) for order in orders]
        self._send_json(serializable)

    def _handle_orders_api(self, parsed):
        """Return orders, optionally filtered by status."""
        params = parse_qs(parsed.query)
        status = params.get("status", [None])[0]

        if status:
            rows = models.get_orders_by_status(status)
            data = [dict(row) for row in rows]
        else:
            rows = models.get_all_orders()
            data = [dict(row) for row in rows]

        self._send_json(data)

    def _handle_move_api(self):
        """Move an order to a new status."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            order_id = payload.get("order_id")
            new_status = payload.get("new_status")

            if order_id is None or new_status is None:
                self._send_json({"error": "order_id and new_status are required"}, 400)
                return

            success = models.move_order_status(int(order_id), new_status)
            if success:
                self._send_json({"success": True})
            else:
                self._send_json({"error": "Invalid order or status"}, 400)
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json({"error": str(e)}, 400)

    def _serve_file(self, filename, content_type):
        """Serve a static file."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except FileNotFoundError:
            self.send_error(404, f"File {filename} not found")

    def _send_json(self, data, status=200):
        """Send a JSON response."""
        response = json.dumps(data, ensure_ascii=False, default=str)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging for cleaner output."""
        pass


def run_server(host="127.0.0.1", port=8080):
    """Start the Kanban board server."""
    init_db()
    server = HTTPServer((host, port), KanbanHandler)
    print(f"Kanban board server running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    run_server()
