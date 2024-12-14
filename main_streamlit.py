import os
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
from datetime import datetime
import asyncio
import src
from notes.basket_manager import add_to_basket_async, load_user_basket, edit_illness_async, delete_illness_async

from src import medical_advisor

# Load environment variables from the .env file
dotenv_path = Path(".env")
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    st.warning("Warning: .env file not found. Ensure it's in the root directory.")

# Retrieve the OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Error: OPENAI_API_KEY not found. Ensure it's correctly set in the .env file.")

# Function to format currency
def format_currency(amount: float) -> str:
    """Format amount as KSH currency."""
    return f"KSH {amount:,.2f}"

# Function to print service categories
def print_category(services: list, category: str):
    """Print services for a category."""
    if not services:
        return

    st.write(f"\n### {category}:")
    st.write("-" * 80)

    # Group services by department
    dept_services = {}
    for service in services:
        dept = service["department"]
        if dept not in dept_services:
            dept_services[dept] = []
        dept_services[dept].append(service)

    # Print services by department
    for dept, dept_list in sorted(dept_services.items()):
        st.write(f"\n**{dept}:**")
        for service in dept_list:
            st.write(f"- {service['description']}")
            st.write(f"  Code: {service['code']}")
            st.write(f"  Price: {format_currency(service['price'])}")

# Function to print service recommendations
def print_services(services: dict):
    """Print formatted service recommendations."""
    st.write("\n### Recommended Medical Services")
    st.write("=" * 80)

    # Print services by category
    print_category(services["categories"]["diagnostic"], "Diagnostic Tests")
    print_category(services["categories"]["treatment"], "Treatments")
    print_category(services["categories"]["monitoring"], "Monitoring Services")

    st.write("=" * 80)
    st.write(f"Total Estimated Cost: {format_currency(services['total_cost'])}")
    st.write(f"Departments Involved: {', '.join(services['departments'])}")

# Streamlit app starts here
st.title("Medical Consultation System")

# Select page for consultation or illness notes
page = st.sidebar.selectbox("Select Page", ("Consultation", "Illness Notes"))

if page == "Consultation":
    try:
        # Input symptoms for medical consultation
        symptoms = st.text_area("Enter symptoms:", "Headache, burning sensation when urinating, sores on the penis")

        if st.button("Analyze Symptoms"):
            # Initialize medical advisor
            st.write("\nInitializing medical advisor system...")
            advisor = medical_advisor.Advisor(api_key)

            # Get medical analysis
            analysis = advisor.analyze_symptoms(symptoms)
            st.write("\n### Medical Analysis:")
            st.write("=" * 80)
            st.write(analysis["analysis"])

            # Get treatment plan
            st.write("\nGenerating treatment plan...")
            plan = advisor.get_treatment_plan("STI", "standard")

            # Print service recommendations
            print_services(plan["available_services"])

            # Print treatment plan
            st.write("\n### Recommended Treatment Plan:")
            st.write("=" * 80)
            st.write(plan["treatment_plan"])

            # Save consultation
            consultation_data = {
                "symptoms": symptoms,
                "analysis": analysis,
                "treatment_plan": plan,
                "consultation_date": datetime.now().isoformat(),
            }

            report_path = advisor.save_consultation(consultation_data)
            st.write(f"\nDetailed consultation report saved to: {report_path}")

    except Exception as e:
        st.error(f"Error during consultation: {str(e)}")

elif page == "Illness Notes":
    # Handle Illness Notes (as in your original code, with asyncio calls)
    # Add your existing illness notes logic here, unchanged from your provided script
    pass
