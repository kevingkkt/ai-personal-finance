import sqlite3
import os

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "savings_goals.db")
)

database_directory = os.path.dirname(DB_PATH)

if database_directory:
    os.makedirs(database_directory, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS savings_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL NOT NULL,
    target_date DATE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    contribution_date DATE NOT NULL,
    FOREIGN KEY (goal_id) REFERENCES savings_goals(id)
)
""")

sample_goals = [
    ("Emergency fund", 10000.00, 850.00, "31-08-2027"),
    ("New laptop", 2500.00, 550.00, "15-12-2026"),
    ("Japan holiday", 6000.00, 1000.00, "01-04-2027"),
    ("Car deposit", 12000.00, 1250.00, "31-12-2027"),
    ("Course fees", 3000.00, 600.00, "01-02-2027"),
    ("Home office upgrade", 1800.00, 200.00, "30-11-2026"),
    ("Dental treatment", 2200.00, 220.00, "31-01-2027"),
    ("Moving costs", 4500.00, 450.00, "30-06-2027"),
    ("Professional course", 1500.00, 150.00, "31-12-2026"),
    ("Long-term investment", 8000.00, 800.00, "01-01-2028")
]

cursor.executemany("""
INSERT INTO savings_goals (
    goal_name,
    target_amount,
    current_amount,
    target_date
)
VALUES (?, ?, ?, ?)
""", sample_goals)

sample_contributions = [
    (1, 850.00, "05-08-2026"),
    (2, 550.00, "12-08-2026"),
    (3, 1000.00, "20-08-2026"),
    (4, 1250.00, "25-08-2026"),
    (5, 600.00, "10-08-2026"),
    (6, 200.00, "01-08-2026"),
    (7, 220.00, "03-08-2026"),
    (8, 450.00, "08-08-2026"),
    (9, 150.00, "15-08-2026"),
    (10, 800.00, "18-08-2026")
]

cursor.executemany("""
INSERT INTO contributions (
    goal_id,
    amount,
    contribution_date
)
VALUES (?, ?, ?)
""", sample_contributions)

conn.commit()
conn.close()

print("Database created successfully with 10 savings goals and 10 contributions.")