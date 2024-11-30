import os
from dotenv import load_dotenv
from ai_service_mapper_v5 import AIServiceMapper

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
    print("\nNew Features:")
    print("✓ Smart caching for faster responses")
    print("✓ Related service suggestions")
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
            # Group services by category
            radiology = [s for s in services if s["category"] == "RADIOLOGY"]
            general = [s for s in services if s["category"] == "GENERAL"]
            
            # Calculate price ranges
            all_prices = [s["base_price"] for s in services]
            min_price = min(all_prices)
            max_price = max(all_prices)
            
            print(f"\nFound {len(services)} relevant services")
            print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
            
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
            
            # Calculate estimated total cost for recommended services
            recommended_services = radiology[:1] + general[:1]  # Usually 1 diagnostic + 1 consultation
            if recommended_services:
                total_cost = sum(s["base_price"] for s in recommended_services)
                print(f"\nEstimated initial cost: KES {total_cost:.2f}")
                print("Note: Additional costs may apply based on findings")
        else:
            print("\nNo services found matching your query.")
            print("Try using different terms or ask about a specific type of service.")
    
    mapper.close()
    print("\nThank you for using the Enhanced Medical Service Search!")

if __name__ == "__main__":
    main()
