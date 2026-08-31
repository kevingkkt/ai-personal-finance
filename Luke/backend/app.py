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

#get all the bills
@app.route("/bills", methods=["GET"])
def get_bills():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

#grab a single bill by id
@app.route("/bills/<int:bill_id>", methods=["GET"])
def get_bill(bill_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/bills", methods=["POST"])
def create_bill():
    try:
        response = requests.post(
            f"{DATABASE_API_URL}/bills",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/bills/<int:bill_id>", methods=["PUT"])
def update_bill(bill_id):
    try:
        response = requests.put(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


@app.route("/bills/<int:bill_id>", methods=["DELETE"])
def delete_bill(bill_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500


# HTMX route
@app.route("/bills-html", methods=["GET"])
def get_bills_html():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/bills",
            timeout=10
        )

        if response.status_code != 200:
            return "<p>The bills were unable to be loaded.</p>", 500

        bills = response.json()

        rows = ""

        for bill in bills:
            rows += f"""
            <tr>
                <td>{bill['bill_id']}</td>
                <td>{bill['payment_status']}</td>
                <td>{bill['due_date']}</td>
                <td>${bill['amount']:.2f}</td>
                <td>{bill['description']}</td>
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
            f"{DATABASE_API_URL}/bills",
            timeout=10
        )

        if database_response.status_code != 200:
            return jsonify({
                "error": "Could not get the bill data"
            }), 500

        bill_data = database_response.json()

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

    prompt = f"""
You are a intelligent ai assistant that is able to analyse incomining  bills and provide insights on making sure that bills are being paid on time  and won't miss a bill payment.


Analyse the following bill data and give insights on how to manage the bills effectively:

{bill_data}

Output the following in this exact format:
Give a summary of the unpaid bills, including the total amount due and the number of unpaid bills.
and then give a list of reccommendations on how to pay off the bills the best way possible each week and the amount that they should pay each week to make sure that they are paying off the bills on time and not missing any payments.

Return ONLY the final answer.
Do not include your reasoning, thinking process, analysis steps, or a second final answer.

Rules:
Return as a string in about 1 paragraph.
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
                "error": "The AI service is unavailable with the following status code: " + str(response.status_code)
            }), 500

        result = response.json()

        return jsonify({
            "model": "deepseek-r1:1.5b",
            "insight": result["response"]
        })

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Sorrt the program could not mange toconnect to Ollama"
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "The API worked in backend"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5001
    )