import sqlite3

conn = sqlite3.connect("budgets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT
)
""")

sample_budgets = [
    ("Grocery Budget", 600.00, "2026-08-01", "2026-08-31", "August grocery budget"),
    ("Entertainment Budget", 200.00, "2026-08-01", "2026-08-31", "August entertainment budget"),
    ("Travel Budget", 1500.00, "2026-08-01", "2026-08-31", "August travel budget"),
    ("Utilities Budget", 300.00, "2026-08-01", "2026-08-31", "August utilities budget"),
    ("Dining Out Budget", 250.00, "2026-08-01", "2026-08-31", "August dining out budget"),
    ("Fitness Budget", 100.00, "2026-08-01", "2026-08-31", "August fitness budget"),
    ("Education Budget", 400.00, "2026-08-01", "2026-08-31", "August education budget"),
    ("Healthcare Budget", 350.00, "2026-08-01", "2026-08-31", "August healthcare budget"),
    ("Clothing Budget", 150.00, "2026-08-01", "2026-08-31", "August clothing budget"),
    ("Miscellaneous Budget", 100.00, "2026-08-01", "2026-08-31", "August miscellaneous budget")        
]

cursor.executemany("""
INSERT INTO budgets (name, amount, start_date, end_date, description)
VALUES (?, ?, ?, ?, ?)
""", sample_budgets)

conn.commit()
conn.close()

print("Database created successfully with 10 budgets.")