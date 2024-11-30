import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.service_mappings = {
            # Common Medical Services with expanded terms
            "Consultation": {
                "terms": ["Consultation", "Consultancy", "Review", "Visit", "Check up"],
                "exclude": ["Blood Sugar"],
                "categories": ["1", "18", "19", "20", "CLINICS", "FILTER CLINIC", "OUT PATIENT", "CASUALTY"]
            },
            "Pain medication": {
                "terms": ["Pain", "Paracetamol", "Brufen", "Analgesic", "Diclofenac", "Ibuprofen", "Aspirin", "Tramadol",
                         "Tab", "Tablet", "Capsule", "Cap", "Syrup", "Suspension"],
                "exclude": ["Painting", "Art", "Peg"],
                "categories": ["PHARMACY 24HR -DRUGS", "ADULT PHARMACY", "INPATIENT PHARMACY", "PHARMACY", "DRUGS", 
                             "SPECIAL CLINIC PHARMACY", "CCC PHARMACY", "ONCOLOGY PHARMACY"]
            },
            "Blood tests": {
                "terms": ["Blood", "Haemoglobin", "Hb", "Complete Blood Count", "CBC", "Blood Test", "Blood Sample"],
                "exclude": ["Sugar", "Consultation"],
                "categories": ["LABORATORY GENERAL", "11", "12", "LAB", "LABORATORY"]
            },
            "Injection": {
                "terms": ["Injection", "Inj", "IM", "IV Push", "Intramuscular", "Intravenous", "Shot", 
                         "Syringe", "Needle", "Ampoule", "Amp"],
                "exclude": [],
                "categories": ["PHARMACY 24HR -DRUGS", "ADULT PHARMACY", "INPATIENT PHARMACY", "PHARMACY", 
                             "SPECIAL CLINIC PHARMACY", "CCC PHARMACY", "ONCOLOGY PHARMACY", "OUT PATIENT", "CASUALTY"]
            },
            
            # Diagnostic Services with expanded terms
            "Physical exam": {
                "terms": ["Examination", "Medical Exam", "Check up", "Physical", "Assessment"],
                "exclude": ["Employment", "School", "P3", "Gloves"],
                "categories": ["CLINICS", "OUT PATIENT", "FILTER CLINIC", "CASUALTY"]
            },
            "CT scan": {
                "terms": ["CT", "Scan", "Computed Tomography", "CAT Scan"],
                "exclude": [],
                "categories": ["XRAY"]
            },
            "MRI": {
                "terms": ["MRI", "Magnetic", "Resonance"],
                "exclude": [],
                "categories": ["XRAY"]
            },
            
            # Common Supplies with expanded terms
            "IV line": {
                "terms": ["Branula", "IV", "Cannula", "Intravenous", "Line", "Drip", "IV Set", "Giving Set"],
                "exclude": [],
                "categories": ["PHARMACY24 HR NON DRUGS", "CASUALTY", "SUPPLIES", "PROCEDURE"]
            },
            "Oxygen": {
                "terms": ["Oxygen", "O2", "Oxygen therapy"],
                "exclude": [],
                "categories": ["CASUALTY", "I.C.U", "PROCEDURE", "WARD"]
            },
            "Dressing": {
                "terms": ["Dressing", "Bandage", "Gauze", "Wound care", "Wound dressing"],
                "exclude": [],
                "categories": ["PHARMACY24 HR NON DRUGS", "CASUALTY", "107", "108", "109", "110", "PROCEDURE", "SUPPLIES"]
            },
            
            # Lab Tests with expanded terms
            "Urine test": {
                "terms": ["Urine", "Urinalysis", "UA", "Urine sample"],
                "exclude": [],
                "categories": ["LABORATORY GENERAL"]
            },
            "Blood sugar": {
                "terms": ["Sugar", "Glucose", "RBS", "FBS", "Blood sugar", "Diabetes test"],
                "exclude": ["Consultation"],
                "categories": ["LABORATORY GENERAL"]
            },
            "Liver function": {
                "terms": ["Liver", "LFT", "SGPT", "SGOT", "Liver enzymes", "ALT", "AST"],
                "exclude": [],
                "categories": ["LABORATORY GENERAL"]
            },
            
            # Wards with expanded terms
            "Ward admission": {
                "terms": ["Ward", "Admission", "Bed", "Inpatient", "Hospital stay"],
                "exclude": ["Day"],
                "categories": [
                    "WARD 1", "WARD 2", "WARD 3", "WARD 4", "WARD 5",
                    "WARD 6", "WARD 7", "WARD 8", "WARD 9", "WARD 10",
                    "INPATIENT WARD", "24", "WARD", "ADMISSION FEES"
                ]
            },
            "ICU": {
                "terms": ["ICU", "I.C.U", "Intensive", "Critical care"],
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
            like_conditions = [f"(LOWER(description) LIKE ? OR LOWER(code) LIKE ?)" for _ in mapping["terms"]]
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
                WHERE (category = ? OR category LIKE ?)
                AND description IS NOT NULL
                AND ({like_clause})
                {exclude_clause}
                AND base_price > 0
                AND base_price < 100000  -- Exclude extremely high prices
                ORDER BY base_price ASC
                LIMIT 10
            """
            
            # Build parameters list
            params = [category, f"%{category}%"]
            for term in mapping["terms"]:
                params.extend([f"%{term.lower()}%", f"%{term.lower()}%"])  # One for description, one for code
            if exclude_terms:
                params.extend([f"%{term.lower()}%" for term in exclude_terms])
            
            try:
                cursor.execute(query, params)
                results = cursor.fetchall()
                for result in results:
                    base_desc, category, desc, price, code = result
                    tier = 'K'
                    if desc and '-Nk' in desc:
                        tier = 'Nk'
                    elif desc and '-P' in desc:
                        tier = 'P'
                    
                    matches.append({
                        'base_description': base_desc,
                        'category': category,
                        'description': desc,
                        'price': price,
                        'code': code,
                        'tier': tier
                    })
            except sqlite3.Error as e:
                print(f"Error executing query for category {category}: {e}")
                continue
        
        # Remove duplicates based on description
        unique_matches = []
        seen_descriptions = set()
        for match in matches:
            if match['description'] and match['description'] not in seen_descriptions:
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
    print("=" * 50 + "\n")
    
    for term in test_terms:
        print(f"Searching for: {term}")
        matches = mapper.find_matching_services(term)
        min_price, max_price = mapper.get_service_price_range(term)
        print(f"Found {len(matches)} matches")
        print(f"Price range: KES {min_price} - {max_price}")
        
        for match in matches:
            print(f"- {match['description']} ({match['code']}) - KES {match['price']}")
        print()
