import sqlite3

try:
    # Try to connect to the database
    print("Attempting to connect to database...")
    conn = sqlite3.connect('pharmiliar.db')
    cursor = conn.cursor()
    
    # Check if services table exists
    print("\nChecking tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables found:", [t[0] for t in tables])
    
    if 'services' in [t[0] for t in tables]:
        # Check column names
        cursor.execute("PRAGMA table_info(services)")
        columns = cursor.fetchall()
        print("\nColumns in services table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Count rows
        cursor.execute("SELECT COUNT(*) FROM services")
        count = cursor.fetchone()[0]
        print(f"\nTotal services: {count}")
        
        # Sample some data
        print("\nSample data:")
        cursor.execute("SELECT * FROM services LIMIT 3")
        samples = cursor.fetchall()
        for sample in samples:
            print(sample)
            
        # Test a simple query
        print("\nTesting simple query:")
        cursor.execute("""
            SELECT description, category, base_price 
            FROM services 
            WHERE LOWER(description) LIKE '%consultation%'
            LIMIT 3
        """)
        results = cursor.fetchall()
        for result in results:
            print(result)
    else:
        print("Error: 'services' table not found!")
        
except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
