import sqlite3

db_path = 'site.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(table[0])
    conn.close()
except sqlite3.Error as e:
    print(f"Error connecting to or querying database: {e}")
