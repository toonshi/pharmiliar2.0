"""
Database Setup Module

Creates and populates SQLite database for hospital services:
- Creates tables and indexes
- Migrates cleaned data
- Sets up ChromaDB for AI features
"""

import sqlite3
from pathlib import Path
import pandas as pd
import logging
from typing import Dict
import chromadb
from datetime import datetime

class DatabaseSetup:
    def __init__(self, config: Dict):
        self.config = config['database']
        self.logger = logging.getLogger(__name__)
        
    def create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        conn.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            gl_account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY,
            department_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            description TEXT NOT NULL,
            normal_rate REAL,
            special_rate REAL,
            non_ea_rate REAL,
            gl_account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY,
            service_id INTEGER NOT NULL,
            normal_rate REAL,
            special_rate REAL,
            non_ea_rate REAL,
            effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id)
        )''')
        
    def create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes"""
        for index in self.config['indexes']:
            table, column = index.split('.')
            index_name = f"idx_{table}_{column}"
            conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})")
            
    def setup_chromadb(self, data_dir: Path):
        """Setup ChromaDB for service descriptions"""
        chroma_client = chromadb.Client()
        collection = chroma_client.create_collection(
            name="medical_services",
            metadata={"description": "Medical service descriptions for semantic search"}
        )
        return collection
        
    def setup(self, db_path: Path, df: pd.DataFrame) -> bool:
        """Setup complete database"""
        self.logger.info(f"Setting up database at: {db_path}")
        
        try:
            # Create SQLite database
            conn = sqlite3.connect(db_path)
            
            # Create tables and indexes
            self.create_tables(conn)
            self.create_indexes(conn)
            
            # Setup ChromaDB
            collection = self.setup_chromadb(db_path.parent)
            
            # Migrate data
            self.migrate_data(conn, df, collection)
            
            conn.close()
            self.logger.info("Database setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {str(e)}")
            return False
            
    def migrate_data(self, conn: sqlite3.Connection, df: pd.DataFrame, collection):
        """Migrate cleaned data to database"""
        # First, insert departments
        departments = df['department'].unique()
        for dept in departments:
            conn.execute(
                "INSERT OR IGNORE INTO departments (name) VALUES (?)",
                (dept,)
            )
            
        # Get department IDs
        dept_ids = {
            row[0]: row[1] for row in 
            conn.execute("SELECT name, id FROM departments").fetchall()
        }
        
        # Insert services
        for _, row in df.iterrows():
            cursor = conn.execute(
                """
                INSERT INTO services 
                (department_id, code, description, normal_rate, special_rate, non_ea_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    dept_ids[row['department']],
                    row['code'],
                    row['description'],
                    row['normal_rate'],
                    row['special_rate'],
                    row['non_ea_rate']
                )
            )
            
            # Add to ChromaDB for semantic search
            collection.add(
                documents=[row['description']],
                metadatas=[{
                    'code': row['code'],
                    'department': row['department'],
                    'normal_rate': str(row['normal_rate'])
                }],
                ids=[str(cursor.lastrowid)]
            )
            
        conn.commit()
