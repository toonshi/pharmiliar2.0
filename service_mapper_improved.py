import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self, db_path: str = 'pharmiliar.db'):
        """Initialize the service mapper with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.create_function("RELEVANCE", 2, self._calculate_relevance)
        
    def _calculate_relevance(self, description: str, search_term: str) -> int:
        """Calculate search result relevance score."""
        if not description or not search_term:
            return 0
            
        description = description.lower()
        search_term = search_term.lower()
        search_words = search_term.split()
        
        score = 0
        # Exact match
        if search_term in description:
            score += 100
            
        # All words match in order
        if all(word in description for word in search_words):
            score += 50
            
        # Individual word matches
        for word in search_words:
            if word in description:
                score += 10
                
        return score

    def find_services(self, category: str, search_term: str) -> List[Dict]:
        """Find services in a specific category matching the search term."""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                description,
                category,
                code,
                base_price,
                max_price,
                RELEVANCE(description, ?) as relevance
            FROM services
            WHERE category = ?
            AND description IS NOT NULL
            AND base_price > 0
            AND (
                LOWER(description) LIKE ? OR
                LOWER(code) LIKE ?
            )
            HAVING relevance > 0
            ORDER BY relevance DESC, base_price ASC
            LIMIT 10
        """
        
        search_pattern = f"%{search_term.lower()}%"
        
        try:
            cursor.execute(query, (
                search_term,
                "RADIOLOGY" if category == "Radiology" else "GENERAL",
                search_pattern,
                search_pattern
            ))
            results = cursor.fetchall()
            
            services = []
            for result in results:
                desc, cat, code, base_price, max_price, _ = result
                services.append({
                    "description": desc,
                    "category": cat,
                    "code": code,
                    "base_price": base_price,
                    "max_price": max_price or base_price
                })
            
            return services
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def get_price_range(self, category: str, search_term: str) -> Tuple[float, float]:
        """Get the minimum and maximum prices for matching services."""
        services = self.find_services(category, search_term)
        if not services:
            return 0.0, 0.0
        
        prices = [s["base_price"] for s in services]
        return min(prices), max(prices)

    def get_categories(self) -> List[str]:
        """Get all available service categories."""
        return ["Radiology", "General"]

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

def test_mapper():
    """Test the improved service mapper."""
    mapper = ServiceMapper()
    
    test_cases = [
        ("Radiology", "x-ray chest"),
        ("Radiology", "ultrasound"),
        ("Radiology", "ct brain"),
        ("Radiology", "mri"),
        ("General", "consultation"),
        ("General", "examination"),
    ]
    
    print("\nTesting Improved Service Mapper")
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
