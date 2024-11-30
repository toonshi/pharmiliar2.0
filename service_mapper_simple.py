import sqlite3
from typing import Dict, List, Tuple

class ServiceMapper:
    def __init__(self, db_path: str = 'pharmiliar.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def _score_match(self, description: str, search_term: str) -> int:
        if not description or not search_term:
            return 0
            
        description = description.lower()
        search_term = search_term.lower()
        words = search_term.split()
        
        score = 0
        if search_term in description:
            score += 100
        if all(word in description for word in words):
            score += 50
        for word in words:
            if word in description:
                score += 10
        return score

    def find_services(self, category: str, search_term: str) -> List[Dict]:
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                description,
                category,
                code,
                base_price,
                max_price
            FROM services
            WHERE category = ?
            AND description IS NOT NULL
            AND base_price > 0
            AND (
                LOWER(description) LIKE ?
                OR LOWER(code) LIKE ?
            )
        """
        
        search_pattern = f"%{search_term.lower()}%"
        cat = "RADIOLOGY" if category == "Radiology" else "GENERAL"
        
        try:
            cursor.execute(query, (cat, search_pattern, search_pattern))
            results = cursor.fetchall()
            
            # Score and sort results
            scored_results = []
            for result in results:
                desc, cat, code, base_price, max_price = result
                score = self._score_match(desc, search_term)
                if score > 0:
                    scored_results.append((score, {
                        "description": desc,
                        "category": cat,
                        "code": code,
                        "base_price": base_price,
                        "max_price": max_price or base_price
                    }))
            
            # Sort by score and return top 10
            scored_results.sort(key=lambda x: (-x[0], x[1]["base_price"]))
            return [item[1] for item in scored_results[:10]]
            
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
        ("Radiology", "x-ray chest"),
        ("Radiology", "ultrasound"),
        ("Radiology", "ct brain"),
        ("Radiology", "mri"),
        ("General", "consultation"),
        ("General", "examination"),
    ]
    
    print("\nTesting Simple Service Mapper")
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
