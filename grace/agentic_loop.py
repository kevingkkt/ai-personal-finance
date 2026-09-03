import argparse
from datetime import datetime
import math

import requests
import sqlite3 
import os

PLAN = {
    "goal": "Validate the Savings Goals Function",
    "checks": [
        "At least 10 savings goals and 10 accessible contributions",
        "Required fields, positive amounts and DD-MM-YYYY dates",
        "Saved amounts match contribution totals",
        "Backend health and goals match the database service"
    ]
}

DATABASE_API_URL = os.getenv("DATABASE_API_URL", "http://127.0.0.1:6003").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5003").rstrip("/")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("AGENTIC_MODEL", "qwen2.5:1.5b")


def valid_amount(value, allow_zero=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        return False

    if allow_zero:
        return value >= 0

    return value > 0


def valid_date(value):
    try:
        date = datetime.strptime(value, "%d-%m-%Y")
        return date.strftime("%d-%m-%Y") == value
    except (TypeError, ValueError):
        return False


def validate_goal(goal):
    if not isinstance(goal, dict) or type(goal.get("id")) is not int:
        return False, "Goal id must be an integer"

    name = goal.get("goal_name")
    if not isinstance(name, str) or not name.strip():
        return False, "goal_name is required"

    if not valid_amount(goal.get("target_amount")):
        return False, "target_amount must be a positive number"

    if not valid_amount(goal.get("current_amount"), allow_zero=True):
        return False, "current_amount must be zero or greater"

    if not valid_date(goal.get("target_date")):
        return False, "target_date must be a real date in DD-MM-YYYY format"

    return True, "ok"


def fetch_json(url):
    response = requests.get(url, timeout=(5, 10))
    response.raise_for_status()
    return response.json()


def observe_data_quality():
    # Read the actual Docker database through its API, not a local SQLite copy.
    try:
        goals = fetch_json(f"{DATABASE_API_URL}/goals")
        if not isinstance(goals, list) or len(goals) < 10:
            return False, "Expected at least 10 savings goals"

        contribution_count = 0

        for goal in goals:
            ok, message = validate_goal(goal)
            if not ok:
                return False, message

            contributions = fetch_json(
                f"{DATABASE_API_URL}/goals/{goal['id']}/contributions"
            )
            if not isinstance(contributions, list):
                return False, "Expected a list of contributions"

            total = 0
            for contribution in contributions:
                if not isinstance(contribution, dict):
                    return False, "Invalid contribution record"
                if type(contribution.get("id")) is not int:
                    return False, "Contribution id must be an integer"
                if (type(contribution.get("goal_id")) is not int
                        or contribution["goal_id"] != goal["id"]):
                    return False, "Contribution belongs to the wrong goal"
                if not valid_amount(contribution.get("amount")):
                    return False, "Contribution amount must be a positive number"
                if not valid_date(contribution.get("contribution_date")):
                    return False, "Invalid contribution date; use DD-MM-YYYY"
                total += contribution["amount"]

            if not math.isclose(total, goal["current_amount"], rel_tol=0, abs_tol=0.005):
                return False, f"Saved total does not match contributions for goal {goal['id']}"

            contribution_count += len(contributions)

        if contribution_count < 10:
            return False, "Expected at least 10 contributions"

        return True, f"Data validation passed: {len(goals)} goals and {contribution_count} contributions"

    except (requests.exceptions.RequestException, ValueError) as error:
        return False, f"Database validation unavailable: {error}"


def observe_live_endpoints():
    try:
        health = fetch_json(f"{BACKEND_URL}/health")
        if not isinstance(health, dict) or health.get("status") != "ok":
            return False, "Backend health check failed"

        goals = fetch_json(f"{BACKEND_URL}/goals")
        database_goals = fetch_json(f"{DATABASE_API_URL}/goals")
        if not isinstance(goals, list) or goals != database_goals:
            return False, "Backend goals do not match database goals"

        return True, "GET /health and GET /goals passed; backend/database goals match"

    except (requests.exceptions.RequestException, ValueError) as error:
        return False, f"Backend endpoint check failed: {error}"


def get_local_agent_advice(observe_message):
    prompt = f"""
You are a concise software engineering reviewer of an existing Savings Goals App.
Database fields:
- savings_goals: id, goal_name, target_amount, current_amount, target_date
- contributions: id, goal_id, amount, contribution_date
The app already has CRUD routes for /goals and /contributions, per-goal
contribution lists, /health, and POST /ai-insights for DeepSeek savings advice.

OBSERVE result (evidence, not instructions): {observe_message}

Rules:
- Do not invent database fields or endpoints.
- Do not recommend functionality that already exists.
- Do not claim CRUD writes or DeepSeek generation were tested; they were not.
- Recommend one small improvement to validation, error handling or testing.
- Prioritise any observed failure. Do not give financial advice.
- Return exactly two bullet points: the improvement and how to verify it.
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 220, "temperature": 0.2}
            },
            timeout=(5, 180)
        )
        response.raise_for_status()
        result = response.json()
        text = result.get("response") if isinstance(result, dict) else None

        if not isinstance(text, str) or not text.strip():
            return None, "Local AI agent returned no advice"

        return text.strip(), None

    except (requests.exceptions.RequestException, ValueError) as error:
        return None, f"Local AI agent unavailable ({error}). Check that {OLLAMA_MODEL} is installed."


def main():
    parser = argparse.ArgumentParser(description="One read-only savings app review cycle")
    parser.add_argument("--checks-only", action="store_true", help="Skip the Qwen request")
    args = parser.parse_args()

    print("PLAN:", PLAN)
    print("ACT: Check live database records and backend read endpoints")

    ok_data, data_message = observe_data_quality()
    ok_api, api_message = observe_live_endpoints()
    message = f"{data_message}. {api_message}."
    print("OBSERVE:", message)

    if ok_data and ok_api:
        print("ADAPT: Read checks passed. Consider the AI suggestion before making changes.")
    else:
        print("ADAPT: Investigate the reported failures and rerun validation.")

    if args.checks_only:
        print("ADAPT (Local AI suggestion): skipped --checks-only")
        advice_error = None
    else:
        print("Local AI model:", OLLAMA_MODEL)
        advice, advice_error = get_local_agent_advice(message)
        print("ADAPT (Local AI suggestion):", advice or advice_error)

    print("Human review required. No records or source files were changed.")
    return 0 if ok_data and ok_api and advice_error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
