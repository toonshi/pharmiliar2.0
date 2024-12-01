"""Price anomaly detection and analysis."""

import pandas as pd
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from .base import Department, Service, init_db

def analyze_price_anomalies():
    """Analyze and categorize price anomalies in the dataset."""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
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
        
        anomalies = {
            'fixed_non_ea': analyze_fixed_non_ea_rates(df),
            'price_differences': analyze_price_differences(df),
            'service_patterns': analyze_service_patterns(df),
            'data_errors': find_potential_errors(df)
        }
        
        return anomalies

def analyze_fixed_non_ea_rates(df):
    """Analyze services with fixed Non-EA rates."""
    common_rates = df['Non-EA Rate'].value_counts().head(10)
    five_ksh = df[df['Non-EA Rate'] == 5.0]
    
    return {
        'common_rates': common_rates,
        'five_ksh_count': len(five_ksh),
        'five_ksh_departments': five_ksh['Department'].value_counts(),
        'five_ksh_avg_normal': five_ksh.groupby('Department')['Normal Rate'].mean()
    }

def analyze_price_differences(df):
    """Analyze significant price differences between rate types."""
    large_diff = df[
        ((df['Special Rate'] / df['Normal Rate'] > 2) |
         (df['Special Rate'] / df['Normal Rate'] < 0.5)) &
        (df['Normal Rate'] > 100)
    ]
    
    return {
        'large_differences': large_diff[
            ['Description', 'Department', 'Normal Rate', 'Special Rate', 'Non-EA Rate']
        ].sort_values('Normal Rate', ascending=False),
        'dept_variation': df.groupby('Department')[['Special_Ratio', 'NonEA_Ratio']].agg(['mean', 'std'])
    }

def analyze_service_patterns(df):
    """Analyze price patterns in different types of services."""
    patterns = {}
    
    for term in ['scan', 'surgery', 'consultation', 'admission']:
        services = df[df['Description'].str.lower().str.contains(term, na=False)]
        if len(services) > 0:
            patterns[term] = {
                'count': len(services),
                'avg_normal': services['Normal Rate'].mean(),
                'avg_special': services['Special Rate'].mean(),
                'avg_non_ea': services['Non-EA Rate'].mean(),
                'price_range': (services['Normal Rate'].min(), services['Normal Rate'].max())
            }
    
    return patterns

def find_potential_errors(df):
    """Identify potential data entry errors."""
    # Large price differences
    large_diff = df[
        ((df['Special Rate'] / df['Normal Rate'] > 5) |
         (df['Normal Rate'] / df['Special Rate'] > 5)) &
        (df['Normal Rate'] > 100)
    ]
    
    # Unusually low prices for complex procedures
    complex_terms = ['surgery', 'scan', 'transplant', 'implant']
    low_complex = df[
        df['Description'].str.lower().str.contains('|'.join(complex_terms), na=False) &
        (df['Normal Rate'] < 1000)
    ]
    
    return {
        'large_differences': large_diff[
            ['Description', 'Department', 'Normal Rate', 'Special Rate', 'Non-EA Rate']
        ],
        'low_complex_prices': low_complex[
            ['Description', 'Department', 'Normal Rate']
        ]
    }

def print_anomaly_report(anomalies):
    """Print a detailed report of price anomalies."""
    print("=== Price Anomaly Analysis Report ===\n")
    
    print("1. Fixed Non-EA Rates")
    print("-----------------------")
    print("Most common Non-EA rates:")
    print(anomalies['fixed_non_ea']['common_rates'])
    print(f"\nServices with 5 KSH Non-EA rate: {anomalies['fixed_non_ea']['five_ksh_count']}")
    
    print("\n2. Significant Price Differences")
    print("-------------------------------")
    print("Top 5 largest price differences:")
    print(anomalies['price_differences']['large_differences'].head().to_string())
    
    print("\n3. Service Pattern Analysis")
    print("-------------------------")
    for service_type, stats in anomalies['service_patterns'].items():
        print(f"\n{service_type.title()} services:")
        print(f"Count: {stats['count']}")
        print(f"Average Normal Rate: {stats['avg_normal']:.2f}")
        print(f"Price Range: {stats['price_range'][0]:.2f} - {stats['price_range'][1]:.2f}")
    
    print("\n4. Potential Data Entry Errors")
    print("-----------------------------")
    print("Complex procedures with unusually low prices:")
    print(anomalies['data_errors']['low_complex_prices'].to_string())

if __name__ == '__main__':
    anomalies = analyze_price_anomalies()
    print_anomaly_report(anomalies)
