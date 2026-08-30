from flask import Flask, jsonify, request
import sqlite3

import requests


app = Flask(__name__)

DATABASE_NAME = "/app/data/enrolment.db"
#basic function one
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


######################################
#these are READ
#####################################
#dont change
@app.get("/")
def health():
    return jsonify({"service": "database-service", "status": "running"})

@app.get("/bills")
def get_bills():
    conn = get_db_connection()
    bills = conn.execute(
        "SELECT bill_id, payment_status, due_date, amount, description FROM bills"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in bills])

@app.get("/bills/<int:bill_id>")
def get_bill(bill_id):
    conn = get_db_connection()
    bill = conn.execute(
        "SELECT bill_id, payment_status, due_date, amount, description FROM bills WHERE bill_id = ?",
        (bill_id,),
    ).fetchone()
    conn.close()

    if bill is None:
        return jsonify({"error": "Bill not found"}), 404

    return jsonify(dict(bill))
##Get bills by if payment is true or false
@app.get("/bills/by-status")
def get_bills_by_status():
    payment_status = request.args.get("payment_status")

    if not payment_status:
        return jsonify({"error": "There was no payment_status required"}), 400

    conn = get_db_connection()
    bills = conn.execute(
        "SELECT bill_id, payment_status, due_date, amount, description FROM bills WHERE payment_status = ?",
        (payment_status,),
    ).fetchall()
    conn.close()

    if not bills:
        return jsonify({"error": "No bills found"}), 404

    return jsonify([dict(row) for row in bills])

######################################
#These are UPDATE
#################################
#update a bills payment status 
@app.route("/bills/<int:bill_id>", methods=["PUT"])
def update_bill_status(bill_id):
    try:
        response = requests.put(
            f"{DATABASE_API_URL}/bills/{bill_id}",
            json=request.get_json(),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Sorry could not connect to database service"
        }), 500

##########
#Delete
######################
#delete a bill by id although we see if i actually add in functionality to delete a bill by id later
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
            "error": "Sorry, it was unable to database service"
        }), 500

#############
#CREATE
################
#I want to create a new bill
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
            "error": "Sorry, it was unable to connect to the database service"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)