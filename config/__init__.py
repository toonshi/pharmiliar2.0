import os
from dotenv import load_dotenv


 
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PANTRY_ID = os.getenv("PANTRY_ID")

print("configuration package loaded successfully")