import streamlit as st
import asyncio
from basket_manager import add_to_basket_async, load_user_basket, edit_illness_async, delete_illness_async

st.title("Doctor's Appointment Notes")

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
