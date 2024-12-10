import streamlit as st
from basket_manager import add_to_basket, load_all_baskets

st.title("Doctor's Appointment Notes")

st.sidebar.header("Previous Illnesses")

# Display illnesses in the sidebar
def display_illnesses():
    try:
        data = load_all_baskets()
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
            basket_name = add_to_basket(new_note)
            st.success(f"Note added to {basket_name}.")
            
            # Trigger a rerun to refresh the data in the sidebar
            st.rerun()
        else:
            st.error("Please fill in both the illness and appointment note.")

# Display illnesses after potentially adding a new note
display_illnesses()
