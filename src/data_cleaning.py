import os
from pathlib import Path
import pandas as pd
import numpy as np

# Get project root directory
project_root = Path(__file__).parent.parent

# Load the extracted data for cleaning
data_df = pd.read_excel(os.path.join(project_root, "data", "raw", "extracted_data.xlsx"))

# Display original shape
print("Original shape:", data_df.shape)
print("\nFirst few rows before cleaning:")
print(data_df.head())

# Drop rows or columns that are completely empty
cleaned_df = data_df.dropna(how='all').reset_index(drop=True)

# Replace any remaining NaN values with empty string
cleaned_df = cleaned_df.fillna("")

# Clean whitespace from all string columns
for column in cleaned_df.columns:
    if cleaned_df[column].dtype == object:
        cleaned_df[column] = cleaned_df[column].str.strip()

# Remove any duplicate rows
cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)

# Display cleaning results
print("\nShape after cleaning:", cleaned_df.shape)
print("\nFirst few rows after cleaning:")
print(cleaned_df.head())

# Save cleaned version for further processing
cleaned_file = os.path.join(project_root, "data", "processed", "cleaned_data.xlsx")
cleaned_df.to_excel(cleaned_file, index=False)
print(f"\nCleaned data saved to {cleaned_file}")
