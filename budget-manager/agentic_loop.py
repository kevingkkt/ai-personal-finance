import requests
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "database",
    "budgets.db"
)

BACKEND_URL = "http://127.0.0.1:5002"


def plan():
    print("=" * 60)
    print("BUDGET MANAGER - BUDGET TRACKING AGENTIC LOOP")
    print("=" * 60)

    print("\nPLAN")

    plan_data = {
        "goal": "Review the Budget Tracker",
        "checks": [
            "database records",
            "budgets API",
            "CRUD functionality",
            "AI spending insights"
        ]
    }

    print(plan_data)


def act():
    print("\nACT")
    print("Checking transaction database and backend API.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM budgets")
    record_count = cursor.fetchone()[0]

    conn.close()

    return record_count


def observe(record_count):
    print("\nOBSERVE")

    print(f"Database contains {record_count} budget records.")

    try:
        response = requests.get(
            f"{BACKEND_URL}/budgets",
            timeout=10
        )

        if response.status_code == 200:
            budgets = response.json()

            print("Budgets API is working.")
            print(f"API returned {len(budgets)} records.")

            return True
        else:
            print("Budgets API returned an error.")
            return False

    except requests.exceptions.RequestException:
        print("Could not connect to backend API.")
        return False


def adapt(api_working):
    print("\nADAPT")

    if api_working:
        prompt = """
You are reviewing a Budget Tracker for a university
software project.

The application currently has:
- SQLite budget storage
- CRUD API
- Web frontend
- Docker support
- AI budget insights using Qwen 2.5 3B Instruct

Suggest ONE short improvement for the application.

Do not give financial advice.
Focus only on software quality, reliability or usability.
"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:3b-instruct",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()

                print("AI Review:")
                print(result["response"])
            else:
                print("AI review could not be generated.")

        except requests.exceptions.RequestException:
            print("Could not connect to Ollama.")

    else:
        print("Backend API requires review before continuing.")


def main():
    plan()

    record_count = act()

    api_working = observe(record_count)

    adapt(api_working)

    print("\nAGENTIC LOOP COMPLETE")


if __name__ == "__main__":
    main()