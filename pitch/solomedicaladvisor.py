""" An implementation with everything in one place.Incase you need that for some reaseom"""

import json
import openai
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import os
import chromadb
from datetime import datetime
import re

class ChromaMedicalAdvisor:
    def __init__(self, api_key: str):
        """Initialize advisor with existing ChromaDB."""
        self.client = openai.OpenAI(api_key=api_key)
        
        # Connect to existing database
        self.chroma_client = chromadb.PersistentClient(path="./db")
        
        # Use OpenAI embeddings to match database dimension (1536)
        self.embedding_func = chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
        
        # Get existing collection
        collections = self.chroma_client.list_collections()
        if collections:
            collection_name = collections[0].name
            try:
                # Try to get existing collection first
                self.collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_func
                )
            except ValueError:
                # If it doesn't exist with embedding function, create new
                self.collection = self.chroma_client.create_collection(
                    name=f"{collection_name}_v2",
                    embedding_function=self.embedding_func
                )
            print(f"Connected to database collection: {self.collection.name}")
            print(f"Using embedding model: text-embedding-ada-002")
        else:
            print("Warning: No collections found in database")
            self.collection = None

    def query_database(self, query: str, n_results: int = 3) -> List[Dict]:
        """Query the existing database for relevant information."""
        if not self.collection:
            return []
            
        try:
            # Add medical context to query
            medical_query = f"medical condition or treatment: {query}"
            
            results = self.collection.query(
                query_texts=[medical_query],
                n_results=n_results,
                include=["documents", "metadatas"]
            )
            
            if results and results['documents']:
                docs = []
                for doc in results['documents'][0]:
                    try:
                        if isinstance(doc, str):
                            docs.append(json.loads(doc))
                        else:
                            docs.append(doc)
                    except json.JSONDecodeError:
                        print(f"Skipping invalid document: {doc[:100]}...")
                return docs
        except Exception as e:
            print(f"Database query failed: {str(e)}")
            return []
        
        return []

    def get_service_details(self, service: str) -> Dict:
        """Get service details from database."""
        matches = self.query_database(f"medical service: {service}")
        if not matches:
            return {
                'cost': 0,
                'source': 'Estimated',
                'locations': [],
                'details': {}
            }
            
        service_data = matches[0]
        
        # Extract cost from various possible formats
        cost = service_data.get('price', 0)
        if isinstance(cost, str):
            try:
                cost = float(cost.replace('KES', '').replace(',', '').strip())
            except:
                cost = 0
        
        return {
            'cost': cost,
            'source': 'Database',
            'locations': service_data.get('locations', []),
            'details': service_data
        }

    def get_relevant_questions(self, condition: str) -> List[str]:
        """Generate relevant questions based on condition."""
        # First check database for similar cases
        db_matches = self.query_database(f"symptoms of {condition}")
        db_context = json.dumps(db_matches[:2], indent=2) if db_matches else ""
        
        prompt = f"""Given this medical concern: "{condition}"
        And these similar cases from our database: {db_context}
        
        Generate 5-7 most important questions to assess the situation.
        Focus on: symptoms, duration, severity, medical history, risk factors.
        Return ONLY a JSON array of questions."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Generate questions"}
            ]
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return [
                "How long have you been experiencing this symptom?",
                "Is there any pain or discomfort?",
                "Have you noticed any other symptoms?",
                "Have you had this condition before?",
                "Are you currently taking any medications?"
            ]

    def analyze_responses(self, condition: str, responses: Dict[str, str]) -> Dict:
        """Analyze responses and generate assessment."""
        # First check database for similar cases
        db_matches = self.query_database(f"diagnosis for {condition}")
        
        # Format responses for GPT
        formatted_responses = json.dumps(responses, indent=2)
        db_context = json.dumps(db_matches[:2], indent=2) if db_matches else ""
        
        prompt = f"""Based on:
        Condition: {condition}
        Patient responses: {formatted_responses}
        Database matches: {db_context}
        
        Provide a medical assessment with these exact JSON fields:
        {{
            "risk_level": "HIGH/MEDIUM/LOW",
            "immediate_steps": ["step1", "step2"],
            "required_tests": ["test1", "test2"],
            "estimated_timeline": "X days/weeks",
            "warning_signs": ["sign1", "sign2"],
            "recommended_specialists": ["specialist1", "specialist2"]
        }}"""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical advisor focusing on urinary tract and related conditions."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            assessment = json.loads(response.choices[0].message.content)
            
            # Enhance with real service data
            enhanced = assessment.copy()
            enhanced['services_data'] = {}
            
            # Get real costs from database
            for test in assessment['required_tests']:
                try:
                    service_info = self.get_service_details(test)
                    enhanced['services_data'][test] = service_info
                except Exception as e:
                    print(f"Failed to get service details for {test}: {str(e)}")
                    enhanced['services_data'][test] = {
                        'cost': 0,
                        'source': 'Estimated',
                        'locations': [],
                        'details': {}
                    }
            
            return enhanced
            
        except json.JSONDecodeError:
            # Fallback assessment for UTI-like symptoms
            return {
                "risk_level": "MEDIUM",
                "immediate_steps": [
                    "Consult a healthcare provider",
                    "Drink plenty of water",
                    "Avoid alcohol and caffeine"
                ],
                "required_tests": ["Urinalysis", "Urine culture"],
                "estimated_timeline": "1-2 days",
                "warning_signs": [
                    "Fever",
                    "Back pain",
                    "Blood in urine",
                    "Severe pain"
                ],
                "recommended_specialists": ["General Practitioner", "Urologist"],
                "services_data": {}
            }

    def generate_treatment_plan(self, assessment: Dict) -> Dict:
        """Generate treatment plans using database information."""
        # Get service costs from database
        services_data = {}
        for test in assessment['required_tests']:
            service_info = self.get_service_details(test)
            services_data[test] = service_info
        
        db_info = json.dumps(services_data, indent=2)
        
        prompt = f"""Based on this assessment: {json.dumps(assessment, indent=2)}
        And these available services: {db_info}
        
        Generate a treatment plan with these exact JSON fields:
        {{
            "standard_plan": {{
                "steps": ["step1", "step2"],
                "duration": "X weeks",
                "total_cost": "KES XXXX",
                "cost_breakdown": {{"service": "KES cost"}},
                "recommended_facilities": ["facility1"],
                "followup_schedule": "schedule"
            }},
            "budget_plan": {{
                "steps": ["step1", "step2"],
                "duration": "X weeks",
                "total_cost": "KES XXXX",
                "cost_breakdown": {{"service": "KES cost"}},
                "recommended_facilities": ["facility1"],
                "cost_saving_tips": ["tip1", "tip2"],
                "followup_schedule": "schedule"
            }},
            "comprehensive_plan": {{
                "steps": ["step1", "step2"],
                "duration": "X weeks",
                "total_cost": "KES XXXX",
                "cost_breakdown": {{"service": "KES cost"}},
                "recommended_facilities": ["facility1"],
                "additional_benefits": ["benefit1", "benefit2"],
                "followup_schedule": "schedule"
            }}
        }}"""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical advisor focusing on urinary tract and related conditions in Kenya."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback plan for UTI-like symptoms
            return {
                "standard_plan": {
                    "steps": [
                        "Visit a general practitioner",
                        "Complete urinalysis",
                        "Start prescribed antibiotics if needed"
                    ],
                    "duration": "1-2 weeks",
                    "total_cost": "KES 5000",
                    "cost_breakdown": {
                        "Consultation": "KES 2000",
                        "Urinalysis": "KES 1500",
                        "Basic antibiotics": "KES 1500"
                    },
                    "recommended_facilities": ["Nairobi Hospital", "Aga Khan Hospital"],
                    "followup_schedule": "After 3-5 days of treatment"
                },
                "budget_plan": {
                    "steps": [
                        "Visit local clinic",
                        "Basic urinalysis",
                        "Generic antibiotics if prescribed"
                    ],
                    "duration": "1-2 weeks",
                    "total_cost": "KES 3000",
                    "cost_breakdown": {
                        "Consultation": "KES 1000",
                        "Basic urinalysis": "KES 1000",
                        "Generic antibiotics": "KES 1000"
                    },
                    "recommended_facilities": ["Local government hospital", "Community clinic"],
                    "cost_saving_tips": ["Use NHIF if available", "Ask for generic medications"],
                    "followup_schedule": "As recommended by doctor"
                },
                "comprehensive_plan": {
                    "steps": [
                        "Urologist consultation",
                        "Complete urinalysis and culture",
                        "Prescription antibiotics",
                        "Follow-up tests"
                    ],
                    "duration": "2-3 weeks",
                    "total_cost": "KES 15000",
                    "cost_breakdown": {
                        "Specialist": "KES 5000",
                        "Complete tests": "KES 5000",
                        "Premium antibiotics": "KES 3000",
                        "Follow-up": "KES 2000"
                    },
                    "recommended_facilities": ["Aga Khan Hospital", "Karen Hospital"],
                    "additional_benefits": [
                        "Specialist care",
                        "Comprehensive testing",
                        "Premium medications",
                        "Priority follow-up"
                    ],
                    "followup_schedule": "Weekly follow-ups"
                }
            }

    def save_report(self, patient_name: str, condition: str, 
                   assessment: Dict, plan: Dict, responses: Dict[str, str]) -> Tuple[Path, Path]:
        """Save detailed report to JSON and TXT files."""
        # Create reports directory
        reports_dir = Path(__file__).parent.parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Sanitize filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', patient_name).strip('. ')
        safe_condition = re.sub(r'[<>:"/\\|?*]', '_', condition).strip('. ')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        base_filename = f"{safe_name}_{safe_condition}_{timestamp}"
        
        # Save JSON report
        json_report = {
            "patient_name": patient_name,
            "condition": condition,
            "timestamp": timestamp,
            "responses": responses,
            "assessment": assessment,
            "treatment_plan": plan
        }
        
        json_path = reports_dir / f"{base_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        # Save TXT report (formatted)
        txt_path = reports_dir / f"{base_filename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.format_report(json_report))
        
        return json_path, txt_path

    def format_report(self, report: Dict) -> str:
        """Format JSON report into readable text."""
        output = []
        
        # Header
        output.append("=== Medical Assessment Report ===")
        output.append(f"Patient: {report['patient_name']}")
        output.append(f"Condition: {report['condition']}")
        output.append(f"Date: {report['timestamp']}")
        
        # Patient Responses
        output.append("\n=== Patient Information ===")
        for question, answer in report['responses'].items():
            output.append(f"Q: {question}")
            output.append(f"A: {answer}")
        
        # Assessment
        assessment = report['assessment']
        output.append("\n=== Medical Assessment ===")
        output.append(f"Risk Level: {assessment['risk_level']}")
        
        output.append("\nImmediate Steps Required:")
        for step in assessment['immediate_steps']:
            output.append(f"- {step}")
        
        output.append("\nRequired Tests:")
        for test in assessment['required_tests']:
            service_data = assessment.get('services_data', {}).get(test, {})
            cost = service_data.get('cost', 'TBD')
            source = service_data.get('source', '')
            locations = service_data.get('locations', [])
            
            output.append(f"- {test}")
            if isinstance(cost, (int, float)):
                output.append(f"  Cost: KES {cost:,.2f} ({source})")
            else:
                output.append(f"  Cost: KES {cost} ({source})")
            if locations:
                output.append("  Available at:")
                for location in locations:
                    output.append(f"  - {location}")
        
        output.append(f"\nEstimated Timeline: {assessment['estimated_timeline']}")
        
        output.append("\nWarning Signs:")
        for sign in assessment['warning_signs']:
            output.append(f"- {sign}")
        
        output.append("\nRecommended Specialists:")
        for specialist in assessment['recommended_specialists']:
            output.append(f"- {specialist}")
        
        # Treatment Plans
        plan = report['treatment_plan']
        output.append("\n=== Treatment Plans ===")
        
        for plan_type in ['standard_plan', 'budget_plan', 'comprehensive_plan']:
            current_plan = plan[plan_type]
            name = plan_type.replace('_', ' ').title()
            
            output.append(f"\n{name}:")
            output.append("Steps:")
            for step in current_plan['steps']:
                output.append(f"- {step}")
            
            output.append(f"Duration: {current_plan['duration']}")
            output.append(f"Total Cost: {current_plan['total_cost']}")
            
            output.append("Cost Breakdown:")
            for service, cost in current_plan['cost_breakdown'].items():
                output.append(f"- {service}: {cost}")
            
            output.append("Recommended Facilities:")
            for facility in current_plan['recommended_facilities']:
                output.append(f"- {facility}")
            
            if 'cost_saving_tips' in current_plan:
                output.append("\nCost-Saving Tips:")
                for tip in current_plan['cost_saving_tips']:
                    output.append(f"- {tip}")
            
            if 'additional_benefits' in current_plan:
                output.append("\nAdditional Benefits:")
                for benefit in current_plan['additional_benefits']:
                    output.append(f"- {benefit}")
            
            output.append(f"\nFollow-up Schedule: {current_plan['followup_schedule']}")
        
        return "\n".join(output)




def main():
    """Run the medical advisor system."""
    # Load environment variables
    load_dotenv(os.path.join(Path(__file__).parent.parent, "config", ".env"))
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    advisor = ChromaMedicalAdvisor(api_key)
    
    print("\nWelcome to Medical Advisor")
    print("=" * 50)
    
    while True:
        # Get patient info
        patient_name = input("\nYour name (or 'anonymous'): ").strip() or "anonymous"
        location = input("Your location (or press Enter to skip): ").strip()
        
        condition = input("\nDescribe your medical concern (or 'quit' to exit): ").strip()
        
        if condition.lower() in ['quit', 'exit', 'q','escape']:
            break
            
        if not condition:
            continue
        
        try:
            # Get relevant questions
            print("\nTo better understand your situation, please answer these questions:")
            questions = advisor.get_relevant_questions(condition)
            
            # Gather responses
            responses = {}
            for question in questions:
                response = input(f"\n{question}\n> ").strip()
                responses[question] = response if response else "Not provided"
            
            # Generate assessment
            print("\nAnalyzing your responses...")
            assessment = advisor.analyze_responses(condition, responses)
            
            # Generate treatment plan
            print("Generating treatment plans...")
            plan = advisor.generate_treatment_plan(assessment)
            
            # Save detailed report
            json_path, txt_path = advisor.save_report(
                patient_name, condition, assessment, plan, responses
            )
            
            # Show report
            with open(txt_path, 'r', encoding='utf-8') as f:
                print("\n" + f.read())
            
            print(f"\nDetailed report saved to:")
            print(f"JSON: {json_path}")
            print(f"Text: {txt_path}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again with a different description.")
    
    print("\nThank you for using Medical Advisor!")

if __name__ == "__main__":
    main()