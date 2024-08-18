import requests

# This is done for testing purposes so I do not need to edit all the process_ids values in the test*.py, I just perform +1
# and I read it from all the tests.
edit_process_id = 0

with open("process_id.txt", 'r') as file:
        content = file.read().strip()
        edit_process_id = int(content)
        
with open("process_id.txt", 'w') as file:
        file.write(str(edit_process_id+1))

url = "http://localhost:8888/certification/generate_rsa_key_pair/"

# List of actor addresses
values = [
    "0x7364cc4E7F136a16a7c38DE7205B7A5b18f17258",
    "0xa5B6B3729Cf8f377EF6F97d87C49661b36Ed02bB",
    "0xb885E5701a3A4714799eE906f4Aa7C297f16D90a",
    "0x0882271d553738aB2b238F7a95fa7Ce0DE171EF5",
    "0xaA799c5cF973b4efe8386D4AcEfdAa2BF8e76Ab3"
]

# Set the headers to specify that the content type is JSON
headers = {
    "Content-Type": "application/json"
}

# Iterate over each address in the values list
for actor in values:
    # Update the payload with the current actor
    payload = {
        "actor": actor
    }
    
    # Send the POST request
    response = requests.post(url, json=payload, headers=headers)
    
    # Print out the status code and the response JSON for each actor
    print("Status Code:", response.status_code)
    
    # Handle the possibility of a non-JSON response
    try:
        print("Response JSON:", response.json())
    except ValueError:
        print("Response Text:", response.text)
    
    print("-" * 50)  # Separator between each request
