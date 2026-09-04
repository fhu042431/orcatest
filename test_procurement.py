"""Unit tests for the procurement system."""

import pytest
import sqlite3
from db import get_connection, init_db, hash_password, verify_password
import models


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use an in-memory database for every test."""
    db_path = str(tmp_path / "test.db")

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


# ─── Supplier Tests ────────────────────────────────────────

class TestSupplierCRUD:
    def test_add_supplier(self):
        sid = models.add_supplier("供应商A", "张三", "13800138000", "北京")
        assert sid is not None
        s = models.get_supplier(sid)
        assert s["name"] == "供应商A"
        assert s["contact"] == "张三"
        assert s["phone"] == "13800138000"
        assert s["address"] == "北京"

    def test_get_all_suppliers(self):
        models.add_supplier("供应商A")
        models.add_supplier("供应商B")
        rows = models.get_all_suppliers()
        assert len(rows) == 2

    def test_get_supplier_not_found(self):
        assert models.get_supplier(999) is None

    def test_update_supplier(self):
        sid = models.add_supplier("供应商A")
        models.update_supplier(sid, name="供应商X", phone="111")
        s = models.get_supplier(sid)
        assert s["name"] == "供应商X"
        assert s["phone"] == "111"

    def test_update_supplier_skip_empty(self):
        sid = models.add_supplier("供应商A")
        models.update_supplier(sid, name=None)
        s = models.get_supplier(sid)
        assert s["name"] == "供应商A"

    def test_delete_supplier(self):
        sid = models.add_supplier("供应商A")
        models.delete_supplier(sid)
        assert models.get_supplier(sid) is None


# ─── Product Tests ─────────────────────────────────────────

class TestProductCRUD:
    def test_add_product(self):
        pid = models.add_product("螺丝", "包", 5.0, 100)
        assert pid is not None
        p = models.get_product(pid)
        assert p["name"] == "螺丝"
        assert p["unit"] == "包"
        assert p["price"] == 5.0
        assert p["stock"] == 100

    def test_get_all_products(self):
        models.add_product("螺丝", "包", 5.0)
        models.add_product("螺母", "个", 2.0)
        rows = models.get_all_products()
        assert len(rows) == 2

    def test_get_product_not_found(self):
        assert models.get_product(999) is None

    def test_update_product(self):
        pid = models.add_product("螺丝", "包", 5.0)
        models.update_product(pid, name="大螺丝", price=8.0)
        p = models.get_product(pid)
        assert p["name"] == "大螺丝"
        assert p["price"] == 8.0

    def test_delete_product(self):
        pid = models.add_product("螺丝", "包", 5.0)
        models.delete_product(pid)
        assert models.get_product(pid) is None


# ─── Order Tests ───────────────────────────────────────────

class TestPurchaseOrders:
    def _setup_supplier_and_product(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        return sid, pid

    def test_create_order(self):
        sid, _ = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        order = models.get_order(oid)
        assert order is not None
        assert order["supplier_id"] == sid
        assert order["total_amount"] == 0
        assert order["status"] == "pending"

    def test_add_order_item(self):
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        items = models.get_order_items(oid)
        assert len(items) == 1
        assert items[0]["subtotal"] == 50.0
        order = models.get_order(oid)
        assert order["total_amount"] == 50.0

    def test_multiple_items_total(self):
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        models.add_order_item(oid, pid, 20, 5.0)
        order = models.get_order(oid)
        assert order["total_amount"] == 150.0

    def test_get_all_orders(self):
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 5, 5.0)
        orders = models.get_all_orders()
        assert len(orders) == 1
        assert orders[0]["supplier_name"] == "供应商A"
        assert orders[0]["total_amount"] == 25.0

    def test_update_order_status(self):
        sid, _ = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.update_order_status(oid, "confirmed")
        order = models.get_order(oid)
        assert order["status"] == "confirmed"

    def test_delete_order_cascades(self):
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 5, 5.0)
        models.delete_order(oid)
        assert models.get_order(oid) is None
        assert models.get_order_items(oid) == []

    def test_get_order_not_found(self):
        assert models.get_order(999) is None


# ─── Constraint Tests ──────────────────────────────────────

class TestConstraints:
    def test_order_invalid_supplier(self):
        with pytest.raises(sqlite3.IntegrityError):
            models.create_order(999)

    def test_order_item_invalid_product(self):
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        with pytest.raises(sqlite3.IntegrityError):
            models.add_order_item(oid, 999, 10, 5.0)

    def test_order_item_invalid_order(self):
        pid = models.add_product("螺丝", "包", 5.0)
        with pytest.raises(sqlite3.IntegrityError):
            models.add_order_item(999, pid, 10, 5.0)


# ─── Password Hash Tests ──────────────────────────────────

class TestPasswordHash:
    def test_hash_and_verify(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)

    def test_wrong_password(self):
        hashed = hash_password("mypassword")
        assert not verify_password("wrongpassword", hashed)

    def test_different_hashes_same_password(self):
        h1 = hash_password("test")
        h2 = hash_password("test")
        # Different salts produce different hashes
        assert h1 != h2
        # But both verify correctly
        assert verify_password("test", h1)
        assert verify_password("test", h2)


# ─── User Auth Tests ───────────────────────────────────────

class TestUserAuth:
    def test_add_user(self):
        uid = models.add_user("admin", "secret123", "管理员")
        assert uid is not None
        user = models.get_user_by_username("admin")
        assert user["username"] == "admin"
        assert user["display_name"] == "管理员"

    def test_add_user_duplicate(self):
        models.add_user("admin", "secret123")
        uid2 = models.add_user("admin", "another")
        assert uid2 is None

    def test_verify_user_success(self):
        models.add_user("admin", "secret123")
        user = models.verify_user("admin", "secret123")
        assert user is not None
        assert user["username"] == "admin"

    def test_verify_user_wrong_password(self):
        models.add_user("admin", "secret123")
        user = models.verify_user("admin", "wrong")
        assert user is None

    def test_verify_user_not_found(self):
        user = models.verify_user("nobody", "pass")
        assert user is None

    def test_get_all_users(self):
        models.add_user("user1", "pass1")
        models.add_user("user2", "pass2")
        users = models.get_all_users()
        assert len(users) == 2

    def test_delete_user(self):
        uid = models.add_user("admin", "secret123")
        models.delete_user(uid)
        assert models.get_user_by_username("admin") is None


# ─── Kanban Board Tests ────────────────────────────────────

class TestKanbanBoard:
    def _setup_supplier_and_product(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        return sid, pid

    def _create_order_with_items(self, status="pending"):
        """Helper to create an order with items and set its status."""
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        models.update_order_status(oid, status)
        return oid

    # ── get_orders_by_status ────────────────────────────────

    def test_get_orders_by_status_empty(self):
        """No orders returns empty list."""
        rows = models.get_orders_by_status("pending")
        assert rows == []

    def test_get_orders_by_status_returns_matching(self):
        """Only orders with the given status are returned."""
        oid1 = self._create_order_with_items("pending")
        oid2 = self._create_order_with_items("confirmed")
        oid3 = self._create_order_with_items("pending")

        rows = models.get_orders_by_status("pending")
        assert len(rows) == 2
        ids = [r["id"] for r in rows]
        assert oid1 in ids
        assert oid3 in ids
        assert oid2 not in ids

    def test_get_orders_by_status_includes_supplier_name(self):
        """Returned rows include supplier_name."""
        self._create_order_with_items("pending")
        rows = models.get_orders_by_status("pending")
        assert rows[0]["supplier_name"] == "供应商A"

    def test_get_orders_by_status_includes_item_count(self):
        """Returned rows include item_count."""
        self._create_order_with_items("pending")
        rows = models.get_orders_by_status("pending")
        assert rows[0]["item_count"] == 1

    def test_get_orders_by_status_multiple_items(self):
        """item_count reflects the number of order items."""
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 5, 5.0)
        models.add_order_item(oid, pid, 10, 5.0)
        models.add_order_item(oid, pid, 15, 5.0)

        rows = models.get_orders_by_status("pending")
        assert rows[0]["item_count"] == 3

    def test_get_orders_by_status_nonexistent_status(self):
        """Querying a status with no orders returns empty list."""
        self._create_order_with_items("pending")
        rows = models.get_orders_by_status("nonexistent")
        assert rows == []

    def test_get_orders_by_status_all_statuses(self):
        """Each valid status returns the correct orders."""
        oid_p = self._create_order_with_items("pending")
        oid_c = self._create_order_with_items("confirmed")
        oid_s = self._create_order_with_items("shipped")
        oid_r = self._create_order_with_items("received")
        oid_x = self._create_order_with_items("cancelled")

        assert len(models.get_orders_by_status("pending")) == 1
        assert models.get_orders_by_status("pending")[0]["id"] == oid_p
        assert len(models.get_orders_by_status("confirmed")) == 1
        assert models.get_orders_by_status("confirmed")[0]["id"] == oid_c
        assert len(models.get_orders_by_status("shipped")) == 1
        assert models.get_orders_by_status("shipped")[0]["id"] == oid_s
        assert len(models.get_orders_by_status("received")) == 1
        assert models.get_orders_by_status("received")[0]["id"] == oid_r
        assert len(models.get_orders_by_status("cancelled")) == 1
        assert models.get_orders_by_status("cancelled")[0]["id"] == oid_x

    # ── get_kanban_data ─────────────────────────────────────

    def test_get_kanban_data_empty(self):
        """Empty database returns all status keys with empty lists."""
        data = models.get_kanban_data()
        assert isinstance(data, dict)
        for status in models.KANBAN_STATUSES:
            assert status in data
            assert data[status] == []

    def test_get_kanban_data_groups_by_status(self):
        """Orders are grouped into the correct status columns."""
        oid_p = self._create_order_with_items("pending")
        oid_c = self._create_order_with_items("confirmed")
        oid_s = self._create_order_with_items("shipped")

        data = models.get_kanban_data()
        assert len(data["pending"]) == 1
        assert data["pending"][0]["id"] == oid_p
        assert len(data["confirmed"]) == 1
        assert data["confirmed"][0]["id"] == oid_c
        assert len(data["shipped"]) == 1
        assert data["shipped"][0]["id"] == oid_s
        assert len(data["received"]) == 0
        assert len(data["cancelled"]) == 0

    def test_get_kanban_data_includes_fields(self):
        """Each order dict contains all expected fields."""
        self._create_order_with_items("pending")
        data = models.get_kanban_data()
        order = data["pending"][0]
        assert "id" in order
        assert "supplier_id" in order
        assert "supplier_name" in order
        assert "total_amount" in order
        assert "status" in order
        assert "created_at" in order
        assert "item_count" in order

    def test_get_kanban_data_total_amount(self):
        """total_amount reflects order total including items."""
        self._create_order_with_items("pending")
        data = models.get_kanban_data()
        assert data["pending"][0]["total_amount"] == 50.0

    def test_get_kanban_data_ignores_unknown_status(self):
        """Orders with status not in KANBAN_STATUSES are excluded."""
        sid, pid = self._setup_supplier_and_product()
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 5, 5.0)
        # Manually set an invalid status
        models.update_order_status(oid, "invalid_status")

        data = models.get_kanban_data()
        for status in models.KANBAN_STATUSES:
            assert len(data[status]) == 0

    def test_get_kanban_data_returns_lists(self):
        """Each status value is a list (not a Row or other type)."""
        self._create_order_with_items("pending")
        data = models.get_kanban_data()
        for status in models.KANBAN_STATUSES:
            assert isinstance(data[status], list)

    def test_get_kanban_data_order_dicts_are_serializable(self):
        """Order dicts can be serialized to JSON (no Row objects)."""
        import json
        self._create_order_with_items("pending")
        data = models.get_kanban_data()
        # Should not raise
        json.dumps(data, default=str)

    # ── move_order_status ───────────────────────────────────

    def test_move_order_status_success(self):
        """Valid status transition updates the order."""
        oid = self._create_order_with_items("pending")
        result = models.move_order_status(oid, "confirmed")
        assert result is True
        order = models.get_order(oid)
        assert order["status"] == "confirmed"

    def test_move_order_status_invalid_order(self):
        """Moving a non-existent order returns False."""
        result = models.move_order_status(999, "confirmed")
        assert result is False

    def test_move_order_status_invalid_status(self):
        """Moving to an invalid status returns False without changing the order."""
        oid = self._create_order_with_items("pending")
        result = models.move_order_status(oid, "invalid_status")
        assert result is False
        order = models.get_order(oid)
        assert order["status"] == "pending"

    def test_move_order_status_all_valid_transitions(self):
        """Test all valid status transitions."""
        # pending -> confirmed
        oid = self._create_order_with_items("pending")
        assert models.move_order_status(oid, "confirmed") is True
        assert models.get_order(oid)["status"] == "confirmed"

        # confirmed -> shipped
        assert models.move_order_status(oid, "shipped") is True
        assert models.get_order(oid)["status"] == "shipped"

        # shipped -> received
        assert models.move_order_status(oid, "received") is True
        assert models.get_order(oid)["status"] == "received"

    def test_move_order_status_cancel_from_pending(self):
        """Can cancel from pending."""
        oid = self._create_order_with_items("pending")
        assert models.move_order_status(oid, "cancelled") is True
        assert models.get_order(oid)["status"] == "cancelled"

    def test_move_order_status_cancel_from_confirmed(self):
        """Can cancel from confirmed."""
        oid = self._create_order_with_items("confirmed")
        assert models.move_order_status(oid, "cancelled") is True
        assert models.get_order(oid)["status"] == "cancelled"

    def test_move_order_status_kanban_data_reflects_move(self):
        """After moving an order, get_kanban_data reflects the change."""
        oid = self._create_order_with_items("pending")
        data = models.get_kanban_data()
        assert len(data["pending"]) == 1
        assert len(data["confirmed"]) == 0

        models.move_order_status(oid, "confirmed")

        data = models.get_kanban_data()
        assert len(data["pending"]) == 0
        assert len(data["confirmed"]) == 1
        assert data["confirmed"][0]["id"] == oid

    def test_kanban_statuses_constant(self):
        """KANBAN_STATUSES contains all expected statuses."""
        expected = ["pending", "confirmed", "shipped", "received", "cancelled"]
        assert models.KANBAN_STATUSES == expected
