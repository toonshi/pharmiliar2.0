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
        """Load prediction cache if exists"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def save_cache(self):
        """Save predictions to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def analyze_symptoms(self, symptoms: str) -> Dict:
        """
        Analyze symptoms using GPT-4 to predict possible conditions and required services
        """
        prompt = f"""Based on the following symptoms, provide a structured analysis of:
        1. Possible conditions (most likely first)
        2. Required medical services (be specific about tests, procedures, and medications)
        3. Potential treatments

        Format as JSON with this structure:
        {{
            "possible_conditions": [{{
                "condition": "name",
                "probability": "high/medium/low"
            }}],
            "required_services": [{{
                "service": "name",
                "category": "test/procedure/medication",
                "keywords": ["word1", "word2"]
            }}],
            "treatments": [{{
                "treatment": "name",
                "keywords": ["word1", "word2"]
            }}]
        }}

        Be specific with medical terminology and include alternative names/keywords for services.
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
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return None

    def find_matching_services(self, search_terms: List[str], category_type: str = None) -> List[Dict]:
        """
        Find services matching any of the search terms
        """
        matches = []
        cursor = self.conn.cursor()
        
        for term in search_terms:
            # Search in description
            query = """
                SELECT description, base_price, category, code
                FROM services 
                WHERE LOWER(description) LIKE ?
                AND base_price > 0
            """
            cursor.execute(query, (f"%{term.lower()}%",))
            
            results = cursor.fetchall()
            for result in results:
                description, base_price, category, code = result
                
                # Skip if we already have this service
                if any(m['description'] == description for m in matches):
                    continue
                
                # Get prices for all tiers
                tiers = {}
                base_desc = description.replace('-K', '').replace('-Nk', '').replace('-P', '')
                for tier in ['-K', '-Nk', '-P']:
                    cursor.execute("""
                        SELECT base_price 
                        FROM services 
                        WHERE description LIKE ? 
                        AND base_price > 0
                        LIMIT 1
                    """, (f"{base_desc}{tier}%",))
                    tier_result = cursor.fetchone()
                    if tier_result:
                        tiers[tier.strip('-')] = tier_result[0]
                
                matches.append({
                    'description': description,
                    'base_price': base_price,
                    'category': category,
                    'code': code,
                    'pricing_tiers': tiers
                })
        
        return matches

    def estimate_costs(self, analysis: Dict) -> Dict:
        """
        Estimate costs based on the analysis and our database
        """
        cost_estimates = {
            "services": [],
            "treatments": [],
            "total_min": 0,
            "total_max": 0
        }

        # Process required services
        for service in analysis["required_services"]:
            search_terms = [service["service"]] + service["keywords"]
            matches = self.find_matching_services(search_terms)
            
            if matches:
                for match in matches:
                    service_cost = {
                        "service": service["service"],
                        "matched_service": match["description"],
                        "category": match["category"],
                        "pricing_tiers": match["pricing_tiers"]
                    }
                    
                    # Calculate min and max costs across tiers
                    prices = list(match["pricing_tiers"].values())
                    if prices:
                        service_cost["min_cost"] = min(prices)
                        service_cost["max_cost"] = max(prices)
                        cost_estimates["total_min"] += service_cost["min_cost"]
                        cost_estimates["total_max"] += service_cost["max_cost"]
                    
                    cost_estimates["services"].append(service_cost)

        # Process treatments
        for treatment in analysis["treatments"]:
            search_terms = [treatment["treatment"]] + treatment["keywords"]
            matches = self.find_matching_services(search_terms)
            
            if matches:
                for match in matches:
                    treatment_cost = {
                        "treatment": treatment["treatment"],
                        "matched_service": match["description"],
                        "category": match["category"],
                        "pricing_tiers": match["pricing_tiers"]
                    }
                    
                    # Calculate min and max costs across tiers
                    prices = list(match["pricing_tiers"].values())
                    if prices:
                        treatment_cost["min_cost"] = min(prices)
                        treatment_cost["max_cost"] = max(prices)
                        cost_estimates["total_min"] += treatment_cost["min_cost"]
                        cost_estimates["total_max"] += treatment_cost["max_cost"]
                    
                    cost_estimates["treatments"].append(treatment_cost)

        return cost_estimates

    def get_cost_prediction(self, symptoms: str) -> Dict:
        """
        Main function to get cost prediction based on symptoms
        """
        # Check cache first
        cache_key = symptoms.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Analyze symptoms
        analysis = self.analyze_symptoms(symptoms)
        if not analysis:
            return {"error": "Could not analyze symptoms"}

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
        """
        Generate cost-saving recommendations based on the analysis and estimates
        """
        recommendations = []
        
        # Cost-based recommendations
        if cost_estimates["total_max"] > 10000:
            recommendations.append("Consider getting treatment under NHIF coverage to reduce costs")
            recommendations.append("Ask about available payment plans or financial assistance")
        
        # Service-based recommendations
        if len(cost_estimates["services"]) > 2:
            recommendations.append("Discuss with your doctor if all tests can be done in phases to spread out costs")
        
        # Treatment-based recommendations
        if any(t["max_cost"] > 5000 for t in cost_estimates["treatments"] if "max_cost" in t):
            recommendations.append("Ask about generic alternatives for expensive medications")
        
        # Add tier-based recommendation
        recommendations.append("Prices vary by tier (K, Nk, P). Discuss with the hospital which tier applies to you")
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    predictor = CostPredictor()
    
    # Example symptoms
    symptoms = "I have been experiencing severe headache for the past 3 days, sensitivity to light, and nausea"
    
    # Get prediction
    prediction = predictor.get_cost_prediction(symptoms)
    
    # Print results in a readable format
    print("\nAnalysis Results:")
    print("\n1. Possible Conditions:")
    for condition in prediction["analysis"]["possible_conditions"]:
        print(f"- {condition['condition']} (Probability: {condition['probability']})")
    
    print("\n2. Required Services and Costs:")
    for service in prediction["cost_estimates"]["services"]:
        print(f"\nService: {service['service']}")
        print(f"Matched Service: {service['matched_service']}")
        print("Pricing Tiers:")
        for tier, price in service['pricing_tiers'].items():
            print(f"  - {tier}: KES {price}")
    
    print("\n3. Treatments and Costs:")
    for treatment in prediction["cost_estimates"]["treatments"]:
        print(f"\nTreatment: {treatment['treatment']}")
        print(f"Matched Service: {treatment['matched_service']}")
        print("Pricing Tiers:")
        for tier, price in treatment['pricing_tiers'].items():
            print(f"  - {tier}: KES {price}")
    
    print(f"\nEstimated Total Cost Range: KES {prediction['cost_estimates']['total_min']} - {prediction['cost_estimates']['total_max']}")
    
    print("\nRecommendations:")
    for rec in prediction["recommendations"]:
        print(f"- {rec}")
