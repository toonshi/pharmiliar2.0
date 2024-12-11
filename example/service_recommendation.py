import sys
import os
from datetime import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import OPENAI_API_KEY
from src import medical_advisor 


api_key = OPENAI_API_KEY
advisor = medical_advisor.Advisor(api_key)
plan = advisor.get_service_recommendations("fever","standard")

if __name__ == "__main__":
  print (plan)





      
    
    
    
    
