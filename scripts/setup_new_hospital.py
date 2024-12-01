"""
Hospital Data Setup Pipeline

This script orchestrates the process of setting up a new hospital's data:
1. Extracts data from chargesheet
2. Cleans and standardizes the data
3. Enriches with metadata and categories
4. Sets up database and loads data
5. Generates initial analysis
"""

import os
import sys
from pathlib import Path
import argparse
from datetime import datetime
import yaml
import logging

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import processing modules
from src.data_processing.data_cleaning import clean_data
from src.data_processing.data_enrichment import DataEnrichment
from src.data_processing.migrate_data import migrate_data

def setup_logging(hospital_name):
    """Setup logging for the pipeline"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"setup_{hospital_name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_config():
    """Load hospital configuration"""
    config_path = Path(__file__).parent / "config" / "hospital_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path) as f:
        return yaml.safe_load(f)

def extract_data(input_file, hospital_name, logger):
    """Extract data from chargesheet"""
    logger.info(f"Extracting data from: {input_file}")
    
    # Create output directories if they don't exist
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy and rename input file
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d")
    raw_file = raw_dir / f"{hospital_name}_{timestamp}.xlsx"
    shutil.copy2(input_file, raw_file)
    
    logger.info(f"Raw data saved to: {raw_file}")
    return raw_file

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Setup new hospital data")
    parser.add_argument("input_file", help="Path to hospital chargesheet")
    parser.add_argument("hospital_name", help="Name of the hospital")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.hospital_name)
    logger.info(f"Starting setup for hospital: {args.hospital_name}")
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Loaded configuration")
        
        # Extract data
        raw_file = extract_data(args.input_file, args.hospital_name, logger)
        
        # Clean data
        logger.info("Cleaning data...")
        cleaned_data = clean_data(raw_file)
        
        # Enrich data
        logger.info("Enriching data...")
        enricher = DataEnrichment()
        enriched_data = enricher.enrich_data(cleaned_data)
        
        # Setup database
        logger.info("Setting up database...")
        db_path = project_root / "data" / "processed" / f"{args.hospital_name.lower()}_services.db"
        migrate_data(enriched_data, str(db_path))
        
        # Generate initial analysis
        logger.info("Generating analysis...")
        from src.analysis.price_anomalies import analyze_price_anomalies
        analyze_price_anomalies()
        
        logger.info("Setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
