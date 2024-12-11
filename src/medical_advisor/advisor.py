import json
from datetime import datetime
import openai
from typing import Dict, List
from pathlib import Path
from .services import ServiceManager
from .service_priority import ServicePriority


class Advisor:
    def __init__(self, api_key: str):
        """Initialize the medical advisor system."""
        self.client = openai.OpenAI(api_key=api_key)
        self.service_manager = ServiceManager(api_key)
        self.collection = self.service_manager.get_collection()
        
        if not self.collection or self.collection.count() == 0:
            raise ValueError("Medical services database is empty. Please run populate_services.py first.")
        
        # Define search priorities
        self.search_priorities = {
            "respiratory": {
                "diagnostic": [
                    "throat swab culture respiratory infection",
                    "sputum analysis respiratory infection",
                    "blood test complete blood count infection",
                    "chest x-ray respiratory infection"
                ],
                "treatment": [
                    "antibiotics treatment respiratory infection",
                    "nebulizer treatment respiratory infection",
                    "oxygen therapy respiratory infection"
                ],
                "monitoring": [
                    "vital signs monitoring respiratory",
                    "oxygen saturation monitoring"
                ]
            },
            "infectious": {
                "diagnostic": [
                    "blood culture for infectious fever",
                    "urine culture for fever infection",
                    "chest x-ray infectious fever"
                ],
                "treatment": [
                    "antibiotics for infectious fever",
                    "antipyretics for fever reduction"
                ],
                "monitoring": [
                    "temperature monitoring fever",
                    "vital signs monitoring fever"
                ]
            },
            # Add other condition types as needed
        }

    def _get_search_queries(self, condition_type: str, category: str) -> List[str]:
        """Generate search queries based on condition type and category."""
        if condition_type in self.search_priorities:
            if category in self.search_priorities[condition_type]:
                return self.search_priorities[condition_type][category]
            else:
                return []  # Return an empty list if the category is not found
        else:
            return []  # Return an empty list if the condition type is not found

    def get_service_recommendations(self, condition: str, budget_level: str = "standard") -> Dict:
        """Get recommended medical services for a condition."""
        try:
            print(f"\nStarting service recommendation process for condition: {condition}")
            
            # Determine condition type
            try:
                type_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "system", 
                        "content": "Classify the medical condition into one of these types: respiratory, cardiac, digestive, musculoskeletal, neurological, endocrine, infectious, dermatological, hematological, renal, reproductive, psychiatric, immunological, oncological, pediatric, geriatric, trauma/injury or other. Respond with just the type."
                    }, {
                        "role": "user", 
                        "content": f"Classify this condition: {condition}"
                    }]
                )
                condition_type = type_response.choices[0].message.content.lower().strip()
                print(f"Detected condition type: {condition_type}")
            except Exception as e:
                print(f"Error detecting condition type: {e}")
                return {"error": "Failed to classify condition type."}

            # Get prioritized search queries
            all_results = []
            categories = ["diagnostic", "treatment", "monitoring"]

            for category in categories:
                try:
                    queries = self._get_search_queries(condition_type, category)
                    if not queries:
                        queries = [f"{category} for {condition}"]
                    
                    for query in queries:
                        print(f"\nSearching for {category}: {query}")
                        try:
                            results = self.collection.query(
                                query_texts=[query],
                                n_results=3  # Limit results per query
                            )
                            print(f"Results: {results}")  # Log the results for debugging
                            if not results or not results.get("documents"):
                                print(f"No results found for query: {query}")
                                continue
                            
                            # Add category to results
                            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                                service_desc = doc.split("Medical service:")[1].split("Department:")[0].strip()
                                service_info = {
                                    "description": service_desc,
                                    "department": meta["department"],
                                    "price": float(meta["price"]),
                                    "code": meta["code"],
                                    "category": category
                                }
                                all_results.append(service_info)
                        except Exception as e:
                            print(f"Error querying collection for {query}: {e}")
                            
                except Exception as e:
                    print(f"Error getting search queries for category {category}: {e}")

            # Format and filter results
            formatted_results = {
                "services": [],
                "total_cost": 599.0,
                "departments": set(),
                "categories": {
                    "diagnostic": [],
                    "treatment": [],
                    "monitoring": []
                }
            }

            # Score and deduplicate services by category
            for category in categories:
                category_services = [s for s in all_results if s["category"] == category]
                
                # Score services
                scored_services = []
                for service in category_services:
                    # Use priority weight as base score
                    priority = ServicePriority.get_service_priority(service)
                    base_score = ServicePriority.get_priority_weight(priority)
                    
                    # Adjust score based on price (lower price = higher score)
                    price_factor = 1.0
                    if float(service["price"]) <= ServicePriority.PRICE_THRESHOLDS["basic"]:
                        price_factor = 1.5
                    
                    final_score = base_score * price_factor
                    service["relevance_score"] = final_score
                    scored_services.append(service)
                
                # Deduplicate similar services
                unique_services = ServicePriority.consolidate_oxygen_services(scored_services)
                
                # Add to results
                formatted_results["categories"][category] = unique_services
                for service in unique_services:
                    formatted_results["services"].append(service)
                    formatted_results["total_cost"] += service["price"]
                    formatted_results["departments"].add(service["department"])
            
            formatted_results["departments"] = sorted(list(formatted_results["departments"]))
            return formatted_results
        
        except Exception as e:
            print(f"Error in service recommendation process: {e}")
            return {"error": "Failed to generate service recommendations."}
        




            return self.search_priorities[condition_type].get(category, [])
        return []
    
    def analyze_symptoms(self, symptoms: str) -> Dict:
        """Analyze symptoms and provide medical assessment."""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system", 
                "content": """You are a medical expert. Analyze the symptoms and provide:
                    1. Possible conditions (list the most likely ones first)
                    2. Risk level (Low, Medium, High) with explanation
                    3. Recommended immediate steps
                    4. Warning signs to watch for
                    5. Type of specialist needed (if any)

                    Format your response in clear sections with bullet points."""},
                {"role": "user", "content": f"Analyze these symptoms: {symptoms}"}
            ]
        )
        return {"analysis": response.choices[0].message.content}
    

    def save_consultation(self, data: Dict) -> str:
        """Save consultation data to file."""
        reports_dir = Path(__file__).parent.parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consultation_{timestamp}.json"
        filepath = reports_dir / filename
        
        # Add timestamp and format data
        data["timestamp"] = datetime.now().isoformat()
        data["consultation_id"] = timestamp
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)

    def get_treatment_plan(self, condition: str, budget_level: str = "standard") -> Dict:
        """Generate a comprehensive treatment plan with cost estimates."""
        # Get service recommendations first
        services = self.get_service_recommendations(condition, budget_level)
        
        # Create a categorized summary of available services
        service_summary = "\nRecommended Medical Services:"
        
        if services["categories"]["diagnostic"]:
            service_summary += "\n\nDiagnostic Tests (in order of priority):"
            for s in services["categories"]["diagnostic"]:
                service_summary += f"\n- {s['description']} ({s['department']}) - KSH {s['price']:,.2f}"
            
        if services["categories"]["treatment"]:
            service_summary += "\n\nTreatments (in order of priority):"
            for s in services["categories"]["treatment"]:
                service_summary += f"\n- {s['description']} ({s['department']}) - KSH {s['price']:,.2f}"
            
        if services["categories"]["monitoring"]:
            service_summary += "\n\nMonitoring Services (in order of priority):"
            for s in services["categories"]["monitoring"]:
                service_summary += f"\n- {s['description']} ({s['department']}) - KSH {s['price']:,.2f}"
        
        # Generate treatment plan
        plan_response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""You are a medical expert creating a treatment plan. 
                Consider these available services:{service_summary}
                
                Total estimated cost: KSH {services['total_cost']:,.2f}
                Departments involved: {', '.join(services['departments'])}
                Budget level: {budget_level}
                
                Create a {budget_level} budget treatment plan that includes:
                1. Essential diagnostic tests (start with basic tests before advanced imaging)
                2. Recommended treatments (prioritize cost-effective options)
                3. Required monitoring and follow-up
                4. Timeline for all services
                5. Cost-saving suggestions
                6. Important precautions
                
                Format your response in clear sections with bullet points.
                Focus on essential services and cost-effective options first.Be thorough,remember that nothing can hav a cost of 0, if you see 0, use your own wisdom and decide a figure"""},
                {"role": "user", "content": f"Create a treatment plan for: {condition}"}
            ]
        )
        
        return {
            "condition": condition,
            "budget_level": budget_level,
            "available_services": services,
            "treatment_plan": plan_response.choices[0].message.content,
            "total_estimated_cost": services["total_cost"]
        }