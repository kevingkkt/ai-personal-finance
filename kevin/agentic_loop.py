import requests
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "database",
    "transactions.db"
)

BACKEND_URL = "http://127.0.0.1:5001"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


def plan():
    print("=" * 60)
    print("KEVIN - INCOME & EXPENSE AGENTIC LOOP")
    print("=" * 60)

    print("\nPLAN")

    plan_data = {
        "goal": "Review the Income & Expense Tracker implementation",
        "checks": [
            "database records",
            "transactions API",
            "CRUD functionality",
            "microservices connection",
            "Docker integration"
        ]
    }

    print(plan_data)


def act():
    print("\nACT")
    print("Checking transaction database and backend API.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM transactions")
    record_count = cursor.fetchone()[0]

    conn.close()

    return record_count


def observe(record_count):
    print("\nOBSERVE")

    print(f"Database contains {record_count} transaction records.")

    try:
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            timeout=10
        )

        if response.status_code == 200:
            transactions = response.json()

            print("Transactions API is working.")
            print(f"API returned {len(transactions)} records.")

            return True
        else:
            print("Transactions API returned an error.")
            return False

    except requests.exceptions.RequestException:
        print("Could not connect to backend API.")
        return False


def adapt(api_working, record_count):
    print("\nADAPT")

    if not api_working:
        print("Backend API requires review before continuing.")
        return

    prompt = f"""
You are the implementation review AI for a university software project.

Review the following Income & Expense Tracker implementation.

Current implementation:
- SQLite database
- Database contains {record_count} transaction records
- Flask database microservice
- Flask backend REST API
- CRUD operations
- HTML, CSS, JavaScript and HTMX frontend
- Docker and Docker Compose
- AI financial insights using DeepSeek
- Backend transaction API is working

Your role is to review the SOFTWARE IMPLEMENTATION only.

Check:
- software quality
- reliability
- usability
- microservices design
- API design
- database implementation
- Docker integration

Based only on the implementation information above, identify the single
most important software improvement.

Return exactly this format:

Improvement: <one short improvement>
Reason: <one short reason>

Do not list multiple improvements.
Do not suggest functionality that is already implemented.
Do not provide financial advice.
Do not review the written report.
Do not use Markdown.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        if response.status_code == 200:
            result = response.json()

            print("\nIMPLEMENTATION AI REVIEW")
            print("Model: Qwen")
            print(result["response"])
        else:
            print("Qwen implementation review could not be generated.")

    except requests.exceptions.RequestException as error:
        print("Could not connect to Qwen through Ollama.")
        print(error)


def main():
    plan()

    record_count = act()

    api_working = observe(record_count)

    adapt(api_working, record_count)

    print("\nAGENTIC LOOP COMPLETE")


if __name__ == "__main__":
    main()