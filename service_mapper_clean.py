import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self, db_path: str = 'pharmiliar.db'):
        """Initialize the service mapper with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Core service categories and their search terms
        self.service_mappings = {
            "Radiology": {
                "terms": ["X-ray", "Scan", "MRI", "CT", "Ultrasound", "Echo", "ECG"],
                "exclude": [],
                "categories": ["RADIOLOGY"]
            },
            "General": {
                "terms": ["Consultation", "Test", "Examination", "Treatment"],
                "exclude": [],
                "categories": ["GENERAL"]
            }
        }

    def find_services(self, category: str, search_term: str) -> List[Dict]:
        """Find services in a specific category matching the search term."""
        cursor = self.conn.cursor()
        
        # Get the mapping for this category
        mapping = self.service_mappings.get(category)
        if not mapping:
            return []
        
        # Build search conditions
        search_terms = [f"LOWER(description) LIKE ?" for _ in mapping["terms"]]
        search_clause = " OR ".join(search_terms)
        
        # Build category conditions
        category_terms = [f"category = ?" for _ in mapping["categories"]]
        category_clause = " OR ".join(category_terms)
        
        # Add search term to conditions
        if search_term:
            search_clause = f"({search_clause}) OR LOWER(description) LIKE ?"
        
        query = f"""
            SELECT DISTINCT
                description,
                category,
                code,
                base_price,
                max_price
            FROM services
            WHERE ({category_clause})
            AND ({search_clause})
            AND description IS NOT NULL
            AND base_price > 0
            ORDER BY base_price ASC
            LIMIT 10
        """
        
        # Build parameters list
        params = []
        params.extend(mapping["categories"])  # Category parameters
        params.extend([f"%{term.lower()}%" for term in mapping["terms"]])  # Search parameters
        if search_term:
            params.append(f"%{search_term.lower()}%")  # Additional search term
        
        try:
            cursor.execute(query, params)
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
        return list(self.service_mappings.keys())

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

def test_mapper():
    """Test the service mapper functionality."""
    mapper = ServiceMapper()
    
    print("\nTesting Service Mapper")
    print("=" * 50)
    
    # Test each category
    for category in mapper.get_categories():
        print(f"\nTesting {category} category:")
        services = mapper.find_services(category, "")
        min_price, max_price = mapper.get_price_range(category, "")
        
        print(f"Found {len(services)} services")
        print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
        
        for service in services:
            print(f"- {service['description']} ({service['code']})")
            print(f"  Category: {service['category']}")
            print(f"  Price: KES {service['base_price']:.2f}")
    
    # Test specific searches
    test_searches = [
        ("Radiology", "x-ray"),
        ("Radiology", "ultrasound"),
        ("General", "consultation"),
    ]
    
    print("\nTesting specific searches:")
    for category, term in test_searches:
        print(f"\nSearching for '{term}' in {category}:")
        services = mapper.find_services(category, term)
        for service in services:
            print(f"- {service['description']} ({service['code']})")
            print(f"  Price: KES {service['base_price']:.2f}")
    
    mapper.close()

if __name__ == "__main__":
    test_mapper()
