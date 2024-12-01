import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Read the cleaned data
df = pd.read_excel("cleaned_data.xlsx")

# Rename columns to meaningful names
df.columns = ['Category', 'Code', 'Description', 'Price1', 'Price2', 'Rate', 'Reference']

# Convert price columns to numeric, removing any currency symbols and commas
df['Price1'] = pd.to_numeric(df['Price1'].str.replace('KES', '').str.replace(',', ''), errors='coerce')
df['Price2'] = pd.to_numeric(df['Price2'].str.replace('KES', '').str.replace(',', ''), errors='coerce')

# Basic analysis
print("\nUnique Categories:")
print(df['Category'].value_counts().head(10))

print("\nPrice Statistics by Category:")
price_stats = df.groupby('Category')['Price1'].agg(['count', 'mean', 'min', 'max']).round(2)
print(price_stats.head(10))

# Additional statistics
print("\nOverall Price Statistics:")
print(df['Price1'].describe().round(2))

# Visualizations
plt.figure(figsize=(12, 6))
plt.title('Top 10 Categories by Average Price')
price_stats['mean'].sort_values(ascending=False).head(10).plot(kind='bar')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('price_analysis.png')
plt.close()

# Price distribution
plt.figure(figsize=(10, 6))
plt.title('Price Distribution (log scale)')
plt.hist(df['Price1'].dropna(), bins=50, log=True)
plt.xlabel('Price')
plt.ylabel('Count (log scale)')
plt.tight_layout()
plt.savefig('price_distribution.png')
plt.close()

# Save summary to Excel
summary_file = "price_analysis_summary.xlsx"
with pd.ExcelWriter(summary_file) as writer:
    price_stats.to_excel(writer, sheet_name='Price Statistics')
    df['Category'].value_counts().to_excel(writer, sheet_name='Category Counts')

print(f"\nAnalysis saved to {summary_file}")
print("Visualizations saved as price_analysis.png and price_distribution.png")
