"""Unit tests for the procurement system."""

import pytest
import sqlite3
from db import get_connection, init_db
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
