import sqlite3

conn = sqlite3.connect("bills.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_status BOOLEAN NOT NULL,
    due_date DATE NOT NULL
)
""")#I need to get from kevins table the type as that gives if its in mine
#then I just steam some of the info such as amount which is a bit of a yikes with the system but or well

sample_bills = [
    (True, "2026-08-01"),
    (False, "2026-09-04"),
    (True, "2026-08-01"),
    (False, "2026-09-04"),
    (True, "2026-08-01"),
    (False, "2026-09-04"),
    (True, "2026-08-01"),
    (False, "2026-09-04"),
    (True, "2026-08-01"),
    (False, "2026-10-05"),
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
INSERT INTO bills (payment_status, due_date)
VALUES (?, ?)
""", sample_bills)

conn.commit()
conn.close()

print("Database created successfully with 9 bills.")