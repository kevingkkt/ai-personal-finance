from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "transactions.db")
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/transactions", methods=["GET"])
def get_transactions():
    connection = get_connection()

    transactions = connection.execute(
        "SELECT * FROM transactions"
    ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in transactions])


@app.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    connection = get_connection()

    transaction = connection.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    connection.close()

    if transaction is None:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify(dict(transaction))


@app.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json()

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO transactions
        (type, category, amount, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["type"],
            data["category"],
            data["amount"],
            data["date"],
            data.get("description", "")
        )
    )

    connection.commit()
    transaction_id = cursor.lastrowid
    connection.close()

    return jsonify({
        "message": "Transaction created",
        "id": transaction_id
    }), 201


@app.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    data = request.get_json()

    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE transactions
        SET type = ?,
            category = ?,
            amount = ?,
            date = ?,
            description = ?
        WHERE id = ?
        """,
        (
            data["type"],
            data["category"],
            data["amount"],
            data["date"],
            data.get("description", ""),
            transaction_id
        )
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"message": "Transaction updated"})


@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    connection = get_connection()

    cursor = connection.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"message": "Transaction deleted"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Kevin Database Microservice"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )