"""
Data Cleaning Module

Cleans and standardizes hospital service data:
- Removes empty rows and duplicates
- Standardizes price formats
- Cleans text fields
- Validates data types
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict

class DataCleaner:
    def __init__(self, config: Dict):
        self.config = config['cleaning']
        self.logger = logging.getLogger(__name__)
        
    def clean_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean price columns according to config"""
        for col in self.config['price_columns']:
            if col in df.columns:
                # Remove currency symbols and commas
                df[col] = df[col].astype(str)
                df[col] = df[col].str.replace('KES', '')
                df[col] = df[col].str.replace(',', '')
                
                # Convert to float, replacing errors with default value
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(self.config['price_cleaning']['default_value'])
                
        return df
        
    def clean_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean text columns"""
        text_columns = df.select_dtypes(include=['object']).columns
        
        for col in text_columns:
            if self.config['strip_whitespace']:
                df[col] = df[col].str.strip()
            
            if self.config['standardize_case']:
                df[col] = df[col].str.title()
                
        return df
        
    def remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove empty and invalid rows"""
        if self.config['remove_empty_rows']:
            # Remove rows where all values are NaN
            df = df.dropna(how='all')
            
            # Remove rows where required columns are NaN
            required_cols = self.config['extraction']['required_columns']
            df = df.dropna(subset=required_cols)
            
        return df.reset_index(drop=True)
        
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run all cleaning steps"""
        self.logger.info("Starting data cleaning...")
        initial_rows = len(df)
        
        # Clean prices
        df = self.clean_prices(df)
        
        # Clean text fields
        df = self.clean_text(df)
        
        # Remove invalid rows
        df = self.remove_invalid_rows(df)
        
        # Remove duplicates
        df = df.drop_duplicates().reset_index(drop=True)
        
        final_rows = len(df)
        self.logger.info(f"Cleaning complete. Rows: {initial_rows} -> {final_rows}")
        
        return df
