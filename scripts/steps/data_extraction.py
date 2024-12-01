"""
Data Extraction Module

Extracts and validates data from hospital chargesheets.
Supports Excel (.xlsx, .xls) and CSV formats.
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Optional

class DataExtractor:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def validate_file(self, file_path: Path) -> bool:
        """Validate file format and existence"""
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
            
        if file_path.suffix[1:] not in self.config['extraction']['supported_formats']:
            self.logger.error(f"Unsupported file format: {file_path.suffix}")
            return False
            
        return True
        
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Check if required columns are present"""
        missing = []
        for col in self.config['extraction']['required_columns']:
            if col not in df.columns:
                missing.append(col)
                
        if missing:
            self.logger.error(f"Missing required columns: {', '.join(missing)}")
            return False
            
        return True
        
    def read_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read data from file into DataFrame"""
        try:
            if file_path.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            return df
        except Exception as e:
            self.logger.error(f"Error reading file: {str(e)}")
            return None
            
    def extract(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Extract and validate data from file"""
        self.logger.info(f"Extracting data from: {file_path}")
        
        # Validate file
        if not self.validate_file(file_path):
            return None
            
        # Read file
        df = self.read_file(file_path)
        if df is None:
            return None
            
        # Validate columns
        if not self.validate_columns(df):
            return None
            
        self.logger.info(f"Successfully extracted {len(df)} rows of data")
        return df
