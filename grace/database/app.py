from flask import Flask, jsonify, request
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "savings_goals.db")
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def valid_date(date_value):
    try:
        datetime.strptime(date_value, "%d-%m-%Y")
        return True
    except (ValueError, TypeError):
        return False


def update_current_amount(conn, goal_id):
    total = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM contributions
        WHERE goal_id = ?
    """, (goal_id,)).fetchone()[0]

    conn.execute("""
        UPDATE savings_goals
        SET current_amount = ?
        WHERE id = ?
    """, (total, goal_id))

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
        ORDER BY id
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in goals])


@app.get("/goals/by-date")
def get_goals_by_date():
    target_date = request.args.get("target_date", "").strip()

    if not target_date:
        return jsonify({
            "error": "target_date is required"
        }), 400

    if not valid_date(target_date):
        return jsonify({
            "error": "target_date must use DD-MM-YYYY format"
        }), 400

    conn = get_db_connection()

    goals = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        WHERE target_date = ?
        ORDER BY id
    """, (target_date,)).fetchall()

    conn.close()

    if not goals:
        return jsonify({
            "error": "No savings goals found"
        }), 404

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
        return jsonify({
            "error": "Savings goal not found"
        }), 404

    return jsonify(dict(goal))


@app.post("/goals")
def create_goal():
    data = request.get_json(silent=True) or {}

    goal_name = str(data.get("goal_name", "")).strip()
    target_amount = data.get("target_amount")
    target_date = data.get("target_date")

    if not goal_name:
        return jsonify({
            "error": "goal_name is required"
        }), 400

    try:
        target_amount = float(target_amount)
    except (TypeError, ValueError):
        return jsonify({
            "error": "target_amount must be a number"
        }), 400

    if target_amount <= 0:
        return jsonify({
            "error": "target_amount must be greater than zero"
        }), 400

    if not valid_date(target_date):
        return jsonify({
            "error": "target_date must use DD-MM-YYYY format"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO savings_goals (
            goal_name,
            target_amount,
            current_amount,
            target_date
        )
        VALUES (?, ?, ?, ?)
    """, (
        goal_name,
        target_amount,
        0,
        target_date
    ))

    conn.commit()

    new_goal = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        WHERE id = ?
    """, (cursor.lastrowid,)).fetchone()

    conn.close()

    return jsonify(dict(new_goal)), 201


@app.put("/goals/<int:goal_id>")
def update_goal(goal_id):
    data = request.get_json(silent=True) or {}

    goal_name = str(data.get("goal_name", "")).strip()
    target_amount = data.get("target_amount")
    target_date = data.get("target_date")

    if not goal_name:
        return jsonify({
            "error": "goal_name is required"
        }), 400

    try:
        target_amount = float(target_amount)
    except (TypeError, ValueError):
        return jsonify({
            "error": "target_amount must be a number"
        }), 400

    if target_amount <= 0:
        return jsonify({
            "error": "target_amount must be greater than zero"
        }), 400

    if not valid_date(target_date):
        return jsonify({
            "error": "target_date must use DD-MM-YYYY format"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute("""
        UPDATE savings_goals
        SET goal_name = ?,
            target_amount = ?,
            target_date = ?
        WHERE id = ?
    """, (
        goal_name,
        target_amount,
        target_date,
        goal_id
    ))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({
            "error": "Savings goal not found"
        }), 404

    conn.commit()

    updated_goal = conn.execute("""
        SELECT id, goal_name, target_amount, current_amount, target_date
        FROM savings_goals
        WHERE id = ?
    """, (goal_id,)).fetchone()

    conn.close()

    return jsonify(dict(updated_goal))


@app.delete("/goals/<int:goal_id>")
def delete_goal(goal_id):
    conn = get_db_connection()

    goal = conn.execute(
        "SELECT id FROM savings_goals WHERE id = ?",
        (goal_id,)
    ).fetchone()

    if goal is None:
        conn.close()
        return jsonify({
            "error": "Savings goal not found"
        }), 404

    # Delete contributions first because they reference the goal.
    conn.execute(
        "DELETE FROM contributions WHERE goal_id = ?",
        (goal_id,)
    )

    conn.execute(
        "DELETE FROM savings_goals WHERE id = ?",
        (goal_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Savings goal deleted successfully"
    })

@app.get("/goals/<int:goal_id>/contributions")
def get_contributions(goal_id):
    conn = get_db_connection()

    goal = conn.execute(
        "SELECT id FROM savings_goals WHERE id = ?",
        (goal_id,)
    ).fetchone()

    if goal is None:
        conn.close()
        return jsonify({
            "error": "Savings goal not found"
        }), 404

    contributions = conn.execute("""
        SELECT id, goal_id, amount, contribution_date
        FROM contributions
        WHERE goal_id = ?
        ORDER BY id
    """, (goal_id,)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in contributions])


@app.get("/contributions/<int:contribution_id>")
def get_contribution(contribution_id):
    conn = get_db_connection()

    contribution = conn.execute("""
        SELECT id, goal_id, amount, contribution_date
        FROM contributions
        WHERE id = ?
    """, (contribution_id,)).fetchone()

    conn.close()

    if contribution is None:
        return jsonify({
            "error": "Contribution not found"
        }), 404

    return jsonify(dict(contribution))


@app.post("/goals/<int:goal_id>/contributions")
def create_contribution(goal_id):
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    contribution_date = data.get("contribution_date")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({
            "error": "amount must be a number"
        }), 400

    if amount <= 0:
        return jsonify({
            "error": "amount must be greater than zero"
        }), 400

    if not valid_date(contribution_date):
        return jsonify({
            "error": "contribution_date must use DD-MM-YYYY format"
        }), 400

    conn = get_db_connection()

    goal = conn.execute(
        "SELECT id FROM savings_goals WHERE id = ?",
        (goal_id,)
    ).fetchone()

    if goal is None:
        conn.close()
        return jsonify({
            "error": "Savings goal not found"
        }), 404

    cursor = conn.execute("""
        INSERT INTO contributions (
            goal_id,
            amount,
            contribution_date
        )
        VALUES (?, ?, ?)
    """, (
        goal_id,
        amount,
        contribution_date
    ))

    update_current_amount(conn, goal_id)
    conn.commit()

    new_contribution = conn.execute("""
        SELECT id, goal_id, amount, contribution_date
        FROM contributions
        WHERE id = ?
    """, (cursor.lastrowid,)).fetchone()

    conn.close()

    return jsonify(dict(new_contribution)), 201


@app.put("/contributions/<int:contribution_id>")
def update_contribution(contribution_id):
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    contribution_date = data.get("contribution_date")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({
            "error": "amount must be a number"
        }), 400

    if amount <= 0:
        return jsonify({
            "error": "amount must be greater than zero"
        }), 400

    if not valid_date(contribution_date):
        return jsonify({
            "error": "contribution_date must use DD-MM-YYYY format"
        }), 400

    conn = get_db_connection()

    contribution = conn.execute("""
        SELECT id, goal_id
        FROM contributions
        WHERE id = ?
    """, (contribution_id,)).fetchone()

    if contribution is None:
        conn.close()
        return jsonify({
            "error": "Contribution not found"
        }), 404

    goal_id = contribution["goal_id"]

    conn.execute("""
        UPDATE contributions
        SET amount = ?,
            contribution_date = ?
        WHERE id = ?
    """, (
        amount,
        contribution_date,
        contribution_id
    ))

    update_current_amount(conn, goal_id)
    conn.commit()

    updated_contribution = conn.execute("""
        SELECT id, goal_id, amount, contribution_date
        FROM contributions
        WHERE id = ?
    """, (contribution_id,)).fetchone()

    conn.close()

    return jsonify(dict(updated_contribution))


@app.delete("/contributions/<int:contribution_id>")
def delete_contribution(contribution_id):
    conn = get_db_connection()

    contribution = conn.execute("""
        SELECT id, goal_id
        FROM contributions
        WHERE id = ?
    """, (contribution_id,)).fetchone()

    if contribution is None:
        conn.close()
        return jsonify({
            "error": "Contribution not found"
        }), 404

    goal_id = contribution["goal_id"]

    conn.execute(
        "DELETE FROM contributions WHERE id = ?",
        (contribution_id,)
    )

    update_current_amount(conn, goal_id)
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Contribution deleted successfully"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=6003,
        debug=True
    )