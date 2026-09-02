from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from collections import defaultdict
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE_API_URL = os.environ.get(
    "DATABASE_API_URL",
    "http://127.0.0.1:6002"
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

def build_budget_summary(budgets):
    if not budgets:
        return {
            "budget_count": 0,
            "total_budget": 0.0,
            "average_category_amount": 0.0,
            "largest_category": None,
            "smallest_category": None,
            "top_categories_by_amount": [],
            "categories": [],
            "ending_soon": [],
            "description_groups": {},
            "date_overlap": [],
            "potential_trim_candidates": []
        }

    parsed = []
    for item in budgets:
        parsed.append({
            "id": item.get("id"),
            "name": item.get("name", ""),
            "amount": float(item.get("amount", 0) or 0),
            "start_date": item.get("start_date"),
            "end_date": item.get("end_date"),
            "description": item.get("description", "")
        })

    total_budget = sum(item["amount"] for item in parsed)
    average_category_amount = total_budget / len(parsed)

    sorted_by_amount = sorted(parsed, key=lambda x: x["amount"], reverse=True)
    largest_category = sorted_by_amount[0]
    smallest_category = sorted(parsed, key=lambda x: x["amount"])[0]

    categories = []
    for item in parsed:
        share_pct = (item["amount"] / total_budget * 100) if total_budget else 0
        categories.append({
            "name": item["name"],
            "amount": round(item["amount"], 2),
            "start_date": item["start_date"],
            "end_date": item["end_date"],
            "description": item["description"],
            "share_pct": round(share_pct, 2)
        })

    today = datetime.today().date()
    ending_soon = []
    for item in parsed:
        if not item["end_date"]:
            continue
        try:
            end_date = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        days_left = (end_date - today).days
        if days_left <= 30:
            ending_soon.append({
                "name": item["name"],
                "amount": round(item["amount"], 2),
                "end_date": item["end_date"],
                "days_left": days_left
            })

    keyword_map = {
        "food": ["food", "grocery", "groceries", "dining", "meal", "eat"],
        "transport": ["transport", "fuel", "travel", "commute", "car", "bus"],
        "lifestyle": ["entertainment", "movie", "streaming", "hobby", "shopping", "leisure"],
        "housing": ["rent", "housing", "mortgage", "utilities", "home", "electric", "water"],
        "health": ["health", "medical", "pharmacy", "fitness", "wellness"]
    }

    grouped = defaultdict(list)
    for item in parsed:
        text = f"{item['name']} {item['description']}".lower()
        matched = False
        for group_name, keywords in keyword_map.items():
            if any(keyword in text for keyword in keywords):
                grouped[group_name].append(item["name"])
                matched = True
        if not matched:
            grouped["other"].append(item["name"])

    date_overlap = []
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            a = parsed[i]
            b = parsed[j]

            if not a["start_date"] or not b["start_date"] or not a["end_date"] or not b["end_date"]:
                continue

            try:
                a_start = datetime.strptime(a["start_date"], "%Y-%m-%d").date()
                a_end = datetime.strptime(a["end_date"], "%Y-%m-%d").date()
                b_start = datetime.strptime(b["start_date"], "%Y-%m-%d").date()
                b_end = datetime.strptime(b["end_date"], "%Y-%m-%d").date()
            except ValueError:
                continue

            overlap_start = max(a_start, b_start)
            overlap_end = min(a_end, b_end)

            if overlap_start <= overlap_end:
                overlap_days = (overlap_end - overlap_start).days + 1
                date_overlap.append({
                    "category_a": a["name"],
                    "category_b": b["name"],
                    "overlap_days": overlap_days
                })

    trim_candidates = []
    for item in sorted(parsed, key=lambda x: x["amount"], reverse=True)[1:4]:
        share_pct = (item["amount"] / total_budget * 100) if total_budget else 0
        trim_candidates.append({
            "name": item["name"],
            "amount": round(item["amount"], 2),
            "share_pct": round(share_pct, 2)
        })

    return {
        "budget_count": len(parsed),
        "total_budget": round(total_budget, 2),
        "average_category_amount": round(average_category_amount, 2),
        "largest_category": {
            "name": largest_category["name"],
            "amount": round(largest_category["amount"], 2),
            "share_pct": round((largest_category["amount"] / total_budget * 100) if total_budget else 0, 2)
        },
        "smallest_category": {
            "name": smallest_category["name"],
            "amount": round(smallest_category["amount"], 2),
            "share_pct": round((smallest_category["amount"] / total_budget * 100) if total_budget else 0, 2)
        },
        "top_categories_by_amount": [
            {
                "name": item["name"],
                "amount": round(item["amount"], 2),
                "share_pct": round((item["amount"] / total_budget * 100) if total_budget else 0, 2)
            }
            for item in sorted_by_amount[:5]
        ],
        "categories": categories,
        "ending_soon": ending_soon,
        "description_groups": dict(grouped),
        "date_overlap": date_overlap,
        "potential_trim_candidates": trim_candidates
    }


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

    summary = build_budget_summary(budget_data)

    prompt = f"""
You are a personal finance assistant.

The user has a list of monthly budget categories with amounts and date ranges.
Use only the data provided below.

Budget summary:
{summary}

Important rules:
- Do not choose a category as the trim target simply because it is the smallest amount.
- A trim target must be a meaningful spend category, ideally in the top 3 categories by amount or clearly discretionary such as dining, entertainment, travel, shopping, hobbies, leisure, or lifestyle.
- Never choose a category as the most likely trim target if it is below 10% of total budget and not among the top 3 categories by amount, unless no better discretionary option exists.
- If all budget date ranges are the same, do not claim timing-related issues such as longest wait period, shortest wait period, or pressure caused by long delays.
- If all budget date ranges are the same, any balance guidance must be based on category size, concentration, or imbalance, not timing.
- Do not invent extra facts, numbers, or assumptions.
- Do not recommend increasing spending.
- Do not provide investment, tax, loan, credit, or professional financial advice.
- Use plain text only.
- No Markdown, no headings, no bullet lists, no emojis.

Return exactly 3 insights, numbered 1 to 3.

Format exactly:
1. Biggest category: <category_name> - <amount>
   Reason: <brief explanation of why this is the largest category and what it means>
   Recommendation: <clear action>

2. Most likely trim target: <category_name> - <amount>
   Reason: <why this category is the best place to reduce spending based on size, discretionary nature, and overall allocation>
   Recommendation: <clear action>

3. Balance: <smallest or most underfunded category> - <amount>
   Reason: <brief explanation of why this category may be too low relative to the rest of the plan, if relevant>
   Recommendation: <suggest moving a small amount from a larger category to better balance the smaller one without creating a major financial strain>

Rules for Balance:
- If one budget is small relative to the rest of the plan, it is acceptable to suggest shifting a modest amount from a larger category to make the smaller category more realistic.
- The recommendation must be phrased as a balancing adjustment, not a risk warning.
- Do not claim a small category is a financial crisis or threat.
- Keep the recommendation realistic and modest.

Examples of valid balance suggestions:
- "Move $20 from Housing to increase the smaller Entertainment budget so it better matches your lifestyle."
- "Shift a small portion from Groceries to the underfunded Health budget to improve balance."

Examples of invalid balance suggestions:
- "Fish $30 causes financial strain."
- "This category has the longest wait period."
- "The small budget is a major risk because it is tiny."

If no budget data is available, return:
1. Biggest category: No data available
   Reason: There are no budget entries to analyse.
   Recommendation: Add at least one budget before requesting insights.
2. Most likely trim target: No data available
   Reason: There are no budget entries to analyse.
   Recommendation: Add at least one budget before requesting insights.
3. Balance: No data available
   Reason: There are no budget entries to analyse.
   Recommendation: Add at least one budget before requesting insights.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2.5:3b-instruct",
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
            "model": "qwen2.5:3b-instruct",
            "insight": result.get("response", "No insight generated")
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
        port=5002
    )