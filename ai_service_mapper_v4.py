import openai
from typing import Dict, List, Tuple, Optional
from service_mapper_final2 import ServiceMapper
import os
import json
from collections import defaultdict
import re

class AIServiceMapper:
    def __init__(self, api_key: str = None):
        """Initialize the AI-powered service mapper with caching."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = openai.OpenAI(api_key=self.api_key)
        self.service_mapper = ServiceMapper()
        
        # Load cached data
        self.prediction_cache = self._load_cache('prediction_cache.json')
        self.analysis_cache = self._load_cache('analysis_cache.json')
        
        # Build service relationships graph
        self.service_relationships = self._build_relationships()
        
    def _load_cache(self, filename: str) -> Dict:
        """Load cached data from JSON file."""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
            
    def _save_prediction(self, query: str, analysis: Dict):
        """Save prediction to cache."""
        try:
            self.prediction_cache[query] = analysis
            with open('prediction_cache.json', 'w') as f:
                json.dump(self.prediction_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save to cache: {e}")
            
    def _build_relationships(self) -> Dict[str, set]:
        """Build a graph of related services from analysis cache."""
        relationships = defaultdict(set)
        
        # Extract relationships from analysis cache
        for group in self.analysis_cache.values():
            codes = set()
            for service in group:
                codes.add(service['service_code'])
                if 'related_codes' in service:
                    codes.update(service['related_codes'])
            
            # Create bidirectional relationships
            for code1 in codes:
                for code2 in codes:
                    if code1 != code2:
                        relationships[code1].add(code2)
                        
        return relationships
        
    def _find_similar_query(self, query: str) -> Optional[str]:
        """Find a similar query in the prediction cache."""
        query_words = set(re.findall(r'\w+', query.lower()))
        
        best_match = None
        best_score = 0.5  # Minimum similarity threshold
        
        for cached_query in self.prediction_cache:
            cached_words = set(re.findall(r'\w+', cached_query.lower()))
            # Calculate Jaccard similarity
            similarity = len(query_words & cached_words) / len(query_words | cached_words)
            if similarity > best_score:
                best_score = similarity
                best_match = cached_query
                
        return best_match
        
    def _analyze_query(self, query: str) -> Dict:
        """Use OpenAI to analyze the query with caching."""
        # Check for exact or similar match in cache
        cached_query = query if query in self.prediction_cache else self._find_similar_query(query)
        if cached_query:
            print("Using cached analysis...")
            return self.prediction_cache[cached_query]
            
        system_prompt = """
        You are a medical services assistant. For any query, consider:
        1. Primary symptoms or concerns
        2. Required diagnostic tests
        3. Consultation needs
        4. Follow-up care
        
        Format response as JSON:
        {
            "category": "Radiology or General",
            "service_type": "specific service type",
            "search_terms": ["list of search terms"],
            "context": "detailed context",
            "priority": "routine|urgent|emergency"
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
            self._save_prediction(query, result)
            return result
            
        except Exception as e:
            print(f"Error analyzing query: {e}")
            return {
                "category": "General",
                "service_type": "consultation",
                "search_terms": ["consultation", "examination"],
                "context": "General medical consultation",
                "priority": "routine"
            }
            
    def _get_related_services(self, service_codes: List[str], limit: int = 3) -> List[Dict]:
        """Find related services based on cached relationships."""
        related = set()
        for code in service_codes:
            if code in self.service_relationships:
                related.update(self.service_relationships[code])
        
        # Get service details for related codes
        related_services = []
        for code in list(related)[:limit]:
            services = self.service_mapper.find_services_by_code(code)
            if services:
                related_services.extend(services)
                
        return related_services
            
    def _get_recommendations(self, services: List[Dict], query_context: str, priority: str = "routine") -> str:
        """Get AI recommendations with enhanced context."""
        if not services:
            return "No services found matching your query."
            
        # Group services by type
        radiology = [s for s in services if s["category"] == "RADIOLOGY"]
        consultations = [s for s in services if "consultation" in s["description"].lower()]
        examinations = [s for s in services if "examination" in s["description"].lower()]
        related = self._get_related_services([s["code"] for s in services])
        
        services_summary = []
        if radiology:
            services_summary.append("Diagnostic Services:")
            for s in radiology[:3]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
                
        if consultations:
            services_summary.append("\nConsultation Services:")
            for s in consultations[:2]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
                
        if examinations:
            services_summary.append("\nExamination Services:")
            for s in examinations[:2]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
                
        if related:
            services_summary.append("\nRelated Services You May Need:")
            for s in related[:3]:
                services_summary.append(f"- {s['description']} (KES {s['base_price']})")
        
        prompt = f"""
        Based on the query context: "{query_context}"
        Priority level: {priority}
        Available services:
        {chr(10).join(services_summary)}
        
        Provide a comprehensive care plan that:
        1. Suggests the most appropriate initial services based on priority
        2. Includes consultation and follow-up recommendations
        3. Mentions the total estimated cost for recommended services
        4. Explains why each recommended service is important
        Keep response under 200 words.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical services assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=250
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return "Unable to generate recommendations at this time."
    
    def search(self, query: str) -> Tuple[List[Dict], str]:
        """Search for services with enhanced caching and recommendations."""
        query_lower = query.lower()
        analysis = self._analyze_query(query)
        
        # Build search terms based on query type
        search_terms = set(analysis["search_terms"])
        
        # Add specific terms for lung-related queries
        if any(term in query_lower for term in ['lung', 'chest', 'breathing', 'smoking', 'cancer']):
            search_terms.update([
                'chest x-ray',
                'chest xray',
                'ct scan chest',
                'ct scan',
                'x-ray chest',
                'consultation',
                'examination'
            ])
        
        # Add common related terms based on cached analyses
        for cached_query, cached_analysis in self.prediction_cache.items():
            if any(term in query_lower for term in cached_analysis.get("search_terms", [])):
                search_terms.update(cached_analysis["search_terms"])
        
        # Collect all relevant services
        all_services = []
        seen_codes = set()
        
        # First try specific categories
        categories = ["RADIOLOGY", "GENERAL"] if analysis["category"] == "Radiology" else ["GENERAL", "RADIOLOGY"]
        for category in categories:
            for term in search_terms:
                services = self.service_mapper.find_services(category, term)
                for service in services:
                    if service["code"] not in seen_codes:
                        service["category"] = category  # Ensure category is set
                        all_services.append(service)
                        seen_codes.add(service["code"])
        
        # If no services found, try a broader search
        if not all_services:
            general_terms = ["consultation", "examination", "medical exam"]
            for term in general_terms:
                services = self.service_mapper.find_services("GENERAL", term)
                for service in services:
                    if service["code"] not in seen_codes:
                        service["category"] = "GENERAL"
                        all_services.append(service)
                        seen_codes.add(service["code"])
        
        # Sort services by relevance and price
        all_services.sort(key=lambda x: (
            -1 if x["category"] == analysis["category"] else 0,  # Prioritize matching category
            -1 if any(term.lower() in x["description"].lower() for term in search_terms) else 0,  # Then by term match
            x["base_price"]  # Then by price
        ))
        
        # Get recommendations with priority
        recommendation = self._get_recommendations(
            all_services, 
            analysis["context"],
            analysis.get("priority", "routine")
        )
        
        return all_services, recommendation

    def close(self):
        """Close the service mapper connection."""
        self.service_mapper.close()
