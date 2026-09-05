"""Flask API server for the kanban board view."""

from flask import Flask, jsonify, request, send_from_directory
from db import init_db
import models

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    """Serve the kanban page."""
    return send_from_directory("static", "kanban.html")


@app.route("/api/kanban")
def kanban_data():
    """Return all orders grouped by status."""
    data = models.get_kanban_data()
    return jsonify(data)


@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Move an order to a new status."""
    body = request.get_json(silent=True)
    if not body or "status" not in body:
        return jsonify({"error": "missing 'status' field"}), 400

    new_status = body["status"]
    if new_status not in models.VALID_STATUSES:
        return jsonify({"error": f"invalid status: {new_status}"}), 400

    success = models.move_order(order_id, new_status)
    if not success:
        return jsonify({"error": f"order {order_id} not found"}), 404

    return jsonify({"ok": True, "order_id": order_id, "status": new_status})


def create_app(test_db_path=None):
    """Create and configure the app. Used for testing."""
    if test_db_path:
        import db
        original_db_file = db.DB_FILE
        db.DB_FILE = test_db_path
        init_db(test_db_path)
        app.config["TEST_DB"] = test_db_path
    else:
        init_db()
    return app


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
