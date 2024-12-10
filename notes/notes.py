import streamlit as st
import asyncio
from basket_manager import add_to_basket_async, load_user_basket, edit_illness_async, delete_illness_async

st.title("Doctor's Appointment Notes")

st.sidebar.header("Previous Illnesses")

# Display illnesses in the sidebar with options to edit or delete
async def display_illnesses(username):
    try:
        data = await load_user_basket(username)
        if data:
            for illness, appointments in data["illnesses"].items():
                st.sidebar.subheader(illness)
                for appointment in appointments:
                    st.sidebar.write(f"- {appointment}")
                    
                # Create two columns for Edit and Delete buttons side by side
                col1, col2 = st.sidebar.columns(2)
                
                with col1:
                    if st.button(f"Edit"):  # Notice change here to st.button
                        new_illness = st.sidebar.text_input("New Illness Name", illness)
                        new_appointments = st.sidebar.text_area("New Appointment Notes", "\n".join(appointments))
                        if st.sidebar.button(f"Save Edit"):
                            if new_illness and new_appointments:
                                new_appointments_list = new_appointments.split("\n")
                                try:
                                    await edit_illness_async(username, illness, new_illness, new_appointments_list)
                                    st.sidebar.success(f"Entry '{illness}' edited successfully.")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.sidebar.error(f"Error editing illness: {e}")

                with col2:
                    if st.button(f"Delete"):  # Notice change here to st.button
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
    username = st.text_input("Username")
    illness = st.text_input("Illness")
    appointment_note = st.text_area("Appointment Note")
    submitted = st.form_submit_button("Add Note")

    if submitted:
        if username and illness and appointment_note:
            new_note = {illness: [appointment_note]}
            
            # Add the note asynchronously
            basket_name = asyncio.run(add_to_basket_async(username, new_note))
            st.success(f"Note added to {basket_name}.")
            
            # Trigger a rerun to refresh the data in the sidebar
            st.rerun()
        else:
            st.error("Please fill in all fields (username, illness, and appointment note).")

# Run the asynchronous display_illnesses function in the event loop
if username:
    asyncio.run(display_illnesses(username))
