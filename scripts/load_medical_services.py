"""Script to load medical services into ChromaDB."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from medical_advisor.service_loader import ServiceLoader

def main():
    # Load environment variables
    env_path = project_root / "config" / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        return
        
    load_dotenv(env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print(f"Error: OPENAI_API_KEY not found in {env_path}")
        return
    
    try:
        # Initialize loader and load services
        print("\nInitializing service loader...")
        loader = ServiceLoader(api_key)
        
        print("\nLoading medical services...")
        num_services = loader.load_services()
        
        print(f"\nSuccess! Loaded {num_services} medical services into the database.")
        
    except Exception as e:
        print(f"\nError loading services: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()