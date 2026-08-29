from flask import Flask, jsonify, request
import sqlite3


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
        return jsonify({"error": "payment_status required"}), 400

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

##########
#Delete
######################


#############
#CREATE
################



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)