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
            
        self.client = openai.OpenAI(api_key=self.api_key)
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
        
        For lung-related issues, consider both x-ray and CT scan options.
        For cancer screening, include relevant examination and consultation services.
        """
        
        try:
            response = self.client.chat.completions.create(
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
                "category": "Radiology" if any(x in query.lower() for x in ["x-ray", "xray", "scan", "ultrasound", "mri", "lung", "chest"]) else "General",
                "service_type": "examination",
                "search_terms": ["chest x-ray", "ct scan", "consultation"],
                "context": "Lung-related examination"
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
        For lung-related issues, emphasize the importance of early detection and regular check-ups.
        Keep your response under 150 words.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical services assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
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
        seen_codes = set()  # Track unique services
        
        # First try Radiology for specific tests
        for term in analysis["search_terms"]:
            services = self.service_mapper.find_services("Radiology", term)
            for service in services:
                if service["code"] not in seen_codes:
                    all_services.append(service)
                    seen_codes.add(service["code"])
        
        # Then try General for consultations and examinations
        for term in ["consultation", "examination"]:
            services = self.service_mapper.find_services("General", term)
            for service in services:
                if service["code"] not in seen_codes:
                    all_services.append(service)
                    seen_codes.add(service["code"])
        
        # Get AI recommendations
        recommendation = self._get_recommendations(all_services, analysis["context"])
        
        return all_services, recommendation
    
    def close(self):
        """Close the service mapper connection."""
        self.service_mapper.close()
