import sqlite3

conn = sqlite3.connect('pharmiliar.db')
cursor = conn.cursor()

# Get unique categories
cursor.execute("SELECT DISTINCT category FROM services;")
categories = cursor.fetchall()
print("\nAvailable Categories:")
for cat in categories:
    print(f"- {cat[0]}")

# Get sample services for each category
print("\nSample Services by Category:")
for cat in categories:
    if cat[0]:  # Skip None/NULL categories
        cursor.execute("""
            SELECT description, base_price, category 
            FROM services 
            WHERE category = ? 
            LIMIT 3
        """, (cat[0],))
        services = cursor.fetchall()
        if services:
            print(f"\nCategory: {cat[0]}")
            for service in services:
                print(f"- {service[0]} (KES {service[1]})")

conn.close()
