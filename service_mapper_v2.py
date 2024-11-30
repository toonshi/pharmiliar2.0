import sqlite3
from typing import Dict, List, Optional, Tuple

class ServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.service_mappings = {
            # Diagnostic Tests
            "MRI": ["Mri", "MRI Brain", "Magnetic Resonance"],
            "Blood tests": ["Blood Transfusion", "Blood Test", "Blood Transusion", "Bga", "Blood"],
            "Physical examination": ["Physical", "Medical Examination", "Clinical Consultancy"],
            "Neurological examination": ["Neurological", "Brain", "Cranial"],
            
            # Common Procedures
            "Consultation": ["Consultation", "Clinical Consultancy", "Medical Consultation"],
            "Dressing": ["Wound Dressing", "Dressing", "Bandage"],
            "Injection": ["Injection", "Inj"],
            
            # Medications and Supplies
            "Pain relievers": ["Pain", "Analgesic"],
            "IV line": ["Branula", "IV", "Branulars", "Intravenous"],
            "Oxygen therapy": ["Oxygen Therapy", "Oxygen", "O2"],
            
            # Lab Tests
            "Blood count": ["Blood Test", "Blood Transfusion", "Blood"],
            "Urine test": ["Urine Testing", "Urine Test", "Urinalysis"],
            "Liver function": ["Lft", "Liver Function", "Liver Test"],
            
            # Wards and Admissions
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
                "ADMISSION FEES"
            ]
        }

    def find_matching_services(self, medical_term: str) -> List[Dict]:
        """Find matching services for a medical term."""
        cursor = self.conn.cursor()
        matches = []
        
        # Get search terms for this medical term
        search_terms = self.service_mappings.get(medical_term, [medical_term])
        
        # Search in relevant categories
        for category in self.service_mappings["categories"]:
            for term in search_terms:
                cursor.execute("""
                    SELECT DISTINCT 
                        REPLACE(REPLACE(REPLACE(description, '-K', ''), '-Nk', ''), '-P', '') as base_desc,
                        category,
                        description,
                        base_price,
                        code
                    FROM services 
                    WHERE (LOWER(description) LIKE ? OR category = ?)
                    AND base_price > 0
                """, (f"%{term.lower()}%", category))
                
                results = cursor.fetchall()
                for result in results:
                    base_desc, category, desc, price, code = result
                    
                    # Determine tier from description
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
        
        return matches

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
        "MRI",
        "Blood tests",
        "Consultation",
        "Oxygen therapy",
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
