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

    # Calculate financial totals using Python
    total_income = 0.0
    total_expenses = 0.0
    expense_categories = {}

    for transaction in transaction_data:
        transaction_type = transaction["type"].lower()
        amount = float(transaction["amount"])
        category = transaction["category"]

        if transaction_type == "income":
            total_income += amount

        elif transaction_type == "expense":
            total_expenses += amount

            if category not in expense_categories:
                expense_categories[category] = 0.0

            expense_categories[category] += amount

    # Calculate remaining income
    remaining_amount = total_income - total_expenses

    # Save 60% of remaining income
    recommended_saving = max(0, remaining_amount * 0.60)

    # Find highest spending category
    if expense_categories:
        highest_category = max(
            expense_categories,
            key=expense_categories.get
        )

        highest_category_amount = expense_categories[highest_category]

    else:
        highest_category = "None"
        highest_category_amount = 0.0

    # DeepSeek receives the calculated information
    prompt = f"""
You are an AI assistant for a university personal finance project.

Transaction data:

{transaction_data}

The application calculated:

Total Income: ${total_income:.2f}
Total Expenses: ${total_expenses:.2f}
Remaining Income: ${remaining_amount:.2f}
Recommended Saving: ${recommended_saving:.2f}
Highest Spending Category: {highest_category} - ${highest_category_amount:.2f}

Review the financial summary.

The saving rule used by the application is:
Save 60% of the remaining income after expenses.

Do not provide investment, tax, loan, credit, or professional financial advice.
Do not recommend a different saving percentage.
Keep the response short.
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

        # DeepSeek has successfully reviewed the transaction summary
        response.json()

        # Final displayed values use Python calculations
        insight = (
            f"Total Income: ${total_income:,.2f}\n"
            f"Total Expenses: ${total_expenses:,.2f}\n"
            f"Highest Spending Category: "
            f"{highest_category} - ${highest_category_amount:,.2f}\n"
            f"Saving Suggestion: Save 60% of your remaining income "
            f"after expenses, which is ${recommended_saving:,.2f}."
        )

        return jsonify({
            "model": "deepseek-r1:1.5b",
            "insight": insight
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