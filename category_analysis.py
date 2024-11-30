import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Read the cleaned data
df = pd.read_excel("cleaned_data.xlsx")
df.columns = ['Category', 'Code', 'Description', 'Price1', 'Price2', 'Rate', 'Reference']

def analyze_category(df, category):
    """Detailed analysis of a specific category"""
    cat_data = df[df['Category'] == category]
    
    print(f"\nAnalysis for Category: {category}")
    print(f"Number of services: {len(cat_data)}")
    
    # Price analysis
    prices = pd.to_numeric(cat_data['Price1'], errors='coerce')
    print("\nPrice Statistics:")
    print(f"Average Price: {prices.mean():.2f}")
    print(f"Median Price: {prices.median():.2f}")
    print(f"Min Price: {prices.min():.2f}")
    print(f"Max Price: {prices.max():.2f}")
    
    # Service analysis
    print("\nMost common services:")
    print(cat_data['Description'].value_counts().head())
    
    return cat_data

def price_comparison(df):
    """Compare prices across categories"""
    # Convert prices to numeric
    df['Price1'] = pd.to_numeric(df['Price1'], errors='coerce')
    
    # Calculate statistics by category
    category_stats = df.groupby('Category').agg({
        'Price1': ['count', 'mean', 'median', 'std', 'min', 'max']
    }).round(2)
    
    # Sort by average price
    category_stats = category_stats.sort_values(('Price1', 'mean'), ascending=False)
    
    print("\nCategory Price Comparison:")
    print(category_stats.head(10))
    
    return category_stats

def identify_outliers(df):
    """Identify unusually expensive or cheap services"""
    df['Price1'] = pd.to_numeric(df['Price1'], errors='coerce')
    
    # Calculate Z-scores for prices within each category
    df['price_zscore'] = df.groupby('Category')['Price1'].transform(
        lambda x: stats.zscore(x, nan_policy='omit')
    )
    
    # Find outliers (Z-score > 2 or < -2)
    outliers = df[abs(df['price_zscore']) > 2].sort_values('price_zscore', ascending=False)
    
    print("\nPotential Price Outliers:")
    print(outliers[['Category', 'Description', 'Price1', 'price_zscore']].head(10))
    
    return outliers

if __name__ == "__main__":
    # Perform overall category analysis
    print("Analyzing categories...")
    category_stats = price_comparison(df)
    
    # Analyze top 3 categories
    top_categories = df['Category'].value_counts().head(3).index
    for category in top_categories:
        analyze_category(df, category)
    
    # Find price outliers
    print("\nIdentifying price outliers...")
    outliers = identify_outliers(df)
    
    # Save results to Excel
    with pd.ExcelWriter('category_analysis_results.xlsx') as writer:
        category_stats.to_excel(writer, sheet_name='Category Statistics')
        outliers.to_excel(writer, sheet_name='Price Outliers')
    
    print("\nResults saved to category_analysis_results.xlsx")
