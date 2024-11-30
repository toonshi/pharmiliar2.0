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
        2. Recommended diagnostic tests
        3. Potential treatments
        Please format your response as valid JSON with the following structure:
        {{
            "possible_conditions": [{{
                "condition": "name",
                "probability": "high/medium/low"
            }}],
            "diagnostic_tests": ["test1", "test2"],
            "treatments": ["treatment1", "treatment2"]
        }}

        Symptoms: {symptoms}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical cost analysis assistant. Provide structured analysis of symptoms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return None

    def estimate_costs(self, analysis: Dict) -> Dict:
        """
        Estimate costs based on the analysis and our database
        """
        cost_estimates = {
            "diagnostic_tests": [],
            "treatments": [],
            "total_min": 0,
            "total_max": 0
        }

        cursor = self.conn.cursor()

        # Estimate costs for diagnostic tests
        for test in analysis["diagnostic_tests"]:
            cursor.execute("""
                SELECT description, base_price 
                FROM services 
                WHERE LOWER(description) LIKE ? 
                AND department_name IN ('LABORATORY', 'RADIOLOGY', 'DIAGNOSTICS')
            """, (f"%{test.lower()}%",))
            
            results = cursor.fetchall()
            if results:
                cost_estimates["diagnostic_tests"].append({
                    "test": test,
                    "estimated_cost": results[0][1],  # Using the first match for now
                    "description": results[0][0]
                })
                cost_estimates["total_min"] += results[0][1]
                cost_estimates["total_max"] += results[0][1]

        # Estimate costs for treatments
        for treatment in analysis["treatments"]:
            cursor.execute("""
                SELECT description, base_price 
                FROM services 
                WHERE LOWER(description) LIKE ?
            """, (f"%{treatment.lower()}%",))
            
            results = cursor.fetchall()
            if results:
                cost_estimates["treatments"].append({
                    "treatment": treatment,
                    "estimated_cost": results[0][1],
                    "description": results[0][0]
                })
                cost_estimates["total_min"] += results[0][1]
                cost_estimates["total_max"] += results[0][1]

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

        # Combine results
        prediction = {
            "analysis": analysis,
            "cost_estimates": cost_estimates,
            "recommendations": self._generate_recommendations(cost_estimates)
        }

        # Cache the result
        self.cache[cache_key] = prediction
        self.save_cache()

        return prediction

    def _generate_recommendations(self, cost_estimates: Dict) -> List[str]:
        """
        Generate cost-saving recommendations based on the estimates
        """
        recommendations = []
        
        if cost_estimates["total_max"] > 10000:  # Arbitrary threshold
            recommendations.append("Consider getting multiple quotes from different hospitals")
        
        if len(cost_estimates["diagnostic_tests"]) > 2:
            recommendations.append("Ask your doctor if all diagnostic tests are necessary at once")
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    predictor = CostPredictor()
    
    # Example symptoms
    symptoms = "I have been experiencing severe headache for the past 3 days, sensitivity to light, and nausea"
    
    # Get prediction
    prediction = predictor.get_cost_prediction(symptoms)
    
    # Print results
    print("\nAnalysis Results:")
    print(json.dumps(prediction, indent=2))
