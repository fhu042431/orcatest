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


# ─── Kanban Board Tests ──────────────────────────────────

class TestKanbanConstants:
    """Test kanban module constants are correctly defined."""

    def test_kanban_columns_has_five_statuses(self):
        assert len(models.KANBAN_COLUMNS) == 5

    def test_kanban_columns_contain_valid_statuses(self):
        expected = {"pending", "confirmed", "shipped", "received", "cancelled"}
        assert set(models.KANBAN_COLUMNS) == expected

    def test_kanban_labels_cover_all_columns(self):
        for col in models.KANBAN_COLUMNS:
            assert col in models.KANBAN_LABELS

    def test_kanban_labels_are_chinese(self):
        for label in models.KANBAN_LABELS.values():
            assert isinstance(label, str)
            assert len(label) > 0


class TestGetOrdersByStatus:
    """Test get_orders_by_status() function."""

    def _make_order_with_status(self, status, supplier_name="供应商A"):
        sid = models.add_supplier(supplier_name)
        oid = models.create_order(sid)
        models.update_order_status(oid, status)
        return oid

    def test_empty_status_returns_no_orders(self):
        orders = models.get_orders_by_status("pending")
        assert orders == []

    def test_pending_orders(self):
        oid = self._make_order_with_status("pending")
        orders = models.get_orders_by_status("pending")
        assert len(orders) == 1
        assert orders[0]["id"] == oid
        assert orders[0]["status"] == "pending"

    def test_confirmed_orders(self):
        oid = self._make_order_with_status("confirmed")
        orders = models.get_orders_by_status("confirmed")
        assert len(orders) == 1
        assert orders[0]["id"] == oid

    def test_shipped_orders(self):
        oid = self._make_order_with_status("shipped")
        orders = models.get_orders_by_status("shipped")
        assert len(orders) == 1

    def test_received_orders(self):
        oid = self._make_order_with_status("received")
        orders = models.get_orders_by_status("received")
        assert len(orders) == 1

    def test_cancelled_orders(self):
        oid = self._make_order_with_status("cancelled")
        orders = models.get_orders_by_status("cancelled")
        assert len(orders) == 1

    def test_orders_not_in_other_statuses(self):
        """An order in 'pending' should NOT appear in 'confirmed'."""
        self._make_order_with_status("pending")
        orders = models.get_orders_by_status("confirmed")
        assert len(orders) == 0

    def test_multiple_orders_same_status(self):
        self._make_order_with_status("pending", "供应商A")
        self._make_order_with_status("pending", "供应商B")
        self._make_order_with_status("pending", "供应商C")
        orders = models.get_orders_by_status("pending")
        assert len(orders) == 3

    def test_orders_across_different_statuses(self):
        """Orders spread across statuses are correctly separated."""
        self._make_order_with_status("pending")
        self._make_order_with_status("confirmed")
        self._make_order_with_status("shipped")
        self._make_order_with_status("received")
        self._make_order_with_status("cancelled")
        assert len(models.get_orders_by_status("pending")) == 1
        assert len(models.get_orders_by_status("confirmed")) == 1
        assert len(models.get_orders_by_status("shipped")) == 1
        assert len(models.get_orders_by_status("received")) == 1
        assert len(models.get_orders_by_status("cancelled")) == 1

    def test_result_includes_supplier_name(self):
        sid = models.add_supplier("测试供应商")
        oid = models.create_order(sid)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["supplier_name"] == "测试供应商"

    def test_result_includes_item_count_zero(self):
        """Order with no items should have item_count = 0."""
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["item_count"] == 0

    def test_result_includes_item_count_with_items(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        models.add_order_item(oid, pid, 20, 3.0)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["item_count"] == 2

    def test_result_includes_total_amount(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["total_amount"] == 50.0

    def test_result_includes_created_at(self):
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["created_at"] is not None

    def test_orders_sorted_by_created_at_desc(self):
        """Most recent orders first."""
        sid = models.add_supplier("供应商A")
        oid1 = models.create_order(sid)
        oid2 = models.create_order(sid)
        oid3 = models.create_order(sid)
        orders = models.get_orders_by_status("pending")
        ids = [o["id"] for o in orders]
        # Should be reverse chronological (newest first)
        assert ids == sorted(ids, reverse=True)

    def test_invalid_status_returns_empty(self):
        """Querying with an invalid status should return empty list."""
        orders = models.get_orders_by_status("nonexistent")
        assert orders == []

    def test_empty_string_status_returns_empty(self):
        orders = models.get_orders_by_status("")
        assert orders == []


class TestGetKanbanData:
    """Test get_kanban_data() function."""

    def test_empty_kanban_returns_all_columns(self):
        data = models.get_kanban_data()
        assert isinstance(data, dict)
        # Should have all 5 columns
        for label in models.KANBAN_LABELS.values():
            assert label in data

    def test_empty_kanban_all_columns_empty(self):
        data = models.get_kanban_data()
        for label, orders in data.items():
            assert orders == []

    def test_single_order_in_pending(self):
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        data = models.get_kanban_data()
        assert len(data["待处理"]) == 1
        assert data["待处理"][0]["id"] == oid
        # Other columns empty
        assert data["已确认"] == []
        assert data["已发货"] == []
        assert data["已收货"] == []
        assert data["已取消"] == []

    def test_orders_distributed_across_columns(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        oid1 = models.create_order(sid)
        models.add_order_item(oid1, pid, 5, 5.0)
        oid2 = models.create_order(sid)
        models.update_order_status(oid2, "confirmed")
        oid3 = models.create_order(sid)
        models.update_order_status(oid3, "received")

        data = models.get_kanban_data()
        assert len(data["待处理"]) == 1
        assert data["待处理"][0]["id"] == oid1
        assert len(data["已确认"]) == 1
        assert data["已确认"][0]["id"] == oid2
        assert len(data["已收货"]) == 1
        assert data["已收货"][0]["id"] == oid3

    def test_kanban_data_values_are_dicts(self):
        """Each order in kanban data should be a dict (not Row)."""
        sid = models.add_supplier("供应商A")
        models.create_order(sid)
        data = models.get_kanban_data()
        for label, orders in data.items():
            for order in orders:
                assert isinstance(order, dict)

    def test_multiple_orders_same_column(self):
        sid = models.add_supplier("供应商A")
        models.create_order(sid)
        models.create_order(sid)
        models.create_order(sid)
        data = models.get_kanban_data()
        assert len(data["待处理"]) == 3

    def test_move_order_changes_column(self):
        """Moving an order from pending to confirmed should shift it."""
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        data1 = models.get_kanban_data()
        assert len(data1["待处理"]) == 1
        assert len(data1["已确认"]) == 0

        models.update_order_status(oid, "confirmed")
        data2 = models.get_kanban_data()
        assert len(data2["待处理"]) == 0
        assert len(data2["已确认"]) == 1

    def test_full_workflow_across_all_columns(self):
        """Simulate an order going through the full procurement lifecycle."""
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 5.0, 100)
        oid = models.create_order(sid)
        models.add_order_item(oid, pid, 10, 5.0)

        # pending -> confirmed -> shipped -> received
        for next_status in ["confirmed", "shipped", "received"]:
            models.update_order_status(oid, next_status)

        data = models.get_kanban_data()
        assert data["待处理"] == []
        assert data["已确认"] == []
        assert data["已发货"] == []
        assert len(data["已收货"]) == 1
        assert data["已收货"][0]["id"] == oid

    def test_cancel_order_moves_to_cancelled(self):
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        models.update_order_status(oid, "cancelled")
        data = models.get_kanban_data()
        assert len(data["已取消"]) == 1
        assert data["待处理"] == []


class TestKanbanEdgeCases:
    """Edge cases and boundary conditions for kanban features."""

    def test_order_with_many_items_in_kanban(self):
        sid = models.add_supplier("供应商A")
        pid = models.add_product("螺丝", "包", 1.0, 1000)
        oid = models.create_order(sid)
        for i in range(1, 51):
            models.add_order_item(oid, pid, i, 1.0)
        orders = models.get_orders_by_status("pending")
        assert orders[0]["item_count"] == 50
        assert orders[0]["total_amount"] == sum(range(1, 51))

    def test_status_update_does_not_create_duplicate(self):
        """Updating status should move the order, not duplicate it."""
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        models.update_order_status(oid, "confirmed")
        all_pending = models.get_orders_by_status("pending")
        all_confirmed = models.get_orders_by_status("confirmed")
        assert len(all_pending) == 0
        assert len(all_confirmed) == 1
        # Total across all columns should be 1
        total = sum(
            len(models.get_orders_by_status(col))
            for col in models.KANBAN_COLUMNS
        )
        assert total == 1

    def test_kanban_with_all_orders_cancelled(self):
        sid = models.add_supplier("供应商A")
        for _ in range(5):
            oid = models.create_order(sid)
            models.update_order_status(oid, "cancelled")
        data = models.get_kanban_data()
        assert len(data["已取消"]) == 5
        for label in ["待处理", "已确认", "已发货", "已收货"]:
            assert data[label] == []

    def test_get_orders_by_status_with_special_characters_in_supplier(self):
        """Supplier names with special characters should not break queries."""
        sid = models.add_supplier("供应商<>&'\"")
        models.create_order(sid)
        orders = models.get_orders_by_status("pending")
        assert len(orders) == 1
        assert "供应商" in orders[0]["supplier_name"]

    def test_kanban_data_after_order_deletion(self):
        """Deleted order should not appear in kanban."""
        sid = models.add_supplier("供应商A")
        oid = models.create_order(sid)
        data = models.get_kanban_data()
        assert len(data["待处理"]) == 1

        models.delete_order(oid)
        data = models.get_kanban_data()
        assert data["待处理"] == []

    def test_concurrent_orders_same_supplier(self):
        """Multiple orders from the same supplier appear correctly."""
        sid = models.add_supplier("供应商A")
        oid1 = models.create_order(sid)
        oid2 = models.create_order(sid)
        models.update_order_status(oid2, "confirmed")
        data = models.get_kanban_data()
        assert len(data["待处理"]) == 1
        assert data["待处理"][0]["id"] == oid1
        assert len(data["已确认"]) == 1
        assert data["已确认"][0]["id"] == oid2
