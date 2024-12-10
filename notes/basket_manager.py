import aiohttp
import asyncio
import json

# Define your pantry details
PANTRY_URL = "https://getpantry.cloud/apiv1/pantry/6595cb63-5a9f-49bf-b28f-1151f0032f85"

# Local cache for baskets
basket_cache = {}

# Default basket data (this will be the initial structure for new users)
DEFAULT_BASKET_DATA = {
    "illnesses": {},
    "appointments": [],
}

async def fetch_basket_async(basket_name):
    """ Fetches the basket data asynchronously and caches it. """
    if basket_name in basket_cache:
        return basket_cache[basket_name]
    
    url = f"{PANTRY_URL}/basket/{basket_name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                basket_data = await response.json()
                basket_cache[basket_name] = basket_data
                return basket_data
            else:
                return {}

async def create_new_basket(username):
    """ Creates a new basket with the default data for the username. """
    url = f"{PANTRY_URL}/basket/{username}"
    
    # Use the default basket data
    basket_data = DEFAULT_BASKET_DATA
    
    # Make a request to create the new basket
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=basket_data) as response:
            if response.status == 200:
                basket_cache[username] = basket_data  # Cache the new basket
                return basket_data
            else:
                raise Exception(f"Failed to create new basket for {username}")

async def add_to_basket_async(username, new_note):
    """ Adds a new note to a user's basket asynchronously and caches the result. """
    basket_data = await fetch_basket_async(username)

    if not basket_data:
        basket_data = await create_new_basket(username)

    # Add the new note to the basket
    for illness, appointments in new_note.items():
        if illness not in basket_data["illnesses"]:
            basket_data["illnesses"][illness] = appointments
        else:
            basket_data["illnesses"][illness].extend(appointments)

    # Update the basket data on the server
    url = f"{PANTRY_URL}/basket/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=basket_data) as response:
            if response.status == 200:
                basket_cache[username] = basket_data
                return username
            else:
                raise Exception("Error saving basket data.")

async def load_user_basket(username):
    """ Loads the user's basket (either from the cache or by fetching it). """
    basket_data = await fetch_basket_async(username)
    return basket_data

async def edit_illness_async(username, old_illness, new_illness, new_appointments):
    """Edit an illness in the basket data."""
    basket_data = await fetch_basket_async(username)

    if old_illness in basket_data["illnesses"]:
        # Remove the old illness
        del basket_data["illnesses"][old_illness]
        
        # Add the new illness
        basket_data["illnesses"][new_illness] = new_appointments

        # Update the basket data on the server
        url = f"{PANTRY_URL}/basket/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=basket_data) as response:
                if response.status == 200:
                    basket_cache[username] = basket_data
                    return username
                else:
                    raise Exception("Error saving basket data after editing illness.")
    else:
        raise Exception(f"Illness '{old_illness}' not found.")

async def delete_illness_async(username, illness_to_delete):
    """Deletes an illness from the user's basket."""
    basket_data = await fetch_basket_async(username)

    if illness_to_delete in basket_data["illnesses"]:
        # Remove the illness
        del basket_data["illnesses"][illness_to_delete]

        # Update the basket data on the server
        url = f"{PANTRY_URL}/basket/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=basket_data) as response:
                if response.status == 200:
                    basket_cache[username] = basket_data
                    return username
                else:
                    raise Exception("Error saving basket data after deleting illness.")
    else:
        raise Exception(f"Illness '{illness_to_delete}' not found.")
