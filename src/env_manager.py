from decouple import config


# Function to retrieve the number of authorities
def authorities_count():
    count = 1
    while True:
        name_key = f'AUTHORITY{count}_NAME'
        name = config(name_key, default=None)
        if not name:
            break
        count += 1
    return count-1
   
   
# Function to retrieve the authorities' names
def authorities_names():
    authorities = []
    count = 1
    while True:
        name_key = f'AUTHORITY{count}_NAME'
        name = config(name_key, default=None)
        if not name:
            break
        authorities.append(name)
        count += 1
    return authorities


# Function to retrieve the authorities' names and addresses
def authorities_names_and_addresses():
    authorities = []
    count = 1
    while True:
        address_key = f'AUTHORITY{count}_ADDRESS'
        name_key = f'AUTHORITY{count}_NAME'
        address = config(address_key, default=None)
        name = config(name_key, default=None)
        if not address or not name:
            break
        authorities.append((name, address))
        count += 1
    return authorities


# Function to dynamically retrieve authorities addresses and names separated
def authorities_addresses_and_names_separated():
    authorities_names = []
    authorities_addresses = []
    count = 1
    # Loop to retrieve all authority addresses and names until no more are found
    while True:
        address_key = f'AUTHORITY{count}_ADDRESS'
        name_key = f'AUTHORITY{count}_NAME'
        # Check if the config key exists, if not, break the loop
        if not config(address_key, default=None) or not config(name_key, default=None):
            break
        # Append address and name to respective lists
        authorities_names.append(config(name_key))
        authorities_addresses.append(config(address_key))
        count += 1
    return authorities_addresses, authorities_names
