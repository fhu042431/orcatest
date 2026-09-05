"""Unit tests for the kanban board feature."""

import pytest
import sqlite3
from db import get_connection, init_db
import models
from server import create_app


# ─── Shared fixture: in-memory DB + monkeypatch ─────────────

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use a per-test SQLite file so each test starts clean."""
    db_path = str(tmp_path / "test_kanban.db")

    def patched_get_connection(path=None):
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("models.get_connection", patched_get_connection)
    monkeypatch.setattr("db.get_connection", patched_get_connection)

    # Create schema
    conn = patched_get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
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
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
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
    """)
    conn.commit()
    conn.close()

    return db_path


def _seed_order(db_path, supplier_name="供应商A", status="pending", total=100.0):
    """Helper: insert a supplier + order with given status and return order id."""
    conn = get_connection(db_path)
    conn.execute("INSERT INTO suppliers (name) VALUES (?)", (supplier_name,))
    supplier_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO purchase_orders (supplier_id, total_amount, status) VALUES (?, ?, ?)",
        (supplier_id, total, status),
    )
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return order_id


# ─── Model tests: get_orders_by_status ─────────────────────

class TestGetOrdersByStatus:
    def test_returns_orders_for_status(self, setup_db):
        oid = _seed_order(setup_db)
        rows = models.get_orders_by_status("pending")
        assert len(rows) == 1
        assert rows[0]["id"] == oid

    def test_returns_empty_for_unknown_status(self, setup_db):
        _seed_order(setup_db, status="pending")
        rows = models.get_orders_by_status("shipped")
        assert rows == []

    def test_filters_by_status(self, setup_db):
        _seed_order(setup_db, status="pending")
        _seed_order(setup_db, status="confirmed")
        _seed_order(setup_db, status="pending")
        pending = models.get_orders_by_status("pending")
        confirmed = models.get_orders_by_status("confirmed")
        assert len(pending) == 2
        assert len(confirmed) == 1

    def test_includes_supplier_name(self, setup_db):
        _seed_order(setup_db, supplier_name="供应商X", status="confirmed")
        rows = models.get_orders_by_status("confirmed")
        assert rows[0]["supplier_name"] == "供应商X"

    def test_orders_ordered_by_id(self, setup_db):
        _seed_order(setup_db, status="pending")
        _seed_order(setup_db, status="pending")
        rows = models.get_orders_by_status("pending")
        assert rows[0]["id"] < rows[1]["id"]


# ─── Model tests: get_kanban_data ───────────────────────────

class TestGetKanbanData:
    def test_returns_all_statuses(self, setup_db):
        data = models.get_kanban_data()
        for s in models.VALID_STATUSES:
            assert s in data

    def test_groups_orders_correctly(self, setup_db):
        _seed_order(setup_db, status="pending")
        _seed_order(setup_db, status="pending")
        _seed_order(setup_db, status="shipped")
        data = models.get_kanban_data()
        assert len(data["pending"]) == 2
        assert len(data["shipped"]) == 1
        assert len(data["confirmed"]) == 0

    def test_empty_db_returns_empty_lists(self, setup_db):
        data = models.get_kanban_data()
        for status in models.VALID_STATUSES:
            assert data[status] == []


# ─── Model tests: move_order ────────────────────────────────

class TestMoveOrder:
    def test_move_pending_to_confirmed(self, setup_db):
        oid = _seed_order(setup_db, status="pending")
        assert models.move_order(oid, "confirmed") is True
        order = models.get_order(oid)
        assert order["status"] == "confirmed"

    def test_move_invalid_status_returns_false(self, setup_db):
        oid = _seed_order(setup_db)
        assert models.move_order(oid, "invalid_status") is False

    def test_move_nonexistent_order_returns_false(self, setup_db):
        assert models.move_order(9999, "confirmed") is False

    def test_move_to_cancelled(self, setup_db):
        oid = _seed_order(setup_db, status="shipped")
        assert models.move_order(oid, "cancelled") is True
        order = models.get_order(oid)
        assert order["status"] == "cancelled"


# ─── Model tests: VALID_STATUSES ────────────────────────────

class TestValidStatuses:
    def test_has_five_statuses(self):
        assert len(models.VALID_STATUSES) == 5

    def test_contains_expected_statuses(self):
        expected = {"pending", "confirmed", "shipped", "received", "cancelled"}
        assert set(models.VALID_STATUSES) == expected


# ─── Flask API tests ────────────────────────────────────────

@pytest.fixture
def client(setup_db):
    """Create a Flask test client backed by the test DB."""
    app = create_app(test_db_path=setup_db)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestKanbanAPI:
    def test_get_kanban_returns_200(self, client):
        resp = client.get("/api/kanban")
        assert resp.status_code == 200

    def test_get_kanban_returns_all_statuses(self, client):
        data = client.get("/api/kanban").get_json()
        for s in models.VALID_STATUSES:
            assert s in data

    def test_get_kanban_with_data(self, client):
        _seed_order(client.application.config.get("TEST_DB", ""), status="pending")
        data = client.get("/api/kanban").get_json()
        assert len(data["pending"]) == 1


class TestUpdateStatusAPI:
    def test_update_status_success(self, client):
        db_path = client.application.config.get("TEST_DB", "")
        oid = _seed_order(db_path, status="pending")
        resp = client.put(
            f"/api/orders/{oid}/status",
            json={"status": "confirmed"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True
        assert body["status"] == "confirmed"

    def test_update_status_invalid_status(self, client):
        db_path = client.application.config.get("TEST_DB", "")
        oid = _seed_order(db_path)
        resp = client.put(
            f"/api/orders/{oid}/status",
            json={"status": "bogus"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "invalid" in resp.get_json()["error"]

    def test_update_status_missing_body(self, client):
        resp = client.put(
            "/api/orders/1/status",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_status_nonexistent_order(self, client):
        resp = client.put(
            "/api/orders/9999/status",
            json={"status": "confirmed"},
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_update_status_no_json(self, client):
        db_path = client.application.config.get("TEST_DB", "")
        oid = _seed_order(db_path)
        resp = client.put(f"/api/orders/{oid}/status")
        assert resp.status_code == 400


class TestIndexPage:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contains_vue(self, client):
        resp = client.get("/")
        assert b"vue" in resp.data.lower()
