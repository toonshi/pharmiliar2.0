import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.service_mappings = {
            # Common Medical Services with exact terms to match
            "Consultation": {
                "terms": ["Consultation", "Consultancy", "Clinical"],
                "exclude": ["Blood Sugar", "Dental"],
                "categories": ["CLINICS", "FILTER CLINIC", "OUT PATIENT"]
            },
            "Pain medication": {
                "terms": ["Paracetamol", "Brufen", "Pain", "Analgesic", "Painkiller"],
                "exclude": ["Painting", "Art", "Peg"],
                "categories": ["PHARMACY 24HR -DRUGS"]
            },
            "Blood tests": {
                "terms": ["Blood", "Haemoglobin", "Hb", "Complete Blood Count", "CBC"],
                "exclude": ["Sugar", "Consultation", "Back", "Slab"],
                "categories": ["LABORATORY GENERAL"]
            },
            "Injection": {
                "terms": ["Injection", "Inj"],
                "exclude": [],
                "categories": ["PHARMACY 24HR -DRUGS", "OUT PATIENT"]
            },
            
            # Diagnostic Services
            "Physical exam": {
                "terms": ["Examination", "Medical Exam", "Check up"],
                "exclude": ["Employment", "School", "P3", "Gloves"],
                "categories": ["CLINICS", "OUT PATIENT"]
            },
            "CT scan": {
                "terms": ["CT", "Scan"],
                "exclude": [],
                "categories": ["XRAY"]
            },
            "MRI": {
                "terms": ["MRI", "Magnetic"],
                "exclude": [],
                "categories": ["XRAY"]
            },
            
            # Common Supplies
            "IV line": {
                "terms": ["Branula", "IV", "Cannula", "Intravenous"],
                "exclude": [],
                "categories": ["PHARMACY24 HR NON DRUGS"]
            },
            "Oxygen": {
                "terms": ["Oxygen", "O2"],
                "exclude": [],
                "categories": ["CASUALTY", "I.C.U"]
            },
            "Dressing": {
                "terms": ["Dressing", "Bandage", "Gauze"],
                "exclude": [],
                "categories": ["PHARMACY24 HR NON DRUGS", "CASUALTY"]
            },
            
            # Lab Tests
            "Urine test": {
                "terms": ["Urine", "Urinalysis"],
                "exclude": [],
                "categories": ["LABORATORY GENERAL"]
            },
            "Blood sugar": {
                "terms": ["Sugar", "Glucose", "RBS"],
                "exclude": ["Consultation"],
                "categories": ["LABORATORY GENERAL"]
            },
            "Liver function": {
                "terms": ["Liver", "LFT", "SGPT", "SGOT"],
                "exclude": [],
                "categories": ["LABORATORY GENERAL"]
            },
            
            # Wards
            "Ward admission": {
                "terms": ["Ward", "Admission", "Bed"],
                "exclude": ["Day"],
                "categories": ["WARD 1", "WARD 2", "WARD 3", "WARD 4", "WARD 5", "INPATIENT WARD"]
            },
            "ICU": {
                "terms": ["ICU", "I.C.U", "Intensive"],
                "exclude": [],
                "categories": ["I.C.U"]
            }
        }

    def find_matching_services(self, medical_term: str) -> List[Dict]:
        """Find matching services for a medical term with improved filtering."""
        cursor = self.conn.cursor()
        matches = []
        
        # Get mapping for this medical term
        mapping = self.service_mappings.get(medical_term)
        if not mapping:
            return []
            
        # Search in specified categories first
        for category in mapping["categories"]:
            # Build the LIKE conditions for search terms
            like_conditions = [f"LOWER(description) LIKE ?" for _ in mapping["terms"]]
            like_clause = " OR ".join(like_conditions)
            
            # Build the exclude conditions if any
            exclude_clause = ""
            exclude_terms = mapping.get("exclude", [])
            if exclude_terms:
                exclude_conditions = [f"LOWER(description) NOT LIKE ?" for _ in exclude_terms]
                exclude_clause = f"AND {' AND '.join(exclude_conditions)}"
            
            query = f"""
                SELECT DISTINCT 
                    REPLACE(REPLACE(REPLACE(description, '-K', ''), '-Nk', ''), '-P', '') as base_desc,
                    category,
                    description,
                    base_price,
                    code
                FROM services 
                WHERE category = ?
                AND ({like_clause})
                {exclude_clause}
                AND base_price > 0
                AND base_price < 100000  -- Exclude extremely high prices
                ORDER BY base_price ASC
                LIMIT 5
            """
            
            # Build parameters list
            params = [category]
            params.extend([f"%{term.lower()}%" for term in mapping["terms"]])
            if exclude_terms:
                params.extend([f"%{term.lower()}%" for term in exclude_terms])
            
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            for result in results:
                base_desc, category, desc, price, code = result
                tier = 'K'
                if '-Nk' in desc:
                    tier = 'Nk'
                elif '-P' in desc:
                    tier = 'P'
                
                matches.append({
                    'base_description': base_desc,
                    'category': category,
                    'description': desc,
                    'price': price,
                    'code': code,
                    'tier': tier
                })
        
        # Remove duplicates based on description
        unique_matches = []
        seen_descriptions = set()
        for match in matches:
            if match['description'] not in seen_descriptions:
                unique_matches.append(match)
                seen_descriptions.add(match['description'])
        
        return unique_matches

    def get_service_price_range(self, medical_term: str) -> Tuple[float, float]:
        """Get min and max prices for a medical term across all tiers."""
        matches = self.find_matching_services(medical_term)
        if not matches:
            return 0.0, 0.0
        
        prices = [match['price'] for match in matches]
        return min(prices), max(prices)

    def get_service_by_tier(self, medical_term: str, tier: str) -> Optional[Dict]:
        """Get service details for a specific tier (K, Nk, or P)."""
        matches = self.find_matching_services(medical_term)
        for match in matches:
            if match['tier'] == tier:
                return match
        return None

if __name__ == "__main__":
    # Test the mapper
    mapper = ServiceMapper()
    test_terms = [
        "Consultation",
        "Blood tests",
        "Pain medication",
        "Injection",
        "Ward admission"
    ]
    
    print("\nTesting Service Mapper:")
    print("=" * 50)
    
    for term in test_terms:
        print(f"\nSearching for: {term}")
        matches = mapper.find_matching_services(term)
        min_price, max_price = mapper.get_service_price_range(term)
        
        print(f"Found {len(matches)} matches")
        print(f"Price range: KES {min_price} - {max_price}")
        
        for match in matches:
            print(f"- {match['description']} ({match['category']}) - KES {match['price']}")
