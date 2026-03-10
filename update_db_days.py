# update_db_days.py
import sqlite3
from datetime import datetime

def update_database():
    """Add day open/close and back date posting tables"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    
    # Business Days table
    c.execute('''CREATE TABLE IF NOT EXISTS business_days
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  day_date TEXT UNIQUE,
                  opened_by TEXT,
                  opened_at TEXT,
                  closed_by TEXT,
                  closed_at TEXT,
                  status TEXT DEFAULT 'Open',
                  opening_cash REAL DEFAULT 0,
                  closing_cash REAL DEFAULT 0,
                  notes TEXT)''')
    
    # Back Date Posting Log
    c.execute('''CREATE TABLE IF NOT EXISTS back_date_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  transaction_date TEXT,
                  posted_date TEXT,
                  transaction_type TEXT,
                  transaction_id INTEGER,
                  posted_by TEXT,
                  reason TEXT)''')
    
    # Add current day as open if none exists
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM business_days WHERE day_date=?", (today,))
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO business_days (day_date, opened_by, opened_at, status, opening_cash)
                    VALUES (?,?,?,?,?)''',
                  (today, 'System', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Open', 0))
    
    conn.commit()
    conn.close()
    print("✅ Day Open/Close tables added successfully!")

if __name__ == "__main__":
    response = input("This will add day open/close tables. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        update_database()
    else:
        print("Update cancelled.")