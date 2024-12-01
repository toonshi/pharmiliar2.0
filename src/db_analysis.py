"""Analyze and compare database contents."""

from sqlalchemy import create_engine, inspect, MetaData
import pandas as pd
import os
import chromadb
import json

def analyze_databases():
    """Analyze both databases and print comparison."""
    
    # Connect to hospital_services database
    hospital_db = create_engine('sqlite:///../data/processed/hospital_services.db')
    inspector = inspect(hospital_db)
    
    print("=== Hospital Services Database ===")
    print("\nTables:")
    tables = inspector.get_table_names()
    print(tables)
    
    # Get sample data from services
    try:
        with hospital_db.connect() as conn:
            metadata = MetaData()
            metadata.reflect(bind=hospital_db)
            
            if 'services' in tables and 'departments' in tables:
                services = pd.read_sql_table('services', conn)
                departments = pd.read_sql_table('departments', conn)
                
                print(f"\nTotal Services: {len(services)}")
                print(f"Total Departments: {len(departments)}")
                
                print("\nDepartments:")
                print(departments['name'].unique())
                
                print("\nSample Services (first 5):")
                print(services.head().to_string())
                
                # Analyze price distributions
                print("\nPrice Statistics:")
                price_stats = services[['normal_rate', 'special_rate', 'non_ea_rate']].describe()
                print(price_stats.to_string())
                
                # Check for missing or zero values
                print("\nMissing Values:")
                print(services.isnull().sum().to_string())
                
                print("\nZero Prices:")
                zero_prices = {
                    'normal_rate': len(services[services['normal_rate'] == 0]),
                    'special_rate': len(services[services['special_rate'] == 0]),
                    'non_ea_rate': len(services[services['non_ea_rate'] == 0])
                }
                print(json.dumps(zero_prices, indent=2))
                
                # Analyze price relationships
                services['special_ratio'] = services['special_rate'] / services['normal_rate']
                services['non_ea_ratio'] = services['non_ea_rate'] / services['normal_rate']
                
                print("\nPrice Ratio Statistics:")
                ratio_stats = services[['special_ratio', 'non_ea_ratio']].describe()
                print(ratio_stats.to_string())
            else:
                print("Required tables not found in hospital_services.db")
    except Exception as e:
        print(f"Error analyzing hospital_services.db: {str(e)}")
    
    # Connect to pharmiliar database
    print("\n=== Pharmiliar Database ===")
    pharmiliar_db = create_engine('sqlite:///../pharmiliar.db')
    inspector = inspect(pharmiliar_db)
    
    print("\nTables:")
    print(inspector.get_table_names())
    
    # Analyze ChromaDB
    print("\nAnalyzing ChromaDB...")
    chroma_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
    if os.path.exists(chroma_dir):
        try:
            client = chromadb.PersistentClient(path=chroma_dir)
            collections = client.list_collections()
            print(f"\nFound {len(collections)} collections:")
            for collection in collections:
                print(f"\nCollection: {collection.name}")
                print(f"Count: {collection.count()}")
        except Exception as e:
            print(f"Error accessing ChromaDB: {str(e)}")
    else:
        print("ChromaDB directory not found")

if __name__ == "__main__":
    analyze_databases()
