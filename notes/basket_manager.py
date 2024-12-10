import requests

# Define your pantry details
PANTRY_URL = "https://getpantry.cloud/apiv1/pantry/6595cb63-5a9f-49bf-b28f-1151f0032f85"
BASKET_1 = "basket_1"
BASKET_2 = "basket_2"

def fetch_basket(basket_name):
    """ Fetches the basket data, only fetch basket_1 by default. """
    url = f"{PANTRY_URL}/basket/{basket_name}"
    response = requests.get(url)
    
    # Only raise an error if we can't find basket_1.
    if response.status_code != 200:
        if basket_name == BASKET_1:
            raise ValueError(f"Could not get basket: {basket_name} does not exist")
        else:
            # Allow failure for basket_2
            return {}

    return response.json()

def add_to_basket(new_note):
    """ Adds a new note to basket_1 and ensures only basket_1 is accessed at launch. """
    # Check if basket_1 exists
    try:
        basket_data = fetch_basket(BASKET_1)
    except ValueError as e:
        # Basket_1 doesn't exist, create it.
        basket_data = {}

    # Add the new note to the basket
    for illness, appointments in new_note.items():
        if illness not in basket_data:
            basket_data[illness] = appointments
        else:
            basket_data[illness].extend(appointments)
    
    # Update the basket on the server
    response = requests.put(f"{PANTRY_URL}/basket/{BASKET_1}", json=basket_data)
    
    if response.status_code == 200:
        return BASKET_1
    else:
        raise Exception("Error saving basket data.")

def load_all_baskets():
    """ Loads only basket_1 initially. """
    try:
        return fetch_basket(BASKET_1)
    except ValueError as e:
        # Basket_1 doesn't exist yet, so return an empty dictionary
        return {}

# TODO : later add logic to move items to basket_2 when basket_1 reaches a certain size.
