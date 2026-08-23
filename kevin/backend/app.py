from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE_API_URL = os.environ.get(
    "DATABASE_API_URL",
    "http://127.0.0.1:5002"
)

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)


@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/transactions",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/transactions/{transaction_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/transactions", methods=["POST"])
def create_transaction():
    try:
        response = requests.post(
            f"{DATABASE_API_URL}/transactions",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    try:
        response = requests.put(
            f"{DATABASE_API_URL}/transactions/{transaction_id}",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/transactions/{transaction_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


# HTMX route
@app.route("/transactions-html", methods=["GET"])
def get_transactions_html():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/transactions",
            timeout=10
        )

        if response.status_code != 200:
            return "<p>Could not load transactions.</p>", 500

        transactions = response.json()

        rows = ""

        for transaction in transactions:
            rows += f"""
            <tr>
                <td>{transaction['id']}</td>
                <td>{transaction['type']}</td>
                <td>{transaction['category']}</td>
                <td>${transaction['amount']:.2f}</td>
                <td>{transaction['date']}</td>
                <td>{transaction['description']}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Type</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Description</th>
                </tr>
            </thead>

            <tbody>
                {rows}
            </tbody>
        </table>
        """

    except requests.exceptions.RequestException:
        return "<p>Database service unavailable.</p>", 500


@app.route("/ai-insights", methods=["GET"])
def ai_insights():
    try:
        database_response = requests.get(
            f"{DATABASE_API_URL}/transactions",
            timeout=10
        )

        if database_response.status_code != 200:
            return jsonify({
                "error": "Could not retrieve transaction data"
            }), 500

        transaction_data = database_response.json()

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

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
            timeout=300
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


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Kevin Backend API"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5001
    )