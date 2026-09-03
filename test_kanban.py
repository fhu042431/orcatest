"""Unit tests for the kanban board module."""

import json
import sqlite3
from http.server import HTTPServer
from unittest.mock import MagicMock, patch

import pytest
from db import get_connection, init_db
import models
import kanban_server


# ─── Test Fixture ──────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use a temporary database for every test."""
    db_path = str(tmp_path / "test_kanban.db")

    def patched_get_connection(path=None):
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("models.get_connection", patched_get_connection)
    monkeypatch.setattr("db.get_connection", patched_get_connection)

    conn = patched_get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT, phone TEXT, address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, unit TEXT NOT NULL,
            price REAL NOT NULL, stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL, unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS kanban_boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS kanban_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES kanban_boards(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS kanban_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES kanban_columns(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# ─── Board Tests ───────────────────────────────────────────

class TestBoardCRUD:
    def test_add_board(self):
        bid = models.add_board("采购看板", "管理采购流程")
        assert bid is not None
        board = models.get_board(bid)
        assert board["name"] == "采购看板"
        assert board["description"] == "管理采购流程"

    def test_add_board_no_description(self):
        bid = models.add_board("看板2")
        board = models.get_board(bid)
        assert board["name"] == "看板2"
        assert board["description"] is None

    def test_get_board_not_found(self):
        assert models.get_board(999) is None

    def test_get_all_boards(self):
        models.add_board("看板A")
        models.add_board("看板B")
        boards = models.get_all_boards()
        assert len(boards) == 2
        assert boards[0]["name"] == "看板A"
        assert boards[1]["name"] == "看板B"

    def test_get_all_boards_empty(self):
        boards = models.get_all_boards()
        assert len(boards) == 0

    def test_update_board(self):
        bid = models.add_board("旧名称", "旧描述")
        models.update_board(bid, name="新名称", description="新描述")
        board = models.get_board(bid)
        assert board["name"] == "新名称"
        assert board["description"] == "新描述"

    def test_update_board_partial(self):
        bid = models.add_board("看板A", "描述A")
        models.update_board(bid, name="看板B")
        board = models.get_board(bid)
        assert board["name"] == "看板B"
        assert board["description"] == "描述A"

    def test_update_board_skip_none(self):
        bid = models.add_board("看板A", "描述A")
        models.update_board(bid, name=None, description=None)
        board = models.get_board(bid)
        assert board["name"] == "看板A"
        assert board["description"] == "描述A"

    def test_update_board_empty_fields_returns_false(self):
        bid = models.add_board("看板A")
        result = models.update_board(bid)
        assert result is False

    def test_delete_board(self):
        bid = models.add_board("看板A")
        models.delete_board(bid)
        assert models.get_board(bid) is None

    def test_delete_board_cascades_columns_and_cards(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "任务1")
        models.delete_board(bid)
        assert models.get_board(bid) is None
        assert models.get_column(cid) is None
        assert models.get_card(card_id) is None


# ─── Column Tests ──────────────────────────────────────────

class TestColumnCRUD:
    def test_add_column(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "进行中", position=1)
        assert cid is not None
        col = models.get_column(cid)
        assert col["name"] == "进行中"
        assert col["position"] == 1
        assert col["board_id"] == bid

    def test_add_column_default_position(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        col = models.get_column(cid)
        assert col["position"] == 0

    def test_get_column_not_found(self):
        assert models.get_column(999) is None

    def test_get_columns_by_board(self):
        bid = models.add_board("看板A")
        models.add_column(bid, "待办", position=0)
        models.add_column(bid, "进行中", position=1)
        models.add_column(bid, "已完成", position=2)
        cols = models.get_columns_by_board(bid)
        assert len(cols) == 3
        assert cols[0]["name"] == "待办"
        assert cols[1]["name"] == "进行中"
        assert cols[2]["name"] == "已完成"

    def test_get_columns_by_board_ordered_by_position(self):
        bid = models.add_board("看板A")
        models.add_column(bid, "完成", position=2)
        models.add_column(bid, "待办", position=0)
        models.add_column(bid, "进行中", position=1)
        cols = models.get_columns_by_board(bid)
        assert [c["name"] for c in cols] == ["待办", "进行中", "完成"]

    def test_get_columns_by_board_empty(self):
        bid = models.add_board("看板A")
        cols = models.get_columns_by_board(bid)
        assert len(cols) == 0

    def test_get_columns_by_nonexistent_board(self):
        cols = models.get_columns_by_board(999)
        assert len(cols) == 0

    def test_update_column(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "旧名称", position=0)
        models.update_column(cid, name="新名称", position=5)
        col = models.get_column(cid)
        assert col["name"] == "新名称"
        assert col["position"] == 5

    def test_update_column_partial(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办", position=0)
        models.update_column(cid, name="进行中")
        col = models.get_column(cid)
        assert col["name"] == "进行中"
        assert col["position"] == 0

    def test_update_column_skip_none(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办", position=0)
        models.update_column(cid, name=None, position=None)
        col = models.get_column(cid)
        assert col["name"] == "待办"
        assert col["position"] == 0

    def test_update_column_empty_returns_false(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        assert models.update_column(cid) is False

    def test_delete_column(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        models.delete_column(cid)
        assert models.get_column(cid) is None

    def test_delete_column_cascades_cards(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "任务1")
        models.delete_column(cid)
        assert models.get_column(cid) is None
        assert models.get_card(card_id) is None

    def test_columns_different_boards_independent(self):
        bid1 = models.add_board("看板A")
        bid2 = models.add_board("看板B")
        cid1 = models.add_column(bid1, "列1")
        cid2 = models.add_column(bid2, "列2")
        assert len(models.get_columns_by_board(bid1)) == 1
        assert len(models.get_columns_by_board(bid2)) == 1
        models.delete_column(cid1)
        assert len(models.get_columns_by_board(bid1)) == 0
        assert len(models.get_columns_by_board(bid2)) == 1


# ─── Card Tests ────────────────────────────────────────────

class TestCardCRUD:
    def _setup_board_and_column(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        return bid, cid

    def test_add_card(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1", "任务描述")
        assert card_id is not None
        card = models.get_card(card_id)
        assert card["title"] == "任务1"
        assert card["description"] == "任务描述"
        assert card["column_id"] == cid
        assert card["position"] == 0

    def test_add_card_no_description(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1")
        card = models.get_card(card_id)
        assert card["title"] == "任务1"
        assert card["description"] is None

    def test_add_card_with_position(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1", position=5)
        card = models.get_card(card_id)
        assert card["position"] == 5

    def test_get_card_not_found(self):
        assert models.get_card(999) is None

    def test_get_cards_by_column(self):
        _, cid = self._setup_board_and_column()
        models.add_card(cid, "任务1")
        models.add_card(cid, "任务2")
        models.add_card(cid, "任务3")
        cards = models.get_cards_by_column(cid)
        assert len(cards) == 3

    def test_get_cards_by_column_ordered_by_position(self):
        _, cid = self._setup_board_and_column()
        models.add_card(cid, "C", position=2)
        models.add_card(cid, "A", position=0)
        models.add_card(cid, "B", position=1)
        cards = models.get_cards_by_column(cid)
        assert [c["title"] for c in cards] == ["A", "B", "C"]

    def test_get_cards_by_column_empty(self):
        _, cid = self._setup_board_and_column()
        cards = models.get_cards_by_column(cid)
        assert len(cards) == 0

    def test_get_cards_by_nonexistent_column(self):
        cards = models.get_cards_by_column(999)
        assert len(cards) == 0

    def test_update_card(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "旧标题", "旧描述")
        models.update_card(card_id, title="新标题", description="新描述")
        card = models.get_card(card_id)
        assert card["title"] == "新标题"
        assert card["description"] == "新描述"

    def test_update_card_partial(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1", "描述1")
        models.update_card(card_id, title="任务2")
        card = models.get_card(card_id)
        assert card["title"] == "任务2"
        assert card["description"] == "描述1"

    def test_update_card_skip_none(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1", "描述1")
        models.update_card(card_id, title=None, description=None)
        card = models.get_card(card_id)
        assert card["title"] == "任务1"
        assert card["description"] == "描述1"

    def test_update_card_empty_returns_false(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1")
        assert models.update_card(card_id) is False

    def test_update_card_position(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1", position=0)
        models.update_card(card_id, position=10)
        card = models.get_card(card_id)
        assert card["position"] == 10

    def test_update_card_column_id(self):
        bid = self._setup_board_and_column()[0]
        cid1 = models.add_column(bid, "待办")
        cid2 = models.add_column(bid, "进行中")
        card_id = models.add_card(cid1, "任务1")
        models.update_card(card_id, column_id=cid2)
        card = models.get_card(card_id)
        assert card["column_id"] == cid2

    def test_delete_card(self):
        _, cid = self._setup_board_and_column()
        card_id = models.add_card(cid, "任务1")
        models.delete_card(card_id)
        assert models.get_card(card_id) is None

    def test_delete_card_does_not_affect_others(self):
        _, cid = self._setup_board_and_column()
        id1 = models.add_card(cid, "任务1")
        id2 = models.add_card(cid, "任务2")
        models.delete_card(id1)
        assert models.get_card(id1) is None
        assert models.get_card(id2) is not None


# ─── Move Card Tests ──────────────────────────────────────

class TestMoveCard:
    def _setup_board_with_columns(self):
        bid = models.add_board("看板A")
        cid1 = models.add_column(bid, "待办", position=0)
        cid2 = models.add_column(bid, "进行中", position=1)
        return bid, cid1, cid2

    def test_move_card_to_another_column(self):
        bid, cid1, cid2 = self._setup_board_with_columns()
        card_id = models.add_card(cid1, "任务1")
        models.move_card(card_id, cid2)
        card = models.get_card(card_id)
        assert card["column_id"] == cid2

    def test_move_card_with_explicit_position(self):
        bid, cid1, cid2 = self._setup_board_with_columns()
        card_id = models.add_card(cid1, "任务1")
        models.move_card(card_id, cid2, position=0)
        card = models.get_card(card_id)
        assert card["column_id"] == cid2
        assert card["position"] == 0

    def test_move_card_auto_position(self):
        bid, cid1, cid2 = self._setup_board_with_columns()
        models.add_card(cid2, "已有任务", position=0)
        card_id = models.add_card(cid1, "新任务")
        models.move_card(card_id, cid2)
        card = models.get_card(card_id)
        assert card["column_id"] == cid2
        assert card["position"] == 1

    def test_move_card_within_same_column(self):
        bid, cid1, cid2 = self._setup_board_with_columns()
        card_id = models.add_card(cid1, "任务1", position=0)
        models.move_card(card_id, cid1, position=5)
        card = models.get_card(card_id)
        assert card["column_id"] == cid1
        assert card["position"] == 5


# ─── Board With Details Tests ──────────────────────────────

class TestBoardWithDetails:
    def test_get_board_with_details(self):
        bid = models.add_board("采购看板", "管理采购流程")
        cid1 = models.add_column(bid, "待办", position=0)
        cid2 = models.add_column(bid, "进行中", position=1)
        models.add_card(cid1, "任务1", "描述1")
        models.add_card(cid1, "任务2")
        models.add_card(cid2, "任务3", "描述3")

        detail = models.get_board_with_details(bid)
        assert detail is not None
        assert detail["name"] == "采购看板"
        assert len(detail["columns"]) == 2
        assert detail["columns"][0]["name"] == "待办"
        assert len(detail["columns"][0]["cards"]) == 2
        assert detail["columns"][0]["cards"][0]["title"] == "任务1"
        assert detail["columns"][1]["name"] == "进行中"
        assert len(detail["columns"][1]["cards"]) == 1

    def test_get_board_with_details_empty_board(self):
        bid = models.add_board("空看板")
        detail = models.get_board_with_details(bid)
        assert detail is not None
        assert len(detail["columns"]) == 0

    def test_get_board_with_details_nonexistent(self):
        assert models.get_board_with_details(999) is None

    def test_get_board_with_details_column_order(self):
        bid = models.add_board("看板A")
        cid2 = models.add_column(bid, "完成", position=2)
        cid0 = models.add_column(bid, "待办", position=0)
        cid1 = models.add_column(bid, "进行中", position=1)
        detail = models.get_board_with_details(bid)
        names = [c["name"] for c in detail["columns"]]
        assert names == ["待办", "进行中", "完成"]


# ─── Cascade Delete Tests ──────────────────────────────────

class TestCascadeDeletes:
    def test_delete_board_removes_all_children(self):
        bid = models.add_board("看板A")
        cid1 = models.add_column(bid, "列1")
        cid2 = models.add_column(bid, "列2")
        card1 = models.add_card(cid1, "卡片1")
        card2 = models.add_card(cid2, "卡片2")
        models.delete_board(bid)
        assert models.get_board(bid) is None
        assert models.get_column(cid1) is None
        assert models.get_column(cid2) is None
        assert models.get_card(card1) is None
        assert models.get_card(card2) is None

    def test_delete_column_removes_its_cards(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "列1")
        card1 = models.add_card(cid, "卡片1")
        card2 = models.add_card(cid, "卡片2")
        models.delete_column(cid)
        assert models.get_column(cid) is None
        assert models.get_card(card1) is None
        assert models.get_card(card2) is None


# ─── Kanban Server API Tests ──────────────────────────────

class TestKanbanServerAPI:
    """Test the HTTP API handlers by directly calling handler methods."""

    def _make_handler(self):
        """Create a mock handler for testing."""
        handler = kanban_server.KanbanHandler.__new__(kanban_server.KanbanHandler)
        handler.requestline = "GET /api/boards"
        handler.request_version = "HTTP/1.1"
        handler.client_address = ("127.0.0.1", 8080)
        handler.wfile = MagicMock()
        handler.rfile = MagicMock()
        handler.headers = {}
        # Mock send_response and send_header
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        return handler

    def _get_response_body(self, handler):
        """Extract the JSON body from the handler's wfile."""
        call_args = handler.wfile.write.call_args_list
        if not call_args:
            return None
        body = b"".join(args[0][0] for args in call_args)
        return json.loads(body.decode("utf-8"))

    def test_get_boards_empty(self):
        handler = self._make_handler()
        handler._get_boards()
        body = self._get_response_body(handler)
        assert body == []

    def test_get_boards_with_data(self):
        models.add_board("看板A")
        models.add_board("看板B")
        handler = self._make_handler()
        handler._get_boards()
        body = self._get_response_body(handler)
        assert len(body) == 2
        assert body[0]["name"] == "看板A"

    def test_create_board_success(self):
        handler = self._make_handler()
        handler._create_board({"name": "新看板", "description": "测试"})
        body = self._get_response_body(handler)
        assert body["name"] == "新看板"
        assert body["description"] == "测试"
        handler.send_response.assert_called_with(201)

    def test_create_board_missing_name(self):
        handler = self._make_handler()
        handler._create_board({})
        handler.send_response.assert_called_with(400)

    def test_create_board_empty_name(self):
        handler = self._make_handler()
        handler._create_board({"name": ""})
        handler.send_response.assert_called_with(400)

    def test_get_board_detail_success(self):
        bid = models.add_board("看板A")
        handler = self._make_handler()
        handler._get_board_detail(str(bid))
        body = self._get_response_body(handler)
        assert body["name"] == "看板A"
        assert "columns" in body

    def test_get_board_detail_not_found(self):
        handler = self._make_handler()
        handler._get_board_detail("999")
        handler.send_response.assert_called_with(404)

    def test_update_board_success(self):
        bid = models.add_board("旧名称")
        handler = self._make_handler()
        handler._update_board(str(bid), {"name": "新名称"})
        body = self._get_response_body(handler)
        assert body["name"] == "新名称"

    def test_update_board_not_found(self):
        handler = self._make_handler()
        handler._update_board("999", {"name": "新名称"})
        handler.send_response.assert_called_with(404)

    def test_delete_board_success(self):
        bid = models.add_board("看板A")
        handler = self._make_handler()
        handler._delete_board(str(bid))
        body = self._get_response_body(handler)
        assert body["ok"] is True
        assert models.get_board(bid) is None

    def test_delete_board_not_found(self):
        handler = self._make_handler()
        handler._delete_board("999")
        handler.send_response.assert_called_with(404)

    def test_create_column_success(self):
        bid = models.add_board("看板A")
        handler = self._make_handler()
        handler._create_column(str(bid), {"name": "待办", "position": 0})
        body = self._get_response_body(handler)
        assert body["name"] == "待办"
        assert body["position"] == 0
        handler.send_response.assert_called_with(201)

    def test_create_column_missing_name(self):
        bid = models.add_board("看板A")
        handler = self._make_handler()
        handler._create_column(str(bid), {})
        handler.send_response.assert_called_with(400)

    def test_get_columns_success(self):
        bid = models.add_board("看板A")
        models.add_column(bid, "待办")
        handler = self._make_handler()
        handler._get_columns(str(bid))
        body = self._get_response_body(handler)
        assert len(body) == 1

    def test_update_column_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "旧名称")
        handler = self._make_handler()
        handler._update_column(str(cid), {"name": "新名称"})
        body = self._get_response_body(handler)
        assert body["name"] == "新名称"

    def test_update_column_not_found(self):
        handler = self._make_handler()
        handler._update_column("999", {"name": "新名称"})
        handler.send_response.assert_called_with(404)

    def test_delete_column_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        handler = self._make_handler()
        handler._delete_column(str(cid))
        body = self._get_response_body(handler)
        assert body["ok"] is True

    def test_delete_column_not_found(self):
        handler = self._make_handler()
        handler._delete_column("999")
        handler.send_response.assert_called_with(404)

    def test_create_card_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        handler = self._make_handler()
        handler._create_card(str(cid), {"title": "任务1", "description": "描述"})
        body = self._get_response_body(handler)
        assert body["title"] == "任务1"
        assert body["description"] == "描述"
        handler.send_response.assert_called_with(201)

    def test_create_card_missing_title(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        handler = self._make_handler()
        handler._create_card(str(cid), {})
        handler.send_response.assert_called_with(400)

    def test_get_cards_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        models.add_card(cid, "任务1")
        handler = self._make_handler()
        handler._get_cards(str(cid))
        body = self._get_response_body(handler)
        assert len(body) == 1

    def test_get_card_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "任务1")
        handler = self._make_handler()
        handler._get_card(str(card_id))
        body = self._get_response_body(handler)
        assert body["title"] == "任务1"

    def test_get_card_not_found(self):
        handler = self._make_handler()
        handler._get_card("999")
        handler.send_response.assert_called_with(404)

    def test_update_card_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "旧标题")
        handler = self._make_handler()
        handler._update_card(str(card_id), {"title": "新标题"})
        body = self._get_response_body(handler)
        assert body["title"] == "新标题"

    def test_update_card_not_found(self):
        handler = self._make_handler()
        handler._update_card("999", {"title": "新标题"})
        handler.send_response.assert_called_with(404)

    def test_move_card_success(self):
        bid = models.add_board("看板A")
        cid1 = models.add_column(bid, "待办")
        cid2 = models.add_column(bid, "进行中")
        card_id = models.add_card(cid1, "任务1")
        handler = self._make_handler()
        handler._move_card(str(card_id), {"column_id": int(cid2)})
        body = self._get_response_body(handler)
        assert body["column_id"] == cid2

    def test_move_card_missing_column_id(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "任务1")
        handler = self._make_handler()
        handler._move_card(str(card_id), {})
        handler.send_response.assert_called_with(400)

    def test_move_card_not_found(self):
        handler = self._make_handler()
        handler._move_card("999", {"column_id": 1})
        handler.send_response.assert_called_with(404)

    def test_delete_card_success(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        card_id = models.add_card(cid, "任务1")
        handler = self._make_handler()
        handler._delete_card(str(card_id))
        body = self._get_response_body(handler)
        assert body["ok"] is True

    def test_delete_card_not_found(self):
        handler = self._make_handler()
        handler._delete_card("999")
        handler.send_response.assert_called_with(404)


# ─── Edge Cases ────────────────────────────────────────────

class TestEdgeCases:
    def test_very_long_board_name(self):
        long_name = "A" * 1000
        bid = models.add_board(long_name)
        board = models.get_board(bid)
        assert board["name"] == long_name

    def test_very_long_card_title(self):
        bid = models.add_board("看板")
        cid = models.add_column(bid, "列")
        long_title = "T" * 5000
        card_id = models.add_card(cid, long_title)
        card = models.get_card(card_id)
        assert card["title"] == long_title

    def test_special_characters_in_names(self):
        bid = models.add_board("看板<script>alert('xss')</script>")
        board = models.get_board(bid)
        assert "script" in board["name"]

    def test_unicode_in_all_fields(self):
        bid = models.add_board("看板🚀", "描述🎨")
        cid = models.add_column(bid, "待办📋")
        card_id = models.add_card(cid, "任务✅", "详细描述📝")
        detail = models.get_board_with_details(bid)
        assert detail["name"] == "看板🚀"
        assert detail["columns"][0]["name"] == "待办📋"
        assert detail["columns"][0]["cards"][0]["title"] == "任务✅"

    def test_concurrent_operations_same_board(self):
        bid = models.add_board("看板A")
        col_ids = []
        for i in range(10):
            cid = models.add_column(bid, f"列{i}", position=i)
            col_ids.append(cid)
        assert len(models.get_columns_by_board(bid)) == 10

    def test_move_card_many_times(self):
        bid = models.add_board("看板A")
        cols = []
        for i in range(5):
            cid = models.add_column(bid, f"列{i}")
            cols.append(cid)
        card_id = models.add_card(cols[0], "任务")
        for cid in cols[1:]:
            models.move_card(card_id, cid)
        card = models.get_card(card_id)
        assert card["column_id"] == cols[-1]

    def test_board_with_many_cards(self):
        bid = models.add_board("看板A")
        cid = models.add_column(bid, "待办")
        for i in range(100):
            models.add_card(cid, f"任务{i}", position=i)
        cards = models.get_cards_by_column(cid)
        assert len(cards) == 100

    def test_column_position_ordering_stability(self):
        bid = models.add_board("看板A")
        models.add_column(bid, "C", position=2)
        models.add_column(bid, "A", position=0)
        models.add_column(bid, "B", position=1)
        # Add cards to each column
        cols = models.get_columns_by_board(bid)
        for col in cols:
            models.add_card(col["id"], f"卡片-{col['name']}")
        # Verify ordering
        detail = models.get_board_with_details(bid)
        assert [c["name"] for c in detail["columns"]] == ["A", "B", "C"]
        assert detail["columns"][0]["cards"][0]["title"] == "卡片-A"

    def test_empty_description_fields(self):
        bid = models.add_board("看板", "")
        cid = models.add_column(bid, "列")
        card_id = models.add_card(cid, "卡片", "")
        card = models.get_card(card_id)
        assert card["description"] == ""


# ─── Existing Tests Compatibility ─────────────────────────

class TestExistingTestsCompatibility:
    """Ensure existing procurement tests still pass alongside kanban tables."""

    def test_supplier_still_works(self):
        from db import get_connection
        sid = models.add_supplier("供应商A")
        s = models.get_supplier(sid)
        assert s["name"] == "供应商A"

    def test_product_still_works(self):
        pid = models.add_product("螺丝", "包", 5.0, 100)
        p = models.get_product(pid)
        assert p["name"] == "螺丝"

    def test_order_still_works(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0)
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        order = models.get_order(oid)
        assert order["total_amount"] == 50.0

    def test_user_still_works(self):
        uid = models.add_user("admin", "secret123")
        user = models.get_user_by_username("admin")
        assert user["username"] == "admin"
