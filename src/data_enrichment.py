import pandas as pd
import sqlite3
import json

class DataEnrichment:
    def __init__(self):
        # Define standard medical departments
        self.departments = {
            'RADIOLOGY': ['x-ray', 'scan', 'ultrasound', 'mri', 'ct', 'imaging'],
            'LABORATORY': ['lab', 'test', 'blood', 'urine', 'sample', 'culture'],
            'PHARMACY': ['drug', 'medication', 'tablet', 'capsule', 'injection'],
            'CONSULTATION': ['consultation', 'visit', 'checkup', 'review'],
            'SURGERY': ['surgery', 'operation', 'procedure', 'incision'],
            'EMERGENCY': ['emergency', 'casualty', 'accident', 'trauma'],
            'MATERNITY': ['delivery', 'birth', 'prenatal', 'postnatal', 'obstetric'],
            'PEDIATRIC': ['child', 'baby', 'infant', 'pediatric'],
            'DENTAL': ['dental', 'tooth', 'teeth', 'oral'],
            'PHYSIOTHERAPY': ['physio', 'therapy', 'rehabilitation', 'exercise'],
            'OUTPATIENT': ['opd', 'outpatient', 'clinic'],
            'INPATIENT': ['admission', 'ward', 'bed', 'inpatient']
        }

        # Define service types
        self.service_types = {
            'DIAGNOSTIC': ['test', 'scan', 'x-ray', 'examination', 'analysis'],
            'THERAPEUTIC': ['treatment', 'therapy', 'surgery', 'procedure'],
            'PREVENTIVE': ['vaccination', 'immunization', 'screening', 'prevention'],
            'CONSULTATION': ['consultation', 'counseling', 'advisory'],
            'MEDICATION': ['drug', 'medicine', 'prescription'],
            'EMERGENCY': ['emergency', 'urgent', 'casualty']
        }

    def categorize_service(self, description):
        """Categorize a service into a department based on keywords"""
        description = str(description).lower()
        
        for dept, keywords in self.departments.items():
            if any(keyword in description for keyword in keywords):
                return dept
        return 'OTHER'

    def determine_service_type(self, description):
        """Determine the type of service based on keywords"""
        description = str(description).lower()
        
        for stype, keywords in self.service_types.items():
            if any(keyword in description for keyword in keywords):
                return stype
        return 'OTHER'

    def add_service_metadata(self, description):
        """Add additional metadata about the service"""
        metadata = {
            'is_emergency': any(word in str(description).lower() 
                              for word in ['emergency', 'urgent', 'casualty']),
            'requires_admission': any(word in str(description).lower() 
                                    for word in ['admission', 'inpatient', 'ward']),
            'is_outpatient': any(word in str(description).lower() 
                                for word in ['outpatient', 'opd', 'clinic']),
            'needs_appointment': not any(word in str(description).lower() 
                                       for word in ['emergency', 'urgent', 'casualty'])
        }
        return metadata

    def enrich_data(self):
        """Enrich the existing data with categories and metadata"""
        # Connect to database
        conn = sqlite3.connect('pharmiliar.db')
        
        # Read current data
        query = "SELECT * FROM services"
        df = pd.read_sql_query(query, conn)
        
        # Add enriched data
        df['department'] = df['description'].apply(self.categorize_service)
        df['service_type'] = df['description'].apply(self.determine_service_type)
        df['metadata'] = df['description'].apply(self.add_service_metadata)
        
        # Create new enriched table
        df.to_sql('enriched_services', conn, if_exists='replace', index=False)
        
        # Create summary
        department_summary = df.groupby('department').agg({
            'base_price': ['count', 'mean', 'min', 'max'],
            'description': lambda x: list(set(x))[:5]  # Sample services
        }).round(2)
        
        # Save summary to Excel
        with pd.ExcelWriter('enriched_data_summary.xlsx') as writer:
            department_summary.to_excel(writer, sheet_name='Department Summary')
            
            # Service type summary
            df.groupby('service_type').size().to_excel(writer, sheet_name='Service Types')
            
            # Price ranges by department
            price_ranges = df.pivot_table(
                values='base_price',
                index='department',
                aggfunc=['min', 'max', 'mean', 'count']
            ).round(2)
            price_ranges.to_excel(writer, sheet_name='Price Ranges')
        
        print("\nData enrichment complete!")
        print("\nDepartment Summary:")
        print(department_summary)
        
        conn.close()
        return df

if __name__ == "__main__":
    enricher = DataEnrichment()
    enriched_data = enricher.enrich_data()
    
    print("\nSample insights:")
    print(f"Number of departments: {len(enriched_data['department'].unique())}")
    print("\nMost expensive departments:")
    dept_prices = enriched_data.groupby('department')['base_price'].mean().sort_values(ascending=False)
    print(dept_prices.head())
    
    print("\nService type distribution:")
    print(enriched_data['service_type'].value_counts())
