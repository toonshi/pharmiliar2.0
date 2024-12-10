import aiohttp
import asyncio

# Define your pantry details
PANTRY_URL = "https://getpantry.cloud/apiv1/pantry/6595cb63-5a9f-49bf-b28f-1151f0032f85"
BASKET_1 = "basket_1"


# Local cache for baskets
basket_cache = {}

async def fetch_basket_async(basket_name):
    """ Fetches the basket data asynchronously and caches it. """
    # If the basket is already in cache, return it
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

async def add_to_basket_async(new_note):
    """ Adds a new note to basket_1 asynchronously and caches the result. """
    # Fetch basket_1 data
    basket_data = await fetch_basket_async(BASKET_1)

    # Add the new note to the basket
    for illness, appointments in new_note.items():
        if illness not in basket_data:
            basket_data[illness] = appointments
        else:
            basket_data[illness].extend(appointments)

    # Update the basket data on the server
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{PANTRY_URL}/basket/{BASKET_1}", json=basket_data) as response:
            if response.status == 200:
                # Cache the updated basket data
                basket_cache[BASKET_1] = basket_data
                return BASKET_1
            else:
                raise Exception("Error saving basket data.")

async def load_all_baskets():
    """ Loads only basket_1 initially. """
    # Fetch and cache basket_1
    basket_data = await fetch_basket_async(BASKET_1)
    return basket_data

# Usage example (using asyncio to run the async functions)
async def main():
    # Example of adding new data to the basket
    new_note = {
        "flu": ["appointment_1", "appointment_2"],
        "fever": ["appointment_3"]
    }
    
    await add_to_basket_async(new_note)
    
    # Loading all baskets (though only basket_1 is loaded here)
    baskets = await load_all_baskets()
    print(baskets)

# Run the async main function
asyncio.run(main())
