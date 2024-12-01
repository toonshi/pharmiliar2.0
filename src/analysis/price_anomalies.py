import pandas as pd
import numpy as np
from sqlalchemy import func
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Department, Service
from queries import get_session

def analyze_price_anomalies():
    """Analyze and categorize price anomalies in the dataset"""
    with get_session() as session:
        # Get all pricing data
        query = session.query(
            Service.code,
            Service.description,
            Department.name.label('department'),
            Service.normal_rate,
            Service.special_rate,
            Service.non_ea_rate
        ).join(Department)\
         .filter(
            Service.normal_rate > 0,
            Service.special_rate > 0,
            Service.non_ea_rate > 0
         )
        
        df = pd.DataFrame(query.all(), 
                         columns=['Code', 'Description', 'Department', 
                                'Normal Rate', 'Special Rate', 'Non-EA Rate'])
        
        # Calculate price ratios
        df['Special_Ratio'] = df['Special Rate'] / df['Normal Rate']
        df['NonEA_Ratio'] = df['Non-EA Rate'] / df['Normal Rate']
        
        # 1. Identify common Non-EA rates
        print("Common Non-EA Rates:")
        common_nonea = df['Non-EA Rate'].value_counts().head(10)
        print(common_nonea)
        
        # 2. Analyze services with 5 KSH Non-EA rate
        print("\nAnalyzing services with 5 KSH Non-EA rate:")
        five_ksh = df[df['Non-EA Rate'] == 5.0]
        print(f"\nTotal services with 5 KSH Non-EA rate: {len(five_ksh)}")
        print("\nDepartment distribution:")
        print(five_ksh['Department'].value_counts().head())
        
        # Calculate average normal rate for these services
        print("\nAverage Normal Rate for services with 5 KSH Non-EA rate:")
        print(five_ksh.groupby('Department')['Normal Rate'].mean().sort_values(ascending=False).head())
        
        # 3. Identify services with identical rates across all tiers
        identical_rates = df[
            (df['Special Rate'] == df['Normal Rate']) & 
            (df['Non-EA Rate'] == df['Normal Rate'])
        ]
        print(f"\nServices with identical rates across all tiers: {len(identical_rates)}")
        
        # 4. Find services where Special Rate < Normal Rate
        lower_special = df[df['Special Rate'] < df['Normal Rate']]
        print("\nServices where Special Rate is lower than Normal Rate:")
        print(lower_special[['Description', 'Department', 'Normal Rate', 'Special Rate']]\
            .sort_values('Normal Rate', ascending=False)\
            .head())
        
        # 5. Analyze price patterns by service type
        print("\nAnalyzing price patterns in service descriptions:")
        
        # Common words in descriptions
        common_words = pd.Series(' '.join(df['Description'].str.lower()).split()).value_counts()
        print("\nMost common words in service descriptions:")
        print(common_words.head(10))
        
        # Price patterns for common service types
        for word in ['scan', 'surgery', 'consultation', 'admission']:
            services = df[df['Description'].str.lower().str.contains(word, na=False)]
            if len(services) > 0:
                print(f"\nPrice statistics for services containing '{word}':")
                print(f"Count: {len(services)}")
                print(f"Average Normal Rate: {services['Normal Rate'].mean():.2f}")
                print(f"Average Special Rate: {services['Special Rate'].mean():.2f}")
                print(f"Average Non-EA Rate: {services['Non-EA Rate'].mean():.2f}")
        
        # 6. Identify potential data entry errors
        print("\nPotential data entry errors:")
        
        # Large price differences between tiers
        large_diff = df[
            ((df['Special Rate'] / df['Normal Rate'] > 5) |
             (df['Normal Rate'] / df['Special Rate'] > 5)) &
            (df['Normal Rate'] > 100)  # Filter out very low prices
        ]
        
        if len(large_diff) > 0:
            print("\nServices with large price differences between tiers:")
            print(large_diff[['Description', 'Department', 'Normal Rate', 
                            'Special Rate', 'Non-EA Rate']].to_string())
        
        # Unusually low prices for complex procedures
        complex_terms = ['surgery', 'scan', 'transplant', 'implant']
        low_complex = df[
            df['Description'].str.lower().str.contains('|'.join(complex_terms), na=False) &
            (df['Normal Rate'] < 1000)
        ]
        
        if len(low_complex) > 0:
            print("\nComplex procedures with unusually low prices:")
            print(low_complex[['Description', 'Department', 'Normal Rate']].to_string())

if __name__ == '__main__':
    analyze_price_anomalies()
