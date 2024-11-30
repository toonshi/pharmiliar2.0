import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from typing import Dict, List
from service_mapper_v2 import ServiceMapper

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class CostPredictor:
    def __init__(self):
        self.cache_file = 'prediction_cache.json'
        self.service_mapper = ServiceMapper()
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
        4. Use simple, common terms for services that a hospital would recognize
        
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

    def estimate_costs(self, analysis: Dict) -> Dict:
        cost_estimates = {
            "conditions": [],
            "total_min": 0,
            "total_max": 0
        }

        # Process each condition
        for condition in analysis["possible_conditions"]:
            condition_estimate = {
                "condition": condition["condition"],
                "probability": condition["probability"],
                "services": [],
                "min_cost": 0,
                "max_cost": 0
            }
            
            # Process each required service
            for service in condition["required_services"]:
                # Try each keyword for the service
                all_keywords = [service["name"]] + service["keywords"]
                matches = []
                
                for keyword in all_keywords:
                    keyword_matches = self.service_mapper.find_matching_services(keyword)
                    if keyword_matches:
                        matches.extend(keyword_matches)
                
                # Remove duplicates based on description
                unique_matches = []
                seen_descriptions = set()
                for match in matches:
                    if match['description'] not in seen_descriptions:
                        unique_matches.append(match)
                        seen_descriptions.add(match['description'])
                
                if unique_matches:
                    prices = [match['price'] for match in unique_matches]
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    service_details = {
                        "service": service["name"],
                        "type": service["type"],
                        "matches": unique_matches,
                        "min_cost": min_price,
                        "max_cost": max_price
                    }
                    
                    condition_estimate["services"].append(service_details)
                    condition_estimate["min_cost"] += min_price
                    condition_estimate["max_cost"] += max_price
            
            cost_estimates["conditions"].append(condition_estimate)
            
            # Add to total if high probability
            if condition["probability"] == "high":
                cost_estimates["total_min"] += condition_estimate["min_cost"]
                cost_estimates["total_max"] += condition_estimate["max_cost"]

        return cost_estimates

    def get_cost_prediction(self, symptoms: str) -> Dict:
        # Check cache first
        cache_key = symptoms.lower().strip()
        if cache_key in self.cache:
            print("DEBUG - Found in cache")
            return self.cache[cache_key]

        print("DEBUG - Starting prediction for symptoms:", symptoms)

        # Analyze symptoms
        analysis = self.analyze_symptoms(symptoms)
        if "error" in analysis:
            return {"error": analysis["error"]}

        print("DEBUG - GPT Analysis:")
        print(json.dumps(analysis, indent=2))

        # Estimate costs
        print("DEBUG - Starting cost estimation")
        print("Analysis input:", json.dumps(analysis, indent=2))
        cost_estimates = self.estimate_costs(analysis)
        print("DEBUG - Final cost estimates:", json.dumps(cost_estimates, indent=2))

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis, cost_estimates)

        # Combine results
        prediction = {
            "analysis": analysis,
            "cost_estimates": cost_estimates,
            "recommendations": recommendations
        }

        print("DEBUG - Final prediction:", json.dumps(prediction, indent=2))

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
    
    if "error" in prediction:
        print("\nError:", prediction["error"])
    else:
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
                    print(f"    Cost Range: KES {service['min_cost']} - {service['max_cost']}")
                    print("    Available Services:")
                    for match in service["matches"]:
                        print(f"      - {match['description']} ({match['category']}) - KES {match['price']}")
        
        print(f"\nTotal Estimated Cost Range (for high probability conditions):")
        print(f"KES {prediction['cost_estimates']['total_min']} - {prediction['cost_estimates']['total_max']}")
        
        print("\nRecommendations:")
        for rec in prediction["recommendations"]:
            print(f"• {rec}")
