import sqlite3

try:
    conn = sqlite3.connect('pharmiliar.db')
    cursor = conn.cursor()
    
    # Get all distinct categories with their service counts
    print("\nAll Categories and Service Counts:")
    print("-" * 50)
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM services 
        WHERE category IS NOT NULL 
        GROUP BY category 
        ORDER BY count DESC
    """)
    categories = cursor.fetchall()
    for cat, count in categories:
        print(f"{cat}: {count} services")
        
    # Test some specific searches
    test_terms = [
        ("consultation", "Consultation services"),
        ("blood", "Blood-related services"),
        ("pain", "Pain medication"),
        ("ward", "Ward services"),
        ("laboratory", "Laboratory services"),
        ("xray", "X-ray services"),
        ("pharmacy", "Pharmacy items")
    ]
    
    for term, desc in test_terms:
        print(f"\n{desc}:")
        print("-" * 30)
        cursor.execute("""
            SELECT description, category, base_price 
            FROM services 
            WHERE LOWER(description) LIKE ? 
            AND base_price > 0
            LIMIT 5
        """, (f"%{term}%",))
        results = cursor.fetchall()
        for result in results:
            print(f"- {result[0]} ({result[1]}) - KES {result[2]}")
            
except sqlite3.Error as e:
    print(f"SQLite error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
