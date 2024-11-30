import openai
from typing import Dict, List, Tuple, Optional
from service_mapper_final2 import ServiceMapper
import os
import json

class AIServiceMapper:
    def __init__(self, api_key: str = None):
        """Initialize the AI-powered service mapper."""
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass to constructor.")
            
        openai.api_key = self.api_key
        self.service_mapper = ServiceMapper()
        
    def _analyze_query(self, query: str) -> Dict:
        """Use OpenAI to analyze the natural language query."""
        system_prompt = """
        You are a medical services assistant. Analyze the user's query and extract:
        1. The medical service category (Radiology or General)
        2. The specific service or examination type
        3. Any relevant medical terms or synonyms
        4. Additional context or requirements
        
        Format your response as a JSON object with these keys:
        {
            "category": "Radiology or General",
            "service_type": "specific service type",
            "search_terms": ["list of search terms to try"],
            "context": "additional context"
        }
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error analyzing query: {e}")
            # Fallback to basic analysis
            return {
                "category": "Radiology" if any(x in query.lower() for x in ["x-ray", "xray", "scan", "ultrasound", "mri"]) else "General",
                "service_type": query,
                "search_terms": [query],
                "context": ""
            }
    
    def _get_recommendations(self, services: List[Dict], query_context: str) -> str:
        """Get AI recommendations based on found services."""
        if not services:
            return "No services found matching your query."
            
        services_str = "\n".join([
            f"- {s['description']} (Code: {s['code']}, Price: KES {s['base_price']})"
            for s in services[:5]
        ])
        
        prompt = f"""
        Based on the user's query context: "{query_context}"
        And these available services:
        {services_str}
        
        Provide a brief, helpful recommendation about which service might be most appropriate.
        Focus on price ranges and any relevant medical considerations.
        Keep your response under 100 words.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical services assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return "Unable to generate recommendations at this time."
    
    def search(self, query: str) -> Tuple[List[Dict], str]:
        """
        Search for services using AI-powered query analysis.
        Returns tuple of (services, recommendation).
        """
        # Analyze the query
        analysis = self._analyze_query(query)
        
        # Search for services using each suggested term
        all_services = []
        for term in analysis["search_terms"]:
            services = self.service_mapper.find_services(
                analysis["category"],
                term
            )
            # Add unique services
            for service in services:
                if service not in all_services:
                    all_services.append(service)
        
        # Get AI recommendations
        recommendation = self._get_recommendations(all_services, analysis["context"])
        
        return all_services, recommendation
    
    def close(self):
        """Close the service mapper connection."""
        self.service_mapper.close()

def test_ai_mapper():
    """Test the AI-powered service mapper."""
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
        
    mapper = AIServiceMapper(api_key)
    
    test_queries = [
        "I need an x-ray for my chest pain",
        "Looking for a general consultation with a doctor",
        "Need an ultrasound scan for pregnancy",
        "What kind of scan do I need for a head injury?",
        "Regular medical checkup",
    ]
    
    print("\nTesting AI Service Mapper")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        services, recommendation = mapper.search(query)
        
        if services:
            min_price = min(s["base_price"] for s in services)
            max_price = max(s["base_price"] for s in services)
            print(f"Found {len(services)} services")
            print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
            
            for service in services:
                print(f"- {service['description']} ({service['code']})")
                print(f"  Price: KES {service['base_price']:.2f}")
                
            print("\nRecommendation:")
            print(recommendation)
        else:
            print("No services found")
    
    mapper.close()

if __name__ == "__main__":
    test_ai_mapper()
