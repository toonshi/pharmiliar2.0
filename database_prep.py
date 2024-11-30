import pandas as pd
import sqlite3
from datetime import datetime

# Read the cleaned data
df = pd.read_excel("cleaned_data.xlsx")

# Rename columns to meaningful names
df.columns = ['Category', 'Code', 'Description', 'Price1', 'Price2', 'Rate', 'Reference']

# Clean and prepare data for database
def prepare_data(df):
    # Convert prices to numeric, handling any currency symbols and commas
    df['Price1'] = pd.to_numeric(df['Price1'].str.replace('KES', '').str.replace(',', ''), errors='coerce')
    df['Price2'] = pd.to_numeric(df['Price2'].str.replace('KES', '').str.replace(',', ''), errors='coerce')
    
    # Add metadata
    df['hospital_name'] = 'CPGH'  # Replace with actual hospital name
    df['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    return df

# Create SQLite database
def create_database():
    conn = sqlite3.connect('pharmiliar.db')
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            contact TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
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
    
    return conn

# Insert data into database
def insert_data(df, conn):
    # Insert hospital
    conn.execute("INSERT INTO hospitals (name) VALUES (?)", ('CPGH',))
    hospital_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Prepare services data
    services_data = df.apply(lambda row: (
        row['Category'],
        row['Code'],
        row['Description'],
        row['Price1'],
        row['Price2'],
        row['Rate'],
        row['Reference'],
        hospital_id,
        row['last_updated']
    ), axis=1).tolist()
    
    # Insert services
    conn.executemany('''
        INSERT INTO services (
            category, code, description, base_price, max_price,
            rate, reference, hospital_id, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', services_data)
    
    conn.commit()

if __name__ == "__main__":
    # Prepare the data
    print("Preparing data...")
    prepared_df = prepare_data(df)
    
    # Create and populate database
    print("Creating database...")
    conn = create_database()
    
    print("Inserting data...")
    insert_data(prepared_df, conn)
    
    print("Database created successfully!")
    conn.close()
