import sqlite3

conn = sqlite3.connect('pharmiliar.db')
cursor = conn.cursor()

# Get table info
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='services';")
print("Table Schema:")
print(cursor.fetchone()[0])

# Get sample row
cursor.execute("SELECT * FROM services LIMIT 1;")
columns = [description[0] for description in cursor.description]
print("\nColumns:", columns)

conn.close()
