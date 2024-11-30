import sqlite3
import pandas as pd

def fix_database():
    """Fix database issues and populate with clean data."""
    print("Starting database cleanup...")
    
    # Connect to database
    conn = sqlite3.connect('pharmiliar.db')
    cursor = conn.cursor()
    
    # Load data
    df = pd.read_excel('cleaned_data.xlsx')
    
    # Reset tables
    cursor.execute('DROP TABLE IF EXISTS services')
    cursor.execute('DROP TABLE IF EXISTS hospitals')
    
    # Create tables
    cursor.execute('''
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('INSERT INTO hospitals (name) VALUES (?)', ('General Hospital',))
    
    cursor.execute('''
        CREATE TABLE services (
            id INTEGER PRIMARY KEY,
            category TEXT,
            code TEXT,
            description TEXT,
            base_price REAL,
            max_price REAL,
            hospital_id INTEGER DEFAULT 1,
            FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
        )
    ''')
    
    # Process data
    for _, row in df.iterrows():
        try:
            code = str(row[1]).strip()
            desc = str(row[2]).strip()
            base = float(str(row[3]).replace(',', ''))
            maxp = float(str(row[4]).replace(',', ''))
            
            # Determine category
            if code.upper().startswith(('XR', 'ER')):
                category = 'RADIOLOGY'
            else:
                category = 'GENERAL'
            
            cursor.execute('''
                INSERT INTO services (category, code, description, base_price, max_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (category, code, desc, base, maxp))
            
        except Exception as e:
            print(f"Error on row {_}: {e}")
    
    conn.commit()
    
    # Print stats
    cursor.execute('SELECT COUNT(*) FROM services')
    total = cursor.fetchone()[0]
    print(f"\nTotal services: {total}")
    
    cursor.execute('SELECT category, COUNT(*) FROM services GROUP BY category')
    for cat, count in cursor.fetchall():
        print(f"{cat}: {count}")
    
    conn.close()

if __name__ == "__main__":
    fix_database()
