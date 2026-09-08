import sqlite3

conn = sqlite3.connect("bills.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_status BOOLEAN NOT NULL DEFAULT 0  CHECK (payment_status IN (0, 1)),
    due_date DATE NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    description TEXT
)
""")#I need to get from kevins table the type as that gives if its in mine
#then I just steam some of the info such as amount which is a bit of a yikes with the system but or well
#I want amount screw dealing with kevins table so I need a amount
cursor.execute("SELECT  COUNT(*) FROM bills  ")
checkingBills = cursor.fetchone()[0]

if checkingBills > 0:
    print("Database already has bills. Skipping insertion.")
    conn.close()
    exit()

sample_bills = [
    (True, "2026-08-01", 100.00, "Electricity bill"),
    (False, "2026-09-04", 150.00, "Water bill"),
    (True, "2026-08-01", 200.00, "Gas bill"),
    (False, "2026-09-04", 120.00, "Internet bill"),
    (True, "2026-08-01", 80.00, "Phone bill"),
    (False, "2026-09-04", 90.00, "Cable bill"),
    (True, "2026-08-01", 100.50, "Electricity bill"),
    (False, "2026-09-04", 150.00, "Sleep tax"),
    (True, "2026-08-01", 200.00, "dog bill"),
    (False, "2026-10-05", 120.00, "Internet bill"),
]

# leaching off kevins table here where I need to include payment status and due date mAY NEED HIS TABLE BUT FOR NOW DON'T WORRY ABOUT IT
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS  (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     type TEXT NOT NULL,
#     category TEXT NOT NULL,
#     amount REAL NOT NULL,
#     date TEXT NOT NULL,
#     description TEXT
# )
# """)

# sample_transactions = [
#     ("Income", "Salary", 3200.00, "2026-08-01", "Monthly salary"),
#     ("Expense", "Food", 25.50, "2026-08-02", "Lunch"),
#     ("Expense", "Transport", 18.00, "2026-08-03", "Train fare"),
#     ("Expense", "Groceries", 85.40, "2026-08-04", "Weekly groceries"),
#     ("Income", "Freelance", 450.00, "2026-08-05", "Freelance work"),
#     ("Expense", "Entertainment", 40.00, "2026-08-06", "Movie"),
#     ("Expense", "Bills", 120.00, "2026-08-07", "Electricity bill"),
#     ("Expense", "Shopping", 75.00, "2026-08-08", "Clothes"),
#     ("Income", "Gift", 100.00, "2026-08-09", "Birthday gift"),
#     ("Expense", "Food", 32.50, "2026-08-10", "Dinner")
# ]

cursor.executemany("""
INSERT INTO bills (payment_status, due_date, amount, description)
VALUES (?, ?, ?, ?)
""", sample_bills)

conn.commit()
conn.close()

print("Database created successfully with 9 bills.")