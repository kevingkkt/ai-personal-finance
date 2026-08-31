from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DATABASE_NAME = "/app/data/savings_goals.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.get("/")
def health():
    return jsonify({
        "service": "savings-goals-database-service",
        "status": "running"
    })


@app.get("/goals")
def get_goals():
    conn = get_db_connection()

    goals = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        ORDER BY target_date
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in goals])


@app.get("/goals/<int:goal_id>")
def get_goal(goal_id):
    conn = get_db_connection()

    goal = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        WHERE id = ?
    """, (goal_id,)).fetchone()

    conn.close()

    if goal is None:
        return jsonify({"error": "Savings goal not found"}), 404

    return jsonify(dict(goal))


@app.get("/goals/by-date")
def get_goals_by_date():
    target_date = request.args.get("target_date", "").strip()

    if not target_date:
        return jsonify({"error": "target_date is required"}), 400

    conn = get_db_connection()

    goals = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        WHERE target_date = ?
    """, (target_date,)).fetchall()

    conn.close()

    if not goals:
        return jsonify({"error": "No savings goals found"}), 404

    return jsonify([dict(row) for row in goals])


@app.get("/goals/<int:goal_id>/contributions")
def get_contributions(goal_id):
    conn = get_db_connection()

    goal = conn.execute(
        "SELECT id FROM savings_goals WHERE id = ?",
        (goal_id,)
    ).fetchone()

    if goal is None:
        conn.close()
        return jsonify({"error": "Savings goal not found"}), 404

    contributions = conn.execute("""
        SELECT id, goal_id, amount, contribution_date
        FROM contributions
        WHERE goal_id = ?
        ORDER BY contribution_date DESC
    """, (goal_id,)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in contributions])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6003, debug=True)