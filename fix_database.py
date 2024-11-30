import sqlite3
import pandas as pd
from pathlib import Path

def fix_database():
    """Fix database issues and populate with clean data."""
    print("Starting database cleanup...")
    
    # Connect to database
    conn = sqlite3.connect('pharmiliar.db')
    cursor = conn.cursor()
    
    # Check if we have the cleaned Excel data
    if not Path('cleaned_data.xlsx').exists():
        print("Error: cleaned_data.xlsx not found!")
        return
        
    # Load cleaned data
    df = pd.read_excel('cleaned_data.xlsx')
    
    # Clean up existing tables
    cursor.execute('DROP TABLE IF EXISTS services')
    cursor.execute('DROP TABLE IF EXISTS hospitals')
    
    # Create hospitals table
    cursor.execute('''
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            type TEXT,
            last_updated DATE
        )
    ''')
    
    # Insert default hospital
    cursor.execute('''
        INSERT INTO hospitals (name, location, type)
        VALUES (?, ?, ?)
    ''', ('General Hospital', 'Nairobi', 'Public'))
    
    # Create services table
    cursor.execute('''
        CREATE TABLE services (
            id INTEGER PRIMARY KEY,
            category TEXT,
            code TEXT,
            description TEXT,
            base_price REAL,
            max_price REAL,
            rate REAL,
            reference TEXT,
            hospital_id INTEGER,
            last_updated DATE,
            FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
        )
    ''')
    
    # Clean and insert data
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO services (
                    category, code, description, 
                    base_price, max_price, hospital_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(row['category']).strip().upper(),
                str(row['code']).strip(),
                str(row['description']).strip(),
                float(row['base_price']) if pd.notna(row['base_price']) else 0.0,
                float(row['max_price']) if pd.notna(row['max_price']) else None,
                1  # Default hospital ID
            ))
        except Exception as e:
            print(f"Error inserting row: {row}")
            print(f"Error: {e}")
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_category ON services(category)')
    cursor.execute('CREATE INDEX idx_description ON services(description)')
    cursor.execute('CREATE INDEX idx_code ON services(code)')
    
    # Commit changes
    conn.commit()
    
    # Print statistics
    cursor.execute('SELECT COUNT(*) FROM services')
    total_services = cursor.fetchone()[0]
    
    cursor.execute('SELECT category, COUNT(*) FROM services GROUP BY category')
    categories = cursor.fetchall()
    
    print(f"\nDatabase cleanup complete!")
    print(f"Total services: {total_services}")
    print("\nServices by category:")
    for cat, count in categories:
        print(f"- {cat}: {count}")
    
    conn.close()

if __name__ == "__main__":
    fix_database()
