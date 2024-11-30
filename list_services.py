import sqlite3

def print_services_by_category():
    conn = sqlite3.connect('pharmiliar.db')
    cursor = conn.cursor()
    
    # Get all unique categories
    cursor.execute("""
        SELECT DISTINCT category 
        FROM services 
        WHERE category IS NOT NULL 
        ORDER BY category
    """)
    categories = cursor.fetchall()
    
    for category in categories:
        cat = category[0]
        print(f"\nCategory: {cat}")
        
        # Get services for this category
        cursor.execute("""
            SELECT description, base_price, code
            FROM services 
            WHERE category = ? 
            AND base_price > 0
            ORDER BY description
        """, (cat,))
        
        services = cursor.fetchall()
        for service in services:
            desc, price, code = service
            print(f"- {desc} (KES {price})")
    
    conn.close()

if __name__ == "__main__":
    print("\nAvailable Medical Services:")
    print("=" * 50)
    print_services_by_category()
