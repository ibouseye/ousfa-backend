import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'site.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("--- Products ---")
    cursor.execute("SELECT id, name, stock FROM product")
    col_names = [description[0] for description in cursor.description]
    print("Column Names:", col_names)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No products found in the database.")

    print("\n--- StaffUsers ---")
    cursor.execute("SELECT id, username, role FROM staff_user")
    col_names = [description[0] for description in cursor.description]
    print("Column Names:", col_names)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No staff users found in the database.")

    print("\n--- Customers ---")
    cursor.execute("SELECT id, username, email FROM customer")
    col_names = [description[0] for description in cursor.description]
    print("Column Names:", col_names)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No customers found in the database.")

except sqlite3.Error as e:
    print(f"Database error: {e}")

finally:
    conn.close()