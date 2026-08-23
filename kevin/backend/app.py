from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import requests

app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "database",
        "transactions.db"
    )
)

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)   


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/transactions", methods=["GET"])
def get_transactions():
    conn = get_db_connection()

    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC"
    ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in transactions])


@app.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    conn = get_db_connection()

    transaction = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    conn.close()

    if transaction is None:
        return jsonify({
            "error": "Transaction not found"
        }), 404

    return jsonify(dict(transaction))


@app.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json()

    conn = get_db_connection()

    cursor = conn.execute(
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

    conn.commit()

    transaction_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "Transaction created",
        "id": transaction_id
    }), 201


@app.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    data = request.get_json()

    conn = get_db_connection()

    existing_transaction = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    if existing_transaction is None:
        conn.close()

        return jsonify({
            "error": "Transaction not found"
        }), 404

    conn.execute(
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

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Transaction updated"
    })


@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    conn = get_db_connection()

    existing_transaction = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    if existing_transaction is None:
        conn.close()

        return jsonify({
            "error": "Transaction not found"
        }), 404

    conn.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Transaction deleted"
    })


@app.route("/ai-insights", methods=["GET"])
def ai_insights():
    conn = get_db_connection()

    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC"
    ).fetchall()

    conn.close()

    transaction_data = [dict(row) for row in transactions]

    prompt = f"""
You are an AI assistant for a university personal finance project.

Analyse these income and expense transactions:

{transaction_data}

Return ONLY the final answer.
Do not include your reasoning, thinking process, analysis steps, or a second final answer.

Use exactly this format:

Total Income: $0.00
Total Expenses: $0.00
Highest Spending Category: Category - $0.00
Saving Suggestion: One short practical suggestion.

Rules:
- Calculate using only the transaction data provided.
- Do not use Markdown formatting.
- Do not use **, #, or LaTeX symbols.
- Do not suggest increasing spending as a way to save money.
- Do not provide investment, tax, loan, credit, or professional financial advice.
- Keep the saving suggestion to one short sentence.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "deepseek-r1:1.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if response.status_code != 200:
            return jsonify({
                "error": "AI service unavailable"
            }), 500

        result = response.json()

        return jsonify({
            "model": "deepseek-r1:1.5b",
            "insight": result["response"]
        })

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to Ollama"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5001
    )