"""CRUD operations for all entities."""

from db import get_connection, hash_password, verify_password


# ─── Users ─────────────────────────────────────────────────

def add_user(username, password, display_name=None):
    """Register a new user. Returns the new user id, or None if username exists."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
            (username, hash_password(password), display_name),
        )
        conn.commit()
        row_id = cursor.lastrowid
    except Exception:
        row_id = None
    finally:
        conn.close()
    return row_id


def get_user_by_username(username):
    """Return a user by username, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row


def verify_user(username, password):
    """Verify login credentials. Returns the user dict if valid, or None."""
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def get_all_users():
    """Return all users (without password hashes)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, display_name, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def delete_user(user_id):
    """Delete a user by id."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ─── Suppliers ─────────────────────────────────────────────

def add_supplier(name, contact=None, phone=None, address=None):
    """Add a new supplier. Returns the new supplier id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO suppliers (name, contact, phone, address) VALUES (?, ?, ?, ?)",
        (name, contact, phone, address),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_suppliers():
    """Return all suppliers."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM suppliers ORDER BY id").fetchall()
    conn.close()
    return rows


def get_supplier(supplier_id):
    """Return a single supplier by id, or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    conn.close()
    return row


def update_supplier(supplier_id, **kwargs):
    """Update supplier fields. Ignored keys are silently skipped."""
    allowed = {"name", "contact", "phone", "address"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [supplier_id]
    conn = get_connection()
    conn.execute(f"UPDATE suppliers SET {set_clause} WHERE id = ?", values)
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def delete_supplier(supplier_id):
    """Delete a supplier by id."""
    conn = get_connection()
    conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit()
    conn.close()


# ─── Products ──────────────────────────────────────────────

def add_product(name, unit, price, stock=0):
    """Add a new product. Returns the new product id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO products (name, unit, price, stock) VALUES (?, ?, ?, ?)",
        (name, unit, price, stock),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_products():
    """Return all products."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    conn.close()
    return rows


def get_product(product_id):
    """Return a single product by id, or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return row


def update_product(product_id, **kwargs):
    """Update product fields."""
    allowed = {"name", "unit", "price", "stock"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    conn = get_connection()
    conn.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_product(product_id):
    """Delete a product by id."""
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# ─── Purchase Orders ───────────────────────────────────────

def create_order(supplier_id):
    """Create a new purchase order. Returns the new order id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO purchase_orders (supplier_id) VALUES (?)",
        (supplier_id,),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def add_order_item(order_id, product_id, quantity, unit_price):
    """Add an item to an order. Auto-calculates subtotal and updates total."""
    subtotal = round(quantity * unit_price, 2)
    conn = get_connection()
    conn.execute(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) "
        "VALUES (?, ?, ?, ?, ?)",
        (order_id, product_id, quantity, unit_price, subtotal),
    )
    conn.execute(
        "UPDATE purchase_orders SET total_amount = total_amount + ? WHERE id = ?",
        (subtotal, order_id),
    )
    conn.commit()
    conn.close()


def get_all_orders():
    """Return all orders with supplier name."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT o.id, s.name AS supplier_name, o.total_amount, o.status, o.created_at "
        "FROM purchase_orders o "
        "JOIN suppliers s ON o.supplier_id = s.id "
        "ORDER BY o.id"
    ).fetchall()
    conn.close()
    return rows


def get_order(order_id):
    """Return a single order, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT o.*, s.name AS supplier_name "
        "FROM purchase_orders o "
        "JOIN suppliers s ON o.supplier_id = s.id "
        "WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    conn.close()
    return row


def get_order_items(order_id):
    """Return all items for a given order."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT oi.*, p.name AS product_name, p.unit AS product_unit "
        "FROM order_items oi "
        "JOIN products p ON oi.product_id = p.id "
        "WHERE oi.order_id = ?",
        (order_id,),
    ).fetchall()
    conn.close()
    return rows


def update_order_status(order_id, status):
    """Update the status of an order."""
    conn = get_connection()
    conn.execute(
        "UPDATE purchase_orders SET status = ? WHERE id = ?",
        (status, order_id),
    )
    conn.commit()
    conn.close()


def delete_order(order_id):
    """Delete an order and its items."""
    conn = get_connection()
    conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    conn.execute("DELETE FROM purchase_orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


# ─── Kanban Board ──────────────────────────────────────────

KANBAN_COLUMNS = ["pending", "confirmed", "shipped", "received", "cancelled"]
KANBAN_LABELS = {
    "pending": "待处理",
    "confirmed": "已确认",
    "shipped": "已发货",
    "received": "已收货",
    "cancelled": "已取消",
}


def get_orders_by_status(status):
    """Return all orders for a given status column, with supplier name and item count."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT o.id, o.total_amount, o.status, o.created_at, "
        "       s.name AS supplier_name, "
        "       COUNT(oi.id) AS item_count "
        "FROM purchase_orders o "
        "JOIN suppliers s ON o.supplier_id = s.id "
        "LEFT JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status = ? "
        "GROUP BY o.id "
        "ORDER BY o.id DESC",
        (status,),
    ).fetchall()
    conn.close()
    return rows


def get_kanban_data():
    """Return all orders grouped by status for the kanban board.

    Returns a dict: { status_label: [ {id, supplier_name, total_amount,
    item_count, created_at}, ... ], ... }
    """
    data = {}
    for status in KANBAN_COLUMNS:
        orders = get_orders_by_status(status)
        data[KANBAN_LABELS[status]] = [
            dict(o) for o in orders
        ]
    return data
