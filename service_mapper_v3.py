import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.service_mappings = {
            # Common Medical Services
            "Consultation": ["Consultation", "Clinical Consultancy", "CLINICS", "FILTER CLINIC"],
            "Pain medication": ["Pain", "Analgesic", "PHARMACY 24HR -DRUGS"],
            "Blood tests": ["Blood Test", "Blood Transfusion", "LABORATORY GENERAL"],
            "Injection": ["Injection", "CASUALTY", "OUT PATIENT"],
            
            # Diagnostic Services
            "Physical exam": ["Physical", "Examination", "Medical Examination"],
            "CT scan": ["CT", "XRAY", "Scan"],
            "MRI": ["MRI", "XRAY", "Magnetic"],
            
            # Common Supplies
            "IV line": ["Branula", "IV", "Branulars"],
            "Oxygen": ["Oxygen Therapy", "Oxygen", "O2"],
            "Dressing": ["Dressing", "Wound Dressing", "Bandage"],
            
            # Lab Tests
            "Urine test": ["Urine Testing", "Urinalysis"],
            "Blood sugar": ["Blood Sugar", "Glucose", "Sugar"],
            "Liver function": ["Lft", "Liver Function"],
            
            # Wards
            "Ward admission": ["Ward", "Admission", "Bed Fee"],
            "ICU": ["ICU", "I.C.U", "Intensive Care"],
            
            # Categories to search in
            "categories": [
                "LABORATORY GENERAL",
                "XRAY",
                "CLINICS",
                "CASUALTY", 
                "PHARMACY 24HR -DRUGS",
                "PHARMACY24 HR NON DRUGS",
                "OUT PATIENT",
                "WARD 1",
                "WARD 2",
                "WARD 3",
                "WARD 4",
                "WARD 5",
                "I.C.U",
                "INPATIENT WARD",
                "ADMISSION FEES",
                "FILTER CLINIC"
            ]
        }

    def find_matching_services(self, medical_term: str) -> List[Dict]:
        """Find matching services for a medical term."""
        cursor = self.conn.cursor()
        matches = []
        
        # Get search terms for this medical term
        search_terms = self.service_mappings.get(medical_term, [medical_term])
        
        # First try exact category matches
        for category in search_terms:
            if category in self.service_mappings["categories"]:
                cursor.execute("""
                    SELECT DISTINCT 
                        REPLACE(REPLACE(REPLACE(description, '-K', ''), '-Nk', ''), '-P', '') as base_desc,
                        category,
                        description,
                        base_price,
                        code
                    FROM services 
                    WHERE category = ?
                    AND base_price > 0
                    LIMIT 5
                """, (category,))
                
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
        
        # Then try description matches
        for term in search_terms:
            if term not in self.service_mappings["categories"]:
                cursor.execute("""
                    SELECT DISTINCT 
                        REPLACE(REPLACE(REPLACE(description, '-K', ''), '-Nk', ''), '-P', '') as base_desc,
                        category,
                        description,
                        base_price,
                        code
                    FROM services 
                    WHERE LOWER(description) LIKE ?
                    AND base_price > 0
                    LIMIT 5
                """, (f"%{term.lower()}%",))
                
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
