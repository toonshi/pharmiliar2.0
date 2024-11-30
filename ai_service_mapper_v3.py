import openai
from typing import Dict, List, Tuple, Optional
from service_mapper_final2 import ServiceMapper
import os
import json

class AIServiceMapper:
    def __init__(self, api_key: str = None):
        """Initialize the AI-powered service mapper."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = openai.OpenAI(api_key=self.api_key)
        self.service_mapper = ServiceMapper()
        
    def _analyze_query(self, query: str) -> Dict:
        """Use OpenAI to analyze the natural language query."""
        system_prompt = """
        You are a medical services assistant. For lung-related queries, always consider:
        1. Chest X-rays for initial screening
        2. CT scans for detailed imaging
        3. Medical consultations for assessment
        4. Regular check-ups for monitoring
        
        Format response as JSON:
        {
            "category": "Radiology or General",
            "service_type": "specific service type",
            "search_terms": ["list of search terms"],
            "context": "detailed context"
        }
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
            return {
                "category": "Radiology",
                "service_type": "chest examination",
                "search_terms": ["chest x-ray", "ct scan chest", "consultation"],
                "context": "Lung health assessment"
            }
    
    def _get_recommendations(self, services: List[Dict], query_context: str) -> str:
        """Get AI recommendations based on found services."""
        if not services:
            return "No services found matching your query."
            
        # Group services by type
        radiology_services = [s for s in services if s["category"] == "RADIOLOGY"]
        consultation_services = [s for s in services if "consultation" in s["description"].lower()]
        examination_services = [s for s in services if "examination" in s["description"].lower()]
        
        services_summary = []
        if radiology_services:
            services_summary.append("Diagnostic Services:")
            for s in radiology_services[:3]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
                
        if consultation_services:
            services_summary.append("\nConsultation Services:")
            for s in consultation_services[:2]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
                
        if examination_services:
            services_summary.append("\nExamination Services:")
            for s in examination_services[:2]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
        
        prompt = f"""
        Based on the query context: "{query_context}"
        Available services:
        {chr(10).join(services_summary)}
        
        Provide a comprehensive recommendation that:
        1. Suggests the most appropriate initial diagnostic test
        2. Includes consultation for professional medical advice
        3. Mentions the total estimated cost for recommended services
        4. Emphasizes the importance of early detection
        Keep response under 150 words.
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
        """Search for services using AI-powered query analysis."""
        query_lower = query.lower()
        analysis = self._analyze_query(query)
        
        # Build search terms based on query type
        search_terms = set(analysis["search_terms"])
        if any(term in query_lower for term in ['lung', 'chest', 'breathing', 'smoking', 'cancer']):
            search_terms.update([
                'chest x-ray',
                'chest xray',
                'ct scan chest',
                'ct scan',
                'x-ray chest'
            ])
        
        # Collect all relevant services
        all_services = []
        seen_codes = set()
        
        # Search Radiology first
        for term in search_terms:
            services = self.service_mapper.find_services("Radiology", term)
            for service in services:
                if service["code"] not in seen_codes:
                    all_services.append(service)
                    seen_codes.add(service["code"])
        
        # Then search General services
        general_terms = ["consultation", "examination", "medical exam"]
        if "cancer" in query_lower or "screening" in query_lower:
            general_terms.append("medical")
            
        for term in general_terms:
            services = self.service_mapper.find_services("General", term)
            for service in services:
                if service["code"] not in seen_codes:
                    all_services.append(service)
                    seen_codes.add(service["code"])
        
        # Sort services by relevance and price
        all_services.sort(key=lambda x: (
            -1 if any(term in x["description"].lower() for term in ['chest', 'lung', 'ct', 'x-ray']) else 0,
            x["base_price"]
        ))
        
        # Enhance context for recommendation
        enhanced_context = analysis["context"]
        if "lung" in query_lower or "chest" in query_lower:
            enhanced_context += " Focus on diagnostic imaging and screening options."
        if "cancer" in query_lower:
            enhanced_context += " Consider both immediate diagnostic needs and follow-up care."
            
        recommendation = self._get_recommendations(all_services, enhanced_context)
        
        return all_services, recommendation
    
    def close(self):
        """Close the service mapper connection."""
        self.service_mapper.close()
