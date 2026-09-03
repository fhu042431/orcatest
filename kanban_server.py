"""Simple HTTP server for the kanban board (REST API + static HTML)."""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from db import init_db
import models


class KanbanHandler(SimpleHTTPRequestHandler):
    """Handle REST API requests for the kanban board."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "" or path == "/kanban" or path == "/kanban.html":
            self._serve_html()
        elif path == "/api/boards":
            self._get_boards()
        elif path.startswith("/api/boards/") and path.count("/") == 3:
            board_id = path.split("/")[3]
            self._get_board_detail(board_id)
        elif path.startswith("/api/boards/") and path.count("/") == 4:
            parts = path.split("/")
            board_id = parts[3]
            resource = parts[4]
            if resource == "columns":
                self._get_columns(board_id)
            else:
                self._json_response({"error": "Not found"}, 404)
        elif path.startswith("/api/columns/") and path.endswith("/cards"):
            column_id = path.split("/")[2]
            self._get_cards(column_id)
        elif path.startswith("/api/cards/"):
            card_id = path.split("/")[2]
            self._get_card(card_id)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        if path == "/api/boards":
            self._create_board(body)
        elif path == "/api/boards/" or path == "/api/boards":
            self._create_board(body)
        elif path.startswith("/api/boards/") and path.endswith("/columns"):
            board_id = path.split("/")[3]
            self._create_column(board_id, body)
        elif path.startswith("/api/columns/") and path.endswith("/cards"):
            column_id = path.split("/")[2]
            self._create_card(column_id, body)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/boards/") and path.count("/") == 3:
            board_id = path.split("/")[3]
            body = self._read_body()
            self._update_board(board_id, body)
        elif path.startswith("/api/columns/") and path.count("/") == 3:
            column_id = path.split("/")[2]
            body = self._read_body()
            self._update_column(column_id, body)
        elif path.startswith("/api/cards/") and path.count("/") == 3:
            card_id = path.split("/")[2]
            body = self._read_body()
            self._update_card(card_id, body)
        elif path.startswith("/api/cards/") and path.endswith("/move"):
            card_id = path.split("/")[2]
            body = self._read_body()
            self._move_card(card_id, body)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/boards/") and path.count("/") == 3:
            board_id = path.split("/")[3]
            self._delete_board(board_id)
        elif path.startswith("/api/columns/") and path.count("/") == 3:
            column_id = path.split("/")[2]
            self._delete_column(column_id)
        elif path.startswith("/api/cards/") and path.count("/") == 3:
            card_id = path.split("/")[2]
            self._delete_card(card_id)
        else:
            self._json_response({"error": "Not found"}, 404)

    # ─── Helpers ────────────────────────────────────────────

    def _serve_html(self):
        html_path = os.path.join(os.path.dirname(__file__), "kanban.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _row_to_dict(self, row):
        """Convert a sqlite3.Row to a plain dict."""
        if row is None:
            return None
        return dict(row)

    # ─── Board CRUD ─────────────────────────────────────────

    def _get_boards(self):
        boards = models.get_all_boards()
        self._json_response([self._row_to_dict(b) for b in boards])

    def _get_board_detail(self, board_id):
        board = models.get_board_with_details(int(board_id))
        if not board:
            self._json_response({"error": "Board not found"}, 404)
            return
        self._json_response(board)

    def _create_board(self, body):
        name = body.get("name")
        if not name:
            self._json_response({"error": "name is required"}, 400)
            return
        board_id = models.add_board(name, body.get("description"))
        board = models.get_board(board_id)
        self._json_response(self._row_to_dict(board), 201)

    def _update_board(self, board_id, body):
        board = models.get_board(int(board_id))
        if not board:
            self._json_response({"error": "Board not found"}, 404)
            return
        models.update_board(int(board_id), **body)
        board = models.get_board(int(board_id))
        self._json_response(self._row_to_dict(board))

    def _delete_board(self, board_id):
        board = models.get_board(int(board_id))
        if not board:
            self._json_response({"error": "Board not found"}, 404)
            return
        models.delete_board(int(board_id))
        self._json_response({"ok": True})

    # ─── Column CRUD ────────────────────────────────────────

    def _get_columns(self, board_id):
        columns = models.get_columns_by_board(int(board_id))
        self._json_response([self._row_to_dict(c) for c in columns])

    def _create_column(self, board_id, body):
        name = body.get("name")
        if not name:
            self._json_response({"error": "name is required"}, 400)
            return
        position = body.get("position", 0)
        col_id = models.add_column(int(board_id), name, position)
        col = models.get_column(col_id)
        self._json_response(self._row_to_dict(col), 201)

    def _update_column(self, column_id, body):
        col = models.get_column(int(column_id))
        if not col:
            self._json_response({"error": "Column not found"}, 404)
            return
        models.update_column(int(column_id), **body)
        col = models.get_column(int(column_id))
        self._json_response(self._row_to_dict(col))

    def _delete_column(self, column_id):
        col = models.get_column(int(column_id))
        if not col:
            self._json_response({"error": "Column not found"}, 404)
            return
        models.delete_column(int(column_id))
        self._json_response({"ok": True})

    # ─── Card CRUD ──────────────────────────────────────────

    def _get_cards(self, column_id):
        cards = models.get_cards_by_column(int(column_id))
        self._json_response([self._row_to_dict(c) for c in cards])

    def _get_card(self, card_id):
        card = models.get_card(int(card_id))
        if not card:
            self._json_response({"error": "Card not found"}, 404)
            return
        self._json_response(self._row_to_dict(card))

    def _create_card(self, column_id, body):
        title = body.get("title")
        if not title:
            self._json_response({"error": "title is required"}, 400)
            return
        position = body.get("position", 0)
        card_id = models.add_card(
            int(column_id), title, body.get("description"), position
        )
        card = models.get_card(card_id)
        self._json_response(self._row_to_dict(card), 201)

    def _update_card(self, card_id, body):
        card = models.get_card(int(card_id))
        if not card:
            self._json_response({"error": "Card not found"}, 404)
            return
        models.update_card(int(card_id), **body)
        card = models.get_card(int(card_id))
        self._json_response(self._row_to_dict(card))

    def _move_card(self, card_id, body):
        card = models.get_card(int(card_id))
        if not card:
            self._json_response({"error": "Card not found"}, 404)
            return
        target_column_id = body.get("column_id")
        position = body.get("position")
        if target_column_id is None:
            self._json_response({"error": "column_id is required"}, 400)
            return
        models.move_card(int(card_id), int(target_column_id), position)
        card = models.get_card(int(card_id))
        self._json_response(self._row_to_dict(card))

    def _delete_card(self, card_id):
        card = models.get_card(int(card_id))
        if not card:
            self._json_response({"error": "Card not found"}, 404)
            return
        models.delete_card(int(card_id))
        self._json_response({"ok": True})

    def log_message(self, format, *args):
        """Suppress default access logging."""
        pass


def start_server(host="0.0.0.0", port=8080):
    """Start the kanban HTTP server."""
    init_db()
    server = HTTPServer((host, port), KanbanHandler)
    print(f"Kanban server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    start_server()
