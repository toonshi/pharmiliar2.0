import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import local modules
from src.service_mapper import OpenAIServiceMapper

def format_currency(amount: float) -> str:
    """Format currency with thousands separator."""
    return f"KES {amount:,.2f}"

def main():
    # Load environment variables from config/.env
    load_dotenv(os.path.join(project_root, "config", ".env"))
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Initialize mapper
    print("\nInitializing service database...")
    mapper = OpenAIServiceMapper(api_key)
    
    print("\nWelcome to the Smart Medical Service Search")
    print("=" * 50)
    print("Type 'quit' to exit")
    print("\nExample queries:")
    print("- I need a chest x-ray for lung screening")
    print("- My dad has been smoking and needs lung tests")
    print("- Looking for cancer screening options")
    print("- Regular medical checkup cost")
    print("\nFeatures:")
    print("✓ AI-powered service matching")
    print("✓ Accurate cost estimates")
    print("✓ Personalized recommendations")
    print("✓ Priority-based care plans")
    
    while True:
        try:
            # Get query from user
            query = input("\nWhat service are you looking for? ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
            
            print("\nAnalyzing your query...")
            # Search for services
            services, recommendation = mapper.search(query)
            
            if services:
                # Group services by category
                diagnostics = [s for s in services if s["category"] == "RADIOLOGY"]
                consultations = [s for s in services if s["category"] == "GENERAL"]
                
                # Calculate price ranges for relevant services
                all_prices = [s["base_price"] for s in services]
                min_price = min(all_prices)
                max_price = max(all_prices)
                
                print(f"\nFound {len(services)} relevant services")
                print(f"Price range: {format_currency(min_price)} - {format_currency(max_price)}")
                
                if diagnostics:
                    print("\nDiagnostic Services (by relevance):")
                    for service in diagnostics:
                        relevance = service.get("relevance", 0) * 100
                        print(f"- {service['description']} ({service['id']})")
                        print(f"  Price: {format_currency(service['base_price'])}")
                        print(f"  Match: {relevance:.1f}%")
                        
                if consultations:
                    print("\nConsultation Services:")
                    for service in consultations:
                        print(f"- {service['description']} ({service['id']})")
                        print(f"  Price: {format_currency(service['base_price'])}")
                
                print("\nRecommended Care Plan:")
                print(recommendation)
                
                # Calculate initial package cost
                initial_services = []
                if consultations:
                    initial_services.append(consultations[0])
                if diagnostics:
                    initial_services.append(diagnostics[0])
                
                if initial_services:
                    total_cost = sum(s["base_price"] for s in initial_services)
                    print("\nRecommended Initial Package:")
                    for service in initial_services:
                        print(f"- {service['description']}: {format_currency(service['base_price'])}")
                    print(f"\nTotal estimated initial cost: {format_currency(total_cost)}")
                    print("\nNote: This covers initial screening. Additional tests or")
                    print("follow-up consultations may be recommended based on findings.")
                    
                    if len(diagnostics) > 1:
                        print("\nAdditional diagnostic options if needed:")
                        for service in diagnostics[1:]:
                            print(f"- {service['description']}: {format_currency(service['base_price'])}")
            else:
                print("\nNo specific services found matching your needs.")
                print("Try describing your health concerns or the type of screening you're looking for.")
                
        except Exception as e:
            print(f"\nError processing query: {str(e)}")
            print("Please try again or contact support if the issue persists.")
    
    mapper.close()
    print("\nThank you for using the Smart Medical Service Search!")

if __name__ == "__main__":
    main()
