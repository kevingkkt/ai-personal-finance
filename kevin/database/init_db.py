import sqlite3

conn = sqlite3.connect("transactions.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT
)
""")

sample_transactions = [
    ("Income", "Salary", 3200.00, "2026-08-01", "Monthly salary"),
    ("Expense", "Food", 25.50, "2026-08-02", "Lunch"),
    ("Expense", "Transport", 18.00, "2026-08-03", "Train fare"),
    ("Expense", "Groceries", 85.40, "2026-08-04", "Weekly groceries"),
    ("Income", "Freelance", 450.00, "2026-08-05", "Freelance work"),
    ("Expense", "Entertainment", 40.00, "2026-08-06", "Movie"),
    ("Expense", "Bills", 120.00, "2026-08-07", "Electricity bill"),
    ("Expense", "Shopping", 75.00, "2026-08-08", "Clothes"),
    ("Income", "Gift", 100.00, "2026-08-09", "Birthday gift"),
    ("Expense", "Food", 32.50, "2026-08-10", "Dinner")
]

cursor.executemany("""
INSERT INTO transactions (type, category, amount, date, description)
VALUES (?, ?, ?, ?, ?)
""", sample_transactions)

conn.commit()
conn.close()

print("Database created successfully with 10 transactions.")