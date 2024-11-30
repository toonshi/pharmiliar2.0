import os
from typing import Dict, List, Optional
from dotenv import load_load_dotenv
import openai
from service_mapper_clean import ServiceMapper

class CostPredictor:
    def __init__(self):
        """Initialize the cost predictor with OpenAI and service mapper."""
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.service_mapper = ServiceMapper()
        
        # Symptom to service category mappings
        self.symptom_categories = {
            "pain": ["Consultation", "Laboratory", "Pharmacy"],
            "fever": ["Consultation", "Laboratory", "Pharmacy"],
            "injury": ["Consultation", "Radiology", "Pharmacy"],
            "cough": ["Consultation", "Laboratory", "Pharmacy"],
            "headache": ["Consultation", "Laboratory", "Pharmacy"],
            "stomach": ["Consultation", "Laboratory", "Pharmacy"],
            "breathing": ["Consultation", "Laboratory", "Radiology"],
            "chest": ["Consultation", "Laboratory", "Radiology"],
            "fracture": ["Consultation", "Radiology", "Ward"],
            "surgery": ["Consultation", "Laboratory", "Ward"],
        }

    def analyze_symptoms(self, symptoms: str) -> List[Dict]:
        """Use GPT to analyze symptoms and suggest relevant services."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
                    You are a medical cost estimation assistant. Based on the symptoms provided,
                    suggest relevant medical services that might be needed. Focus on these categories:
                    - Consultation
                    - Laboratory tests
                    - Radiology (imaging)
                    - Pharmacy (medications)
                    - Ward (hospitalization)
                    
                    Format your response as a list of services, one per line:
                    category: specific service
                    """},
                    {"role": "user", "content": f"Symptoms: {symptoms}"}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            suggested_services = response.choices[0].message.content.strip().split("\n")
            return [self._parse_service(s) for s in suggested_services if s]
            
        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return []

    def _parse_service(self, service_line: str) -> Dict:
        """Parse a service line from GPT response into category and description."""
        try:
            category, description = service_line.split(":", 1)
            return {
                "category": category.strip(),
                "description": description.strip()
            }
        except:
            return {"category": "", "description": service_line.strip()}

    def estimate_costs(self, symptoms: str) -> Dict:
        """Estimate costs based on symptoms."""
        services = self.analyze_symptoms(symptoms)
        
        estimates = {
            "services": [],
            "total_min": 0.0,
            "total_max": 0.0
        }
        
        for service in services:
            category = service["category"]
            description = service["description"]
            
            # Find matching services and their price ranges
            matches = self.service_mapper.find_services(category, description)
            min_price, max_price = self.service_mapper.get_price_range(category, description)
            
            if matches:
                estimates["services"].append({
                    "category": category,
                    "description": description,
                    "matches": matches,
                    "min_price": min_price,
                    "max_price": max_price
                })
                
                estimates["total_min"] += min_price
                estimates["total_max"] += max_price
        
        return estimates

    def close(self):
        """Clean up resources."""
        self.service_mapper.close()

def test_predictor():
    """Test the cost predictor functionality."""
    predictor = CostPredictor()
    
    test_cases = [
        "I have a severe headache and fever for 2 days",
        "I fell and hurt my arm, it might be broken",
        "I have been coughing for a week with chest pain"
    ]
    
    print("\nTesting Cost Predictor")
    print("=" * 50)
    
    for symptoms in test_cases:
        print(f"\nSymptoms: {symptoms}")
        estimates = predictor.estimate_costs(symptoms)
        
        print(f"\nEstimated cost range: KES {estimates['total_min']:.2f} - {estimates['total_max']:.2f}")
        print("\nSuggested services:")
        
        for service in estimates["services"]:
            print(f"\n{service['category']}: {service['description']}")
            print(f"Price range: KES {service['min_price']:.2f} - {service['max_price']:.2f}")
            print("Matching services:")
            for match in service["matches"]:
                print(f"- {match['description']}")
                print(f"  Price: KES {match['base_price']:.2f}")
    
    predictor.close()

if __name__ == "__main__":
    test_predictor()
