import streamlit as st
import asyncio
from basket_manager import add_to_basket_async, load_all_baskets

st.title("Doctor's Appointment Notes")

st.sidebar.header("Previous Illnesses")

# Display illnesses in the sidebar
async def display_illnesses():
    try:
        # Await the asynchronous function load_all_baskets
        data = await load_all_baskets()
        if data:
            for illness, appointments in data.items():
                st.sidebar.subheader(illness)
                for appointment in appointments:
                    st.sidebar.write(f"- {appointment}")
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
        if illness and appointment_note:
            new_note = {illness: [appointment_note]}
            
            # Await the asynchronous function add_to_basket_async
            basket_name = asyncio.run(add_to_basket_async(new_note))
            st.success(f"Note added to {basket_name}.")
            
            # Trigger a rerun to refresh the data in the sidebar
            st.rerun()
        else:
            st.error("Please fill in both the illness and appointment note.")

# Run the asynchronous display_illnesses function in the event loop
asyncio.run(display_illnesses())
