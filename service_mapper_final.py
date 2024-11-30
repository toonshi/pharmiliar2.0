import sqlite3
from typing import Dict, List, Tuple
import re

class ServiceMapper:
    def __init__(self, db_path: str = 'pharmiliar.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        if not text:
            return ""
        # Convert to lowercase and remove extra spaces
        text = " ".join(text.lower().split())
        # Standardize common terms
        replacements = {
            "xray": "x-ray",
            "x ray": "x-ray",
            "x-ray": "investigation x-ray",  # Match database naming
            "ultra sound": "ultrasound",
            "cat scan": "ct scan",
            "cat-scan": "ct scan",
            "mri scan": "mri",
            "magnetic resonance": "mri",
            "chest": "investigation",  # Handle chest x-rays
            "investigation investigation": "investigation"  # Clean up duplicates
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
            
    def _score_match(self, description: str, search_term: str) -> int:
        if not description or not search_term:
            return 0
            
        description = self._normalize_text(description)
        search_term = self._normalize_text(search_term)
        words = search_term.split()
        
        score = 0
        # Exact phrase match
        if search_term in description:
            score += 100
            
        # All words match in sequence
        if all(word in description for word in words):
            word_positions = [description.find(word) for word in words]
            if word_positions == sorted(word_positions):
                score += 75
            else:
                score += 50
                
        # Individual word matches at word boundaries
        for word in words:
            if word in description:
                # Higher score for matches at start of words
                if re.search(rf'\b{re.escape(word)}', description):
                    score += 20
                else:
                    score += 10
                    
        # Bonus for shorter, more precise matches
        if len(description.split()) <= len(words) + 2:
            score += 25
            
        return score

    def find_services(self, category: str, search_term: str) -> List[Dict]:
        cursor = self.conn.cursor()
        
        # Handle empty search
        if not search_term.strip():
            query = """
                SELECT 
                    description, category, code,
                    base_price, max_price
                FROM services
                WHERE category = ?
                AND description IS NOT NULL
                AND base_price > 0
                ORDER BY base_price ASC
                LIMIT 10
            """
            cat = "RADIOLOGY" if category == "Radiology" else "GENERAL"
            cursor.execute(query, (cat,))
            
        else:
            # Search with term
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
                    OR LOWER(description) LIKE ?
                    OR LOWER(description) LIKE ?
                )
            """
            
            search_term = self._normalize_text(search_term)
            words = search_term.split()
            
            # Create multiple search patterns
            patterns = [
                f"%{search_term}%",  # Full phrase
                f"%{search_term}%",  # Code match
                # Individual word matches
                f"%{' '.join(['%' + w + '%' for w in words])}%",
                # Reverse word order
                f"%{' '.join(['%' + w + '%' for w in reversed(words)])}%"
            ]
            
            cat = "RADIOLOGY" if category == "Radiology" else "GENERAL"
            cursor.execute(query, (cat, *patterns))
        
        try:
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
        ("Radiology", "xray chest"),
        ("Radiology", "ultrasound"),
        ("Radiology", "ultra sound"),
        ("Radiology", "ct brain"),
        ("Radiology", "cat scan brain"),
        ("Radiology", "mri"),
        ("Radiology", "magnetic"),
        ("General", "consultation"),
        ("General", "consult adult"),
        ("General", "examination"),
        ("General", "medical exam"),
    ]
    
    print("\nTesting Enhanced Service Mapper")
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
