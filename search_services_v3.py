import os
from dotenv import load_dotenv
from ai_service_mapper_v3 import AIServiceMapper

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
    
    print("\nWelcome to the AI Medical Service Search")
    print("=" * 50)
    print("Type 'quit' to exit")
    print("\nExample queries:")
    print("- I need a chest x-ray for lung screening")
    print("- What tests do I need for lung cancer screening?")
    print("- Regular medical checkup cost")
    print("- My dad has been smoking and needs lung tests")
    
    while True:
        # Get query from user
        query = input("\nWhat service are you looking for? ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
        
        print("\nSearching for relevant services...")
        # Search for services
        services, recommendation = mapper.search(query)
        
        if services:
            # Group services by category
            radiology = [s for s in services if s["category"] == "RADIOLOGY"]
            general = [s for s in services if s["category"] == "GENERAL"]
            
            # Calculate total price range
            all_prices = [s["base_price"] for s in services]
            min_price = min(all_prices)
            max_price = max(all_prices)
            
            print(f"\nFound {len(services)} relevant services")
            print(f"Total price range: KES {min_price:.2f} - {max_price:.2f}")
            
            if radiology:
                print("\nDiagnostic Services:")
                for service in radiology:
                    print(f"- {service['description']} ({service['code']})")
                    print(f"  Price: KES {service['base_price']:.2f}")
                    
            if general:
                print("\nConsultation & Examination Services:")
                for service in general:
                    print(f"- {service['description']} ({service['code']})")
                    print(f"  Price: KES {service['base_price']:.2f}")
            
            print("\nRecommended Care Plan:")
            print(recommendation)
        else:
            print("\nNo services found matching your query.")
            print("Try using different terms or ask about a specific type of service.")
    
    mapper.close()
    print("\nThank you for using AI Medical Service Search!")

if __name__ == "__main__":
    main()
