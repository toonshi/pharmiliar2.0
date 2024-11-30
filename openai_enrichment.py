import pandas as pd
import sqlite3
import openai
import json
from time import sleep

class OpenAIEnrichment:
    def __init__(self, api_key):
        openai.api_key = api_key
        
    def analyze_service(self, description, code, price):
        """Use OpenAI to analyze and categorize a medical service"""
        prompt = f"""
        Analyze this medical service from a hospital charge sheet:
        Service Code: {code}
        Description: {description}
        Price: {price}

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
            
            # Parse the response as JSON
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing service {code}: {str(e)}")
            return None

    def enrich_data(self, batch_size=10):
        """Enrich the hospital services data using OpenAI"""
        # Connect to database
        conn = sqlite3.connect('pharmiliar.db')
        
        # Read current data
        query = "SELECT * FROM services"
        df = pd.read_sql_query(query, conn)
        
        enriched_data = []
        
        print(f"Processing {len(df)} services...")
        
        # Process in batches to avoid rate limits
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}...")
            
            for _, row in batch.iterrows():
                analysis = self.analyze_service(
                    row['description'],
                    row['code'],
                    row['base_price']
                )
                
                if analysis:
                    enriched_data.append({
                        'service_id': row['id'],
                        'original_description': row['description'],
                        'code': row['code'],
                        'base_price': row['base_price'],
                        **analysis
                    })
                
            # Sleep to respect API rate limits
            sleep(1)
        
        # Convert to DataFrame
        enriched_df = pd.DataFrame(enriched_data)
        
        # Save to database
        enriched_df.to_sql('enriched_services_ai', conn, if_exists='replace', index=False)
        
        # Create summary reports
        self.generate_reports(enriched_df)
        
        conn.close()
        return enriched_df
    
    def generate_reports(self, df):
        """Generate detailed analysis reports"""
        with pd.ExcelWriter('ai_enriched_analysis.xlsx') as writer:
            # Department summary
            dept_summary = df.groupby('department').agg({
                'base_price': ['count', 'mean', 'min', 'max'],
                'original_description': lambda x: list(set(x))[:5]
            }).round(2)
            dept_summary.to_excel(writer, sheet_name='Department Summary')
            
            # Service type analysis
            service_types = df.groupby('service_type').agg({
                'base_price': ['count', 'mean', 'min', 'max']
            }).round(2)
            service_types.to_excel(writer, sheet_name='Service Types')
            
            # Complexity analysis
            complexity = df.groupby(['department', 'metadata.complexity_level']).size().unstack()
            complexity.to_excel(writer, sheet_name='Complexity Analysis')
            
            # Emergency services
            emergency = df[df['metadata.emergency_available'] == True]
            emergency.to_excel(writer, sheet_name='Emergency Services')

def main():
    api_key = input("Enter your OpenAI API key: ")
    enricher = OpenAIEnrichment(api_key)
    
    print("Starting data enrichment...")
    enriched_data = enricher.enrich_data()
    
    print("\nEnrichment complete! Summary of results:")
    print(f"Total services processed: {len(enriched_data)}")
    print("\nDepartments found:")
    print(enriched_data['department'].value_counts())
    
    print("\nService types:")
    print(enriched_data['service_type'].value_counts())
    
    print("\nDetailed analysis saved to 'ai_enriched_analysis.xlsx'")

if __name__ == "__main__":
    main()
