import os
from dotenv import load_dotenv
import openai
import json
import sqlite3
import pandas as pd

# Load environment variables
load_dotenv()

# Setup OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def analyze_single_service(description, code, price):
    """Analyze a single medical service using OpenAI"""
    prompt = f"""
    Analyze this medical service from a hospital charge sheet:
    Service Code: {code}
    Description: {description}
    Price: KES {price}

    Provide a JSON response with the following information:
    1. department: The medical department this service belongs to
    2. service_type: Type of medical service (e.g., diagnostic, therapeutic, preventive)
    3. description_enriched: A clear, patient-friendly description of this service
    4. metadata:
       - complexity_level: Low, Medium, or High
       - typical_duration: Estimated time for the service
       - requires_fasting: Whether patient needs to fast
       - requires_admission: Whether it requires hospital admission
       - emergency_available: Whether available as emergency service
       - prerequisites: Any prerequisites for the service
    5. patient_preparation: What patients should know/do before the service
    6. typical_use_cases: Common medical situations requiring this service

    Format as valid JSON.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a medical service analyzer helping to categorize and explain hospital services."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse and format the response
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        print(f"Error analyzing service: {str(e)}")
        return None

def main():
    # Connect to database and get a sample service
    conn = sqlite3.connect('pharmiliar.db')
    query = "SELECT * FROM services LIMIT 1"
    service = pd.read_sql_query(query, conn).iloc[0]
    conn.close()
    
    print("\nAnalyzing sample service:")
    print(f"Description: {service['description']}")
    print(f"Code: {service['code']}")
    print(f"Price: {service['base_price']}")
    print("\nAnalyzing...")
    
    # Analyze the service
    analysis = analyze_single_service(
        service['description'],
        service['code'],
        service['base_price']
    )
    
    if analysis:
        print("\nAnalysis Results:")
        print(json.dumps(analysis, indent=2))
        
        # Save the analysis to a file
        with open('sample_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print("\nAnalysis saved to 'sample_analysis.json'")

if __name__ == "__main__":
    main()
