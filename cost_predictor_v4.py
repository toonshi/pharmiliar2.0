import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3
import json
from typing import Dict, List, Tuple, Optional

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class CostPredictor:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.cache_file = 'prediction_cache.json'
        self.load_cache()
        
    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def analyze_symptoms(self, symptoms: str) -> Dict:
        prompt = f"""You are a medical cost analysis assistant. Based on these symptoms, provide a structured analysis.
        
        Instructions:
        1. List possible conditions from most to least likely
        2. For each condition, specify required:
           - Diagnostic tests (e.g., blood tests, imaging)
           - Medications
           - Procedures
        3. Include common medical terms and alternative names
        
        Format your response EXACTLY as this JSON:
        {{
            "possible_conditions": [
                {{
                    "condition": "condition name",
                    "probability": "high/medium/low",
                    "required_services": [
                        {{
                            "name": "service name",
                            "type": "test/medication/procedure",
                            "keywords": ["keyword1", "keyword2"]
                        }}
                    ]
                }}
            ]
        }}

        Symptoms: {symptoms}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical cost analysis assistant. Provide detailed, specific medical service analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return {
                "possible_conditions": [],
                "error": str(e)
            }

    def find_matching_services(self, search_terms: List[str]) -> List[Dict]:
        matches = []
        cursor = self.conn.cursor()
        
        for term in search_terms:
            cursor.execute("""
                SELECT DISTINCT 
                    REPLACE(REPLACE(REPLACE(description, '-K', ''), '-Nk', ''), '-P', '') as base_desc,
                    category
                FROM services 
                WHERE LOWER(description) LIKE ?
                AND base_price > 0
            """, (f"%{term.lower()}%",))
            
            base_services = cursor.fetchall()
            
            for base_desc, category in base_services:
                # Get all pricing tiers for this service
                tiers = {}
                for tier in ['-K', '-Nk', '-P']:
                    cursor.execute("""
                        SELECT description, base_price, category, code
                        FROM services 
                        WHERE description LIKE ? 
                        AND base_price > 0
                        LIMIT 1
                    """, (f"{base_desc}{tier}%",))
                    
                    tier_result = cursor.fetchone()
                    if tier_result:
                        tiers[tier.strip('-')] = {
                            'description': tier_result[0],
                            'price': tier_result[1],
                            'category': tier_result[2],
                            'code': tier_result[3]
                        }
                
                if tiers:  # Only add if we found any pricing tiers
                    matches.append({
                        'base_description': base_desc,
                        'category': category,
                        'tiers': tiers
                    })
        
        return matches

    def estimate_costs(self, analysis: Dict) -> Dict:
        cost_estimates = {
            "conditions": [],
            "total_min": 0,
            "total_max": 0
        }

        for condition in analysis.get("possible_conditions", []):
            condition_estimate = {
                "condition": condition["condition"],
                "probability": condition["probability"],
                "services": []
            }
            
            condition_min = 0
            condition_max = 0

            # Process all required services for this condition
            for service in condition.get("required_services", []):
                search_terms = [service["name"]] + service.get("keywords", [])
                matches = self.find_matching_services(search_terms)
                
                for match in matches:
                    service_cost = {
                        "service": service["name"],
                        "type": service["type"],
                        "matched_service": match["base_description"],
                        "category": match["category"],
                        "pricing_tiers": {}
                    }
                    
                    # Process pricing tiers
                    tier_prices = []
                    for tier, details in match["tiers"].items():
                        service_cost["pricing_tiers"][tier] = {
                            "price": details["price"],
                            "description": details["description"]
                        }
                        tier_prices.append(details["price"])
                    
                    if tier_prices:
                        service_cost["min_cost"] = min(tier_prices)
                        service_cost["max_cost"] = max(tier_prices)
                        condition_min += service_cost["min_cost"]
                        condition_max += service_cost["max_cost"]
                    
                    condition_estimate["services"].append(service_cost)
            
            condition_estimate["min_cost"] = condition_min
            condition_estimate["max_cost"] = condition_max
            cost_estimates["conditions"].append(condition_estimate)
            
            # Update total costs based on high probability conditions
            if condition["probability"] == "high":
                cost_estimates["total_min"] += condition_min
                cost_estimates["total_max"] += condition_max

        return cost_estimates

    def get_cost_prediction(self, symptoms: str) -> Dict:
        # Check cache first
        cache_key = symptoms.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Analyze symptoms
        analysis = self.analyze_symptoms(symptoms)
        if "error" in analysis:
            return {"error": analysis["error"]}

        # Estimate costs
        cost_estimates = self.estimate_costs(analysis)

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis, cost_estimates)

        # Combine results
        prediction = {
            "analysis": analysis,
            "cost_estimates": cost_estimates,
            "recommendations": recommendations
        }

        # Cache the result
        self.cache[cache_key] = prediction
        self.save_cache()

        return prediction

    def _generate_recommendations(self, analysis: Dict, cost_estimates: Dict) -> List[str]:
        recommendations = []
        
        # Cost-based recommendations
        if cost_estimates["total_max"] > 10000:
            recommendations.append("Consider getting treatment under NHIF coverage to reduce costs")
            recommendations.append("Ask about available payment plans or financial assistance")
        
        # Service-based recommendations
        high_prob_conditions = [c for c in analysis["possible_conditions"] if c["probability"] == "high"]
        for condition in high_prob_conditions:
            service_count = len(condition.get("required_services", []))
            if service_count > 2:
                recommendations.append(f"For {condition['condition']}, discuss with your doctor if all tests can be done in phases")
        
        # Add tier-based recommendation
        recommendations.append("Prices vary by tier (K, Nk, P). Discuss with the hospital which tier applies to you")
        
        return recommendations


if __name__ == "__main__":
    predictor = CostPredictor()
    
    # Example symptoms
    symptoms = "I have been experiencing severe headache for the past 3 days, sensitivity to light, and nausea"
    
    # Get prediction
    prediction = predictor.get_cost_prediction(symptoms)
    
    # Print results in a readable format
    print("\nMedical Cost Analysis")
    print("=" * 50)
    
    print("\n1. Possible Conditions and Their Costs:")
    for condition in prediction["cost_estimates"]["conditions"]:
        print(f"\nCondition: {condition['condition']} (Probability: {condition['probability']})")
        print(f"Estimated Cost Range: KES {condition['min_cost']} - {condition['max_cost']}")
        
        if condition["services"]:
            print("\nRequired Services:")
            for service in condition["services"]:
                print(f"\n  • {service['service']} ({service['type']})")
                print(f"    Matched Service: {service['matched_service']}")
                print("    Pricing Tiers:")
                for tier, details in service["pricing_tiers"].items():
                    print(f"      - {tier}: KES {details['price']}")
    
    print(f"\nTotal Estimated Cost Range (for high probability conditions):")
    print(f"KES {prediction['cost_estimates']['total_min']} - {prediction['cost_estimates']['total_max']}")
    
    print("\nRecommendations:")
    for rec in prediction["recommendations"]:
        print(f"• {rec}")
