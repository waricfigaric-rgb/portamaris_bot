import sqlite3

conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    category TEXT,
    description TEXT,
    priority TEXT,
    status TEXT DEFAULT 'open'
)
""")

conn.commit()

def create_ticket(user_id, username, category, description, priority):
    cursor.execute("""
    INSERT INTO tickets (user_id, username, category, description, priority)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, category, description, priority))
    conn.commit()
    return cursor.lastrowid

def get_open_tickets():
    cursor.execute("SELECT * FROM tickets WHERE status='open'")
    return cursor.fetchall()

def close_ticket(ticket_id):
    cursor.execute("UPDATE tickets SET status='closed' WHERE id=?", (ticket_id,))
    conn.commit()