import os
from dotenv import load_dotenv
from ai_service_mapper_v5 import AIServiceMapper

def filter_relevant_services(services):
    """Filter and sort services relevant to lung screening."""
    # Define relevant and excluded terms
    lung_terms = ["chest", "lung", "ct scan", "thorax"]
    consult_terms = ["consult", "medical exam", "check"]
    excluded = ["vaginal", "eye", "gynoe", "cervical", "skull", "gloves"]
    
    # Filter radiology services
    radiology = [s for s in services 
                if s["category"] == "RADIOLOGY" 
                and any(term in s["description"].lower() for term in lung_terms)
                and not any(term in s["description"].lower() for term in excluded)]
    
    # Filter consultation services
    general = [s for s in services 
              if s["category"] == "GENERAL"
              and any(term in s["description"].lower() for term in consult_terms)
              and not any(term in s["description"].lower() for term in excluded)]
    
    # Sort radiology by relevance (chest x-rays first, then CT scans)
    radiology.sort(key=lambda x: (
        "chest" not in x["description"].lower(),
        "ct scan" not in x["description"].lower(),
        x["base_price"]
    ))
    
    # Sort consultations by price
    general.sort(key=lambda x: x["base_price"])
    
    return radiology, general

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Initialize mapper
    mapper = AIServiceMapper(api_key)
    
    print("\nWelcome to the Enhanced Medical Service Search")
    print("=" * 50)
    print("Type 'quit' to exit")
    print("\nExample queries:")
    print("- I need a chest x-ray for lung screening")
    print("- My dad has been smoking and needs lung tests")
    print("- Looking for cancer screening options")
    print("- Regular medical checkup cost")
    print("\nFeatures:")
    print("✓ Smart service filtering")
    print("✓ Accurate cost estimates")
    print("✓ Priority-based recommendations")
    print("✓ Comprehensive care plans")
    
    while True:
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
            # Filter and group relevant services
            radiology, general = filter_relevant_services(services)
            relevant_services = radiology + general
            
            if relevant_services:
                # Calculate price ranges
                all_prices = [s["base_price"] for s in relevant_services]
                min_price = min(all_prices)
                max_price = max(all_prices)
                
                print(f"\nFound {len(relevant_services)} relevant services")
                print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
                
                if radiology:
                    print("\nDiagnostic Services (in order of recommendation):")
                    for service in radiology:
                        print(f"- {service['description']} ({service['code']})")
                        print(f"  Price: KES {service['base_price']:.2f}")
                        
                if general:
                    print("\nConsultation Services:")
                    for service in general:
                        print(f"- {service['description']} ({service['code']})")
                        print(f"  Price: KES {service['base_price']:.2f}")
                
                print("\nRecommended Care Plan:")
                print(recommendation)
                
                # Calculate initial service package
                initial_services = []
                if general:  # Add primary consultation
                    initial_services.append(general[0])
                if radiology:  # Add primary diagnostic
                    initial_services.append(radiology[0])
                
                if initial_services:
                    total_cost = sum(s["base_price"] for s in initial_services)
                    print("\nRecommended Initial Services:")
                    for service in initial_services:
                        print(f"- {service['description']}: KES {service['base_price']:.2f}")
                    print(f"\nTotal estimated initial cost: KES {total_cost:.2f}")
                    print("\nNote: This covers initial screening. Additional tests or")
                    print("follow-up consultations may be recommended based on findings.")
                    
                    if len(radiology) > 1:
                        print("\nPotential follow-up diagnostics if needed:")
                        for service in radiology[1:]:
                            print(f"- {service['description']}: KES {service['base_price']:.2f}")
            else:
                print("\nNo specific lung screening services found.")
                print("Try using different terms or ask about a specific type of service.")
        else:
            print("\nNo services found matching your query.")
            print("Try using different terms or ask about a specific type of service.")
    
    mapper.close()
    print("\nThank you for using the Enhanced Medical Service Search!")

if __name__ == "__main__":
    main()
