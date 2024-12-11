import sys
import os
from datetime import datetime


# Add the root folder to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import OPENAI_API_KEY
from src import medical_advisor 

def format_currency(amount: float) -> str:
    """Format amount as KSH currency."""
    return f"KSH {amount:,.2f}"

def print_category(services: list, category: str):
    """Print services for a category."""
    if not services:
        return
        
    print(f"\n{category}:")
    print("-" * 80)
    
    # Group services by department
    dept_services = {}
    for service in services:
        dept = service["department"]
        if dept not in dept_services:
            dept_services[dept] = []
        dept_services[dept].append(service)
    
    # Print services by department
    for dept, dept_list in sorted(dept_services.items()):
        print(f"\n{dept}:")
        for service in dept_list:
            print(f"\n• {service['description']}")
            print(f"  Code: {service['code']}")
            print(f"  Price: {format_currency(service['price'])}")

def print_services(services: dict):
    """Print formatted service recommendations."""
    print("\nRecommended Medical Services")
    print("=" * 80)
    
    # Print services by category
    print_category(services["categories"]["diagnostic"], "Diagnostic Tests")
    print_category(services["categories"]["treatment"], "Treatments")
    print_category(services["categories"]["monitoring"], "Monitoring Services")
    
    print("\n" + "=" * 80)
    print(f"Total Estimated Cost: {format_currency(services['total_cost'])}")
    print(f"Departments Involved: {', '.join(services['departments'])}")

def main():
    # Load environment variables


    api_key = OPENAI_API_KEY
    
    if not api_key:
        print(f"Error: OPENAI_API_KEY not found ")
        return
    
    try:
        # Initialize medical advisor
        print("\nInitializing medical advisor system...")
        advisor = medical_advisor.Advisor(api_key)
        
        # Example consultation
        symptoms = "Headache,burning sensation when urinating,sores on the penis"
        print(f"\nAnalyzing symptoms: {symptoms}")
        print("=" * 80)
        
        # Get medical analysis
        analysis = advisor.analyze_symptoms(symptoms)
        print("\nMedical Analysis:")
        print("=" * 80)
        print(analysis["analysis"])
        
        # Get treatment plan
        print("\nGenerating treatment plan...")
        plan = advisor.get_treatment_plan("STI", "standard")
        
        # Print service recommendations
        print_services(plan["available_services"])
        
        # Print treatment plan
        print("\nRecommended Treatment Plan:")
        print("=" * 80)
        print(plan["treatment_plan"])
        
        # Save consultation
        consultation_data = {
            "symptoms": symptoms,
            "analysis": analysis,
            "treatment_plan": plan,
            "consultation_date": datetime.now().isoformat()
        }
        
        report_path = advisor.save_consultation(consultation_data)
        print(f"\nDetailed consultation report saved to: {report_path}")
        
    except Exception as e:
        print(f"\nError during consultation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
