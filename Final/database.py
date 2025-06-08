import sqlite3

DB_NAME = "expenses.db"

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(date, category, amount, type_):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, category, amount, type) VALUES (?, ?, ?, ?)",
              (date, category, amount, type_))
    conn.commit()
    conn.close()

def get_all_transactions(month=None, year=None, category=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = "SELECT id, date, category, amount, type FROM transactions WHERE 1=1"
    params = []

    if month and month != "All":
        query += " AND strftime('%m', date) = ?"
        params.append(month)
    if year and year != "All":
        query += " AND strftime('%Y', date) = ?"
        params.append(year)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY date DESC"

    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results



def delete_transaction(transaction_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()

def get_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT type, SUM(amount) FROM transactions GROUP BY type
    """)
    summary = c.fetchall()
    conn.close()
    return summary

def get_monthly_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE date IS NOT NULL AND date != ''
        GROUP BY month
        HAVING month IS NOT NULL AND month != ''
        ORDER BY month
    """)
    data = c.fetchall()
    conn.close()
    return [(m, i or 0, e or 0) for m, i, e in data]
