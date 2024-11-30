import os
from dotenv import load_dotenv
from ai_service_mapper import AIServiceMapper

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
    
    print("\nWelcome to the AI Service Search")
    print("=" * 50)
    print("Type 'quit' to exit")
    
    while True:
        # Get query from user
        query = input("\nWhat service are you looking for? ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
        
        # Search for services
        services, recommendation = mapper.search(query)
        
        if services:
            min_price = min(s["base_price"] for s in services)
            max_price = max(s["base_price"] for s in services)
            print(f"\nFound {len(services)} services")
            print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
            
            for service in services:
                print(f"\n- {service['description']} ({service['code']})")
                print(f"  Price: KES {service['base_price']:.2f}")
            
            print("\nRecommendation:")
            print(recommendation)
        else:
            print("\nNo services found matching your query.")
            print("Try using different terms or ask about a specific type of service.")
    
    mapper.close()
    print("\nThank you for using AI Service Search!")

if __name__ == "__main__":
    main()
