import sqlite3

def check_database():
    print("\nChecking Database Connection...")
    print("-" * 50)
    
    try:
        conn = sqlite3.connect('pharmiliar.db')
        cursor = conn.cursor()
        
        # Check if services table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
        if not cursor.fetchone():
            print("Error: 'services' table not found!")
            return
            
        # Get total count of services
        cursor.execute("SELECT COUNT(*) FROM services")
        total = cursor.fetchone()[0]
        print(f"Total services in database: {total}")
        
        # Get distinct categories
        cursor.execute("SELECT DISTINCT category FROM services")
        categories = cursor.fetchall()
        print("\nAvailable categories:")
        for cat in categories:
            cursor.execute("SELECT COUNT(*) FROM services WHERE category = ?", (cat[0],))
            count = cursor.fetchone()[0]
            print(f"- {cat[0]}: {count} services")
            
        # Sample some services
        print("\nSample services:")
        cursor.execute("SELECT description, category, base_price FROM services LIMIT 5")
        samples = cursor.fetchall()
        for sample in samples:
            print(f"- {sample[0]} ({sample[1]}) - KES {sample[2]}")
            
        # Test specific queries
        test_queries = [
            ("Consultation", "CLINICS"),
            ("Blood", "LABORATORY GENERAL"),
            ("Pain", "PHARMACY 24HR -DRUGS")
        ]
        
        print("\nTesting specific queries:")
        for term, category in test_queries:
            query = """
                SELECT description, category, base_price 
                FROM services 
                WHERE category = ? 
                AND LOWER(description) LIKE ?
                AND base_price > 0
                LIMIT 3
            """
            cursor.execute(query, (category, f"%{term.lower()}%"))
            results = cursor.fetchall()
            print(f"\nSearching for '{term}' in '{category}':")
            if results:
                for result in results:
                    print(f"- {result[0]} ({result[1]}) - KES {result[2]}")
            else:
                print("No matches found")
                
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
