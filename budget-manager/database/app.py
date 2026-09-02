from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "budgets.db")
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/budgets", methods=["GET"])
def get_budgets():
    connection = get_connection()

    budgets = connection.execute(
        "SELECT * FROM budgets"
    ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in budgets])


@app.route("/budgets/<int:budget_id>", methods=["GET"])
def get_budget(budget_id):
    connection = get_connection()

    budget = connection.execute(
        "SELECT * FROM budgets WHERE id = ?",
        (budget_id,)
    ).fetchone()

    connection.close()

    if budget is None:
        return jsonify({"error": "Budget not found"}), 404

    return jsonify(dict(budget))


@app.route("/budgets", methods=["POST"])
def create_budget():
    data = request.get_json()

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO budgets
        (name, amount, start_date, end_date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["amount"],
            data["start_date"],
            data["end_date"],
            data.get("description", "")
        )
    )

    connection.commit()
    budget_id = cursor.lastrowid
    connection.close()

    return jsonify({
        "message": "Budget created",
        "id": budget_id
    }), 201


@app.route("/budgets/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    data = request.get_json()

    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE budgets
        SET name = ?,
            amount = ?,
            start_date = ?,
            end_date = ?,
            description = ?
        WHERE id = ?
        """,
        (
            data["name"],
            data["amount"],
            data["start_date"],
            data["end_date"],
            data.get("description", ""),
            budget_id
        )
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Budget not found"}), 404

    return jsonify({"message": "Budget updated"})


@app.route("/budgets/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    connection = get_connection()

    cursor = connection.execute(
        "DELETE FROM budgets WHERE id = ?",
        (budget_id,)
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Budget not found"}), 404

    return jsonify({"message": "Budget deleted"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Budget-Manager Database Microservice"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5007,
        debug=True
    )