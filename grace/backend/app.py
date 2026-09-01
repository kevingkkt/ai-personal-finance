from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE_API_URL = os.environ.get(
    "DATABASE_API_URL",
    "http://127.0.0.1:6003"
)

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

@app.route("/goals", methods=["GET"])
def get_goals():
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/goals",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals/<int:goal_id>", methods=["GET"])
def get_goal(goal_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/goals/{goal_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals", methods=["POST"])
def create_goal():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    try:
        response = requests.post(
            f"{DATABASE_API_URL}/goals",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals/<int:goal_id>", methods=["PUT"])
def update_goal(goal_id):
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    try:
        response = requests.put(
            f"{DATABASE_API_URL}/goals/{goal_id}",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/goals/{goal_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals/<int:goal_id>/contributions", methods=["GET"])
def get_contributions(goal_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/goals/{goal_id}/contributions",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/contributions/<int:contribution_id>", methods=["GET"])
def get_contribution(contribution_id):
    try:
        response = requests.get(
            f"{DATABASE_API_URL}/contributions/{contribution_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/goals/<int:goal_id>/contributions", methods=["POST"])
def create_contribution(goal_id):
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    try:
        response = requests.post(
            f"{DATABASE_API_URL}/goals/{goal_id}/contributions",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/contributions/<int:contribution_id>", methods=["PUT"])
def update_contribution(contribution_id):
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    try:
        response = requests.put(
            f"{DATABASE_API_URL}/contributions/{contribution_id}",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

@app.route("/contributions/<int:contribution_id>", methods=["DELETE"])
def delete_contribution(contribution_id):
    try:
        response = requests.delete(
            f"{DATABASE_API_URL}/contributions/{contribution_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500
    
@app.route("/ai-insights", methods=["POST"])
def ai_insights():
    input_data = request.get_json(silent=True) or {}

    goal_id = input_data.get("goal_id")
    user_input = str(input_data.get("input", "")).strip()

    if goal_id is None:
        return jsonify({
            "error": "goal_id is required"
        }), 400

    try:
        goal_response = requests.get(
            f"{DATABASE_API_URL}/goals/{goal_id}",
            timeout=10
        )

        if goal_response.status_code != 200:
            return (
                jsonify(goal_response.json()),
                goal_response.status_code
            )

        contributions_response = requests.get(
            f"{DATABASE_API_URL}/goals/{goal_id}/contributions",
            timeout=10
        )

        if contributions_response.status_code != 200:
            return (
                jsonify(contributions_response.json()),
                contributions_response.status_code
            )

        goal_data = goal_response.json()
        contribution_data = contributions_response.json()

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to database service"
        }), 500

    prompt = f"""
You are an AI savings assistant for a university personal finance project.

Analyse this savings goal:

{goal_data}

Contribution history:

{contribution_data}

The user has also provided this question or preference:

{user_input}

Provide:
1. A short summary of the current savings progress.
2. A practical regular contribution amount.
3. A short strategy for reaching the target date.
4. A warning if the goal appears unrealistic.

Return only the final answer.
Do not include your reasoning or thinking process.
Do not provide investment, tax, credit, loan, or legal advice.
Keep the response concise and practical.
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "deepseek-r1:1.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )

        if response.status_code != 200:
            return jsonify({
                "error": (
                    "AI service unavailable with status code "
                    f"{response.status_code}"
                )
            }), 500

        result = response.json()

        return jsonify({
            "model": "deepseek-r1:1.5b",
            "goal_id": goal_id,
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
        "service": "Savings Goals Backend API"
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5003
    )