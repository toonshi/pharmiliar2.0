import os
import streamlit as st
from pathlib import Path
from datetime import datetime
import asyncio
import src
from  config import OPENAI_API_KEY
from notes.basket_manager import add_to_basket_async, load_user_basket, edit_illness_async, delete_illness_async

# Add src directory to Python path
# project_root = Path(__file__).parent.parent

from src import medical_advisor


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

# Streamlit pages
st.title("Medical Consultation System")

# Select page for consultation or illness notes
page = st.sidebar.selectbox("Select Page", ("Consultation", "Illness Notes"))

if page == "Consultation":
    # Load environment variables for API
   

    api_key = OPENAI_API_KEY
    
    if not api_key:
        st.error(f"Error: OPENAI_API_KEY not found")
    
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
                "consultation_date": datetime.now().isoformat()
            }
            
            report_path = advisor.save_consultation(consultation_data)
            st.write(f"\nDetailed consultation report saved to: {report_path}")
    
    except Exception as e:
        st.error(f"Error during consultation: {str(e)}")

elif page == "Illness Notes":
    # Handle Illness Notes
    st.sidebar.header("Previous Illnesses")

    # Set up the username in session state if it's not set
    if 'username' not in st.session_state:
        st.session_state.username = ''

    # Input for the username (if it's not already set)
    if st.session_state.username == '':
        st.session_state.username = st.sidebar.text_input("Username", "")

    # Display illnesses in the sidebar with options to edit or delete
    async def display_illnesses():
        username = st.session_state.username
        if not username:
            st.sidebar.write("Please enter a username first.")
            return

        try:
            data = await load_user_basket(username)
            if data:
                for illness, appointments in data["illnesses"].items():
                    st.sidebar.subheader(illness)
                    for appointment in appointments:
                        st.sidebar.write(f"- {appointment}")
                    
                    # Buttons for edit and delete (without handling the button press logic)
                    if st.sidebar.button(f"Edit {illness}"):  # Edit button
                        new_illness = st.sidebar.text_input("New Illness Name", illness)
                        new_appointments = st.sidebar.text_area("New Appointment Notes", "\n".join(appointments))
                        if st.sidebar.button(f"Save Edit for {illness}"):
                            if new_illness and new_appointments:
                                new_appointments_list = new_appointments.split("\n")
                                try:
                                    await edit_illness_async(username, illness, new_illness, new_appointments_list)
                                    st.sidebar.success(f"Entry '{illness}' edited successfully.")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.sidebar.error(f"Error editing illness: {e}")

                    if st.sidebar.button(f"Delete {illness}"):  # Delete button
                        if st.sidebar.button(f"Confirm Delete {illness}"):

                            try:
                                await delete_illness_async(username, illness)
                                st.sidebar.success(f"Illness '{illness}' deleted successfully.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.sidebar.error(f"Error deleting illness: {e}")
            else:
                st.sidebar.write("No illnesses recorded yet.")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")

    # Main form for adding new notes
    with st.form("add_note_form"):
        illness = st.text_input("Illness")
        appointment_note = st.text_area("Appointment Note")
        submitted = st.form_submit_button("Add Note")

        if submitted:
            username = st.session_state.username  # Use the stored username
            
            if username and illness and appointment_note:
                new_note = {illness: [appointment_note]}
                
                # Add the note asynchronously
                basket_name = asyncio.run(add_to_basket_async(username, new_note))
                st.success(f"Note added to {basket_name}.")
                
                # Trigger a rerun to refresh the data in the sidebar
                st.rerun()
            else:
                st.error("Please fill in all fields (illness and appointment note).")

    # Run the asynchronous display_illnesses function in the event loop
    if st.session_state.username:
        asyncio.run(display_illnesses())
