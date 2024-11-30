import sqlite3
from typing import Dict, List, Tuple
import re

class ServiceMapper:
    def __init__(self, db_path: str = 'pharmiliar.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def find_services(self, category: str, search_term: str) -> List[Dict]:
        cursor = self.conn.cursor()
        
        # Special handling for x-ray searches
        search_term = search_term.lower().strip()
        if 'x-ray' in search_term or 'xray' in search_term:
            query = """
                SELECT 
                    description, category, code,
                    base_price, max_price
                FROM services
                WHERE category = 'RADIOLOGY'
                AND description IS NOT NULL
                AND base_price > 0
                AND (
                    LOWER(description) LIKE ?
                    OR LOWER(code) LIKE ?
                )
                ORDER BY base_price ASC
            """
            
            # Extract location if specified (e.g., "chest" from "x-ray chest")
            location = search_term.replace('x-ray', '').replace('xray', '').strip()
            if location:
                pattern = f"%{location}%"
            else:
                pattern = "%x-ray%"
                
            cursor.execute(query, (pattern, f"%xr%"))
            
        else:
            query = """
                SELECT 
                    description, category, code,
                    base_price, max_price
                FROM services
                WHERE category = ?
                AND description IS NOT NULL
                AND base_price > 0
                AND (
                    LOWER(description) LIKE ?
                    OR LOWER(code) LIKE ?
                )
                ORDER BY base_price ASC
                LIMIT 10
            """
            
            cat = "RADIOLOGY" if category == "Radiology" else "GENERAL"
            pattern = f"%{search_term}%"
            cursor.execute(query, (cat, pattern, pattern))
        
        try:
            results = cursor.fetchall()
            services = []
            for result in results:
                desc, cat, code, base_price, max_price = result
                services.append({
                    "description": desc,
                    "category": cat,
                    "code": code,
                    "base_price": base_price,
                    "max_price": max_price or base_price
                })
            return services[:10]
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def get_price_range(self, category: str, search_term: str) -> Tuple[float, float]:
        services = self.find_services(category, search_term)
        if not services:
            return 0.0, 0.0
        prices = [s["base_price"] for s in services]
        return min(prices), max(prices)

    def get_categories(self) -> List[str]:
        return ["Radiology", "General"]

    def close(self):
        if self.conn:
            self.conn.close()

def test_mapper():
    mapper = ServiceMapper()
    
    test_cases = [
        ("Radiology", "x-ray"),
        ("Radiology", "xray chest"),
        ("Radiology", "x-ray abdomen"),
        ("Radiology", "x-ray knee"),
        ("Radiology", "ultrasound"),
        ("Radiology", "ct brain"),
        ("General", "consultation"),
        ("General", "examination"),
    ]
    
    print("\nTesting X-Ray Service Mapper")
    print("=" * 50)
    
    for category, term in test_cases:
        print(f"\nSearching for '{term}' in {category}:")
        services = mapper.find_services(category, term)
        
        if services:
            min_price, max_price = mapper.get_price_range(category, term)
            print(f"Found {len(services)} services")
            print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
            
            for service in services:
                print(f"- {service['description']} ({service['code']})")
                print(f"  Price: KES {service['base_price']:.2f}")
        else:
            print("No services found")
    
    mapper.close()

if __name__ == "__main__":
    test_mapper()
