"""Script to load medical services into the database."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from medical_advisor import MedicalAdvisor
from medical_advisor.config import ENV_PATH

def main():
    # Load environment variables
    load_dotenv(ENV_PATH)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print(f"Error: OPENAI_API_KEY not found in {ENV_PATH}")
        return
    
    # Initialize medical advisor and load services
    advisor = MedicalAdvisor(api_key)
    print("\nLoading medical services into database...")
    advisor.db.load_services()

if __name__ == "__main__":
    main()
