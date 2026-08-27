from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE_API_URL = os.environ.get(
    "DATABASE_API_URL",
    "http://127.0.0.1:5004"
)

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)


@app.route("/budgets", methods=["GET"])
def get_budgets():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/budgets",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/budgets/<int:budget_id>", methods=["GET"])
def get_budget(budget_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/budgets/{budget_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/budgets", methods=["POST"])
def create_budget():
    try:
        response = requests.post(
            f"{DATABASE_API_URL}/budgets",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/budgets/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    try:
        response = requests.put(
            f"{DATABASE_API_URL}/budgets/{budget_id}",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/budgets/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/budgets/{budget_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


# HTMX route
@app.route("/budgets-html", methods=["GET"])
def get_budgets_html():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/budgets",
            timeout=10
        )

        if response.status_code != 200:
            return "<p>Could not load budgets.</p>", 500

        budgets = response.json()

        rows = ""

        for budget in budgets:
            rows += f"""
            <tr>
                <td>{budget['id']}</td>
                <td>{budget['name']}</td>
                <td>${budget['amount']:.2f}</td>
                <td>{budget['start_date']}</td>
                <td>{budget['end_date']}</td>
                <td>{budget['description']}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Amount</th>
                    <th>Start Date</th>
                    <th>End Date</th>
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
            f"{DATABASE_API_URL}/budgets",
            timeout=10
        )

        if database_response.status_code != 200:
            return jsonify({
                "error": "Could not retrieve budget data"
            }), 500

        budget_data = database_response.json()

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

    prompt = f"""
You are an AI assistant for a university personal finance project.

Analyse these monthly budgets::

{budget_data}

Return ONLY the final answer.
Do not include your reasoning, thinking process, analysis steps, or a second final answer.

Use exactly this format:

Budget to Decrease: <budget_name> - <amount_to_decrease>

Rules:
- Calculate using only the budget data provided.
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
        "service": "Budget-Manager Backend API"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5004
    )