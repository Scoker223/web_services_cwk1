import requests
import re
from tabulate import tabulate
from datetime import datetime

current_year = datetime.now().year  # Get the current year

BASE_URL = None  # Change this to your deployed URL if needed
token = None  # To store authentication token


def register():
    global token  # To check if a user is already logged in

    # Check if already logged in
    if token:
        print("You are already logged in. Please log out before registering a new account.")
        return
    
    username = input("Enter username: ")
    email = input("Enter email: ")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print("Invalid email format. please ensure that your mail is in format \'user@example.com\'")
        return
    password = input("Enter password: ")

    response = requests.post(f'{BASE_URL}/register/', json={
        'username': username,
        'email': email,
        'password': password
    })

    if response.status_code == 200:
        print("Registration successful!")
    else:
        print("Registration failed:", response.json().get('error', 'Unknown error'))


def login(command):
    #parse the url inputted
    global BASE_URL, token

    if token:
        print("You are already logged in. Please log out before logging in again.")
        return
    
    # Extract the URL from the command (e.g., "login http://127.0.0.1:8000/api")
    parts = command.split()
    if len(parts) != 2:
        print("Invalid command syntax. Use: login <url>")
        return

    BASE_URL = parts[1].strip()  # Get the URL part

    # Ensure the URL does not end with a trailing slash
    if BASE_URL.endswith('/'):
        BASE_URL = BASE_URL[:-1]

    # Input username and password to be sent to url
    username = input("Enter username: ")
    password = input("Enter password: ")

    try:
        # Adding timeout and handling potential connection errors
        response = requests.post(f'{BASE_URL}/login/', json={
            'username': username,
            'password': password
        }, timeout=5)  # Timeout set to 5 seconds

        # Check if the request was successful
        if response.status_code == 200:
            try:
                token_data = response.json()
                token = token_data.get('token')
                if token:
                    print("Login successful!")
                else:
                    print("Login failed: No token received.")
            except requests.JSONDecodeError:
                print("Login failed: Invalid JSON response.")
        else:
            # Handling HTTP errors (404, 500, etc.)
            print("Login failed:", response.json().get('error', 'Unknown error'))

    except requests.exceptions.MissingSchema:
        print("Invalid URL. Please include http:// or https://")
    except requests.exceptions.InvalidURL:
        print("Invalid URL format.")
    except requests.ConnectionError:
        print("Failed to connect to the server. Please check the URL and your internet connection.")
    except requests.Timeout:
        print("The request timed out. Please try again later.")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")


def logout():
    global token
    if token:
        response = requests.post(f'{BASE_URL}/logout/', headers={'Authorization': f'Token {token}'})
        if response.status_code == 200:
            token = None
            print("Logout successful!")
        else:
            print("Logout failed.")
    else:
        print("You are not logged in.")


def list_modules():
    if token is None:
        print("You need to log in to see the list of modules")
        return
    
    # Fetch module instances
    response = requests.get(f'{BASE_URL}/module-instances/', headers={'Authorization': f'Token {token}'})
    if response.status_code == 200:
        module_instances = response.json()

        # Fetch professors
        professor_response = requests.get(f'{BASE_URL}/professors/', headers={'Authorization': f'Token {token}'})
        if professor_response.status_code != 200:
            print("Failed to retrieve professors.")
            return

        professors = professor_response.json()
        professor_dict = {prof['id']: prof['name'] for prof in professors}

        table_data=[]
        # Display module instances with professor names
        for module in module_instances:
            professor_details = [f"{prof_id}, {professor_dict.get(prof_id, 'Unknown')}" for prof_id in module['professors']]
            professor_list = "\n".join(professor_details)

            table_data.append([
                module['id'],
                module['module_code'],
                module['module_name'],
                module['year'],
                module['semester'],
                professor_list
            ])
        print(tabulate(table_data, headers=["Code", "Name", "Year", "Semester", "Taught by"], tablefmt="grid"))

    elif response.status_code == 401:
        print("Command failed:", response.json().get('error', 'Unknown error'))
    else:
        print("Failed to retrieve modules.")



def view_ratings():
    if token is None:
        print("You need to log in to view the ratings")
        return
    
    response = requests.get(f'{BASE_URL}/ratings/', headers={'Authorization': f'Token {token}'})
    if response.status_code == 200:
        table_data=[]
        rating = response.json()
        if rating:
            # Prepare data for tabulate if ratings are not empty
            table_data = []
            for rate in rating:
                table_data.append([
                    f"{rate['professor__id']}, {rate['professor__name']}", rate["module_instance__module__module_name"],
                    rate['rating']
                ])

            # Print formatted table with just professor and rating
            print(tabulate(table_data, headers=["Professor", "module", "Rating"], tablefmt="grid"))
        else:
            # Print this message if no ratings found
            print("You have not rated any professors")
    elif response.status_code == 401:
        print("command failed:", response.json().get('error', 'Unknown error'))
    else:
        print("Failed to retrieve ratings.")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def average_rate(command):
    if token is None:
        print("You need to log in to view a rating.")
        return

    # Extract professor ID and module code from the command
    parts = command.split()
    if len(parts) != 3:
        print("Invalid command format. Use: average <professor_id> <module_code>")
        return

    professor_id = parts[1].upper()
    module_code = parts[2].upper()

    # Construct the API endpoint
    endpoint = f"{BASE_URL}/average/{professor_id}/{module_code}"

    try:
        response = requests.get(endpoint, headers={'Authorization': f'Token {token}'})

        if response.status_code == 200:
            data = response.json()
            avg_rating = data.get("average_rating")
            if avg_rating is not None:
                print(f"Average rating for Professor {professor_id} in module {module_code}: {avg_rating:.1f}")
            else:
                print(f"No ratings available for Professor {professor_id} in module {module_code}.")
        
        # Handle case when professor does not teach the module
        elif response.status_code == 404:
            data = response.json()
            message = data.get('message', f"No ratings available for Professor {professor_id} in module {module_code}.")
            print(message)
        
        # Handle other potential HTTP errors
        else:
            error_message = response.json().get('error', 'Unknown error')
            print(f"Failed to retrieve ratings: {error_message}")

    except requests.ConnectionError:
        print("Failed to connect to the server. Please check the URL and your internet connection.")
    except requests.Timeout:
        print("The request timed out. Please try again later.")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")



def rate_professor(command):
    if token is None:
        print("You need to log in to rate a professor.")
        return

    parts = command.split()
    if len(parts) != 6:  # Expected format: rate <prof_id> <module_code> <year> <semester> <rating>
        print("Invalid command format. Use: rate <prof_id> <module_code> <year> <semester> <rating>")
        return

    professor_id = parts[1].upper()
    module_code = parts[2].upper()
    try:
        year = int(parts[3])
        semester = int(parts[4])
        rating_val = int(parts[5])
    except ValueError:
        print("Year, semester, and rating must be integers.")
        return

    if year < 1900 or year > current_year:
        print(f"Invalid year. Please enter a valid year between 1900 and {current_year}.")
        return

    if semester not in [1, 2]:
        print("Invalid semester. Please enter 1 or 2.")
        return

    if rating_val < 1 or rating_val > 5:
        print("Invalid rating. Please enter a number between 1 and 5.")
        return

    # Retrieve module instances to find the matching module_instance_id
    try:
        # ✅ Check if response is empty
        if response.content.strip() == b'':
            print("Received an empty response from the server.")
            return

        # ✅ Check if response is JSON-formatted
        try:
            data = response.json()
        except ValueError:
            print("Received a non-JSON response from the server.")
            print(f"Raw response: {response.text}")
            return
        
        response = requests.get(f'{BASE_URL}/module-instances/', headers={'Authorization': f'Token {token}'})
        if response.status_code == 200:
            module_instances = response.json()
        else:
            print("Failed to retrieve module instances.")
            return
    except Exception as e:
        print("Error retrieving module instances:", e)
        return

    matching_instance = None
    for instance in module_instances:
        if instance.get('module_code') == module_code and instance.get('year') == year and instance.get('semester') == semester:
            matching_instance = instance
            break

    if not matching_instance:
        print(f"No module instance found for {module_code} in {year} semester {semester}.")
        return
    
    if professor_id not in matching_instance.get('professors', []):
        print(f"Professor {professor_id} did not teach {module_code} in {year} semester {semester}.")
        return
#----------------------------------------------------------------------------------------------------------------------------------------

    module_instance_id = matching_instance.get('id')

    data = {
        'professor_id': professor_id,
        'module_instance_id': module_instance_id,
        'rating': rating_val
    }

    try:
        response = requests.post(f'{BASE_URL}/rate/', json=data, headers={'Authorization': f'Token {token}'})
        if response.status_code == 200:
            print("Rating submitted successfully!")
        elif response.status_code == 401:
            print("Command failed:", response.json().get('error', 'Unknown error'))
        else:
            print("Failed to submit rating:", response.json().get('error', 'Unknown error'))
    except requests.ConnectionError:
        print("Failed to connect to the server. Please check the URL and your internet connection.")
    except requests.Timeout:
        print("The request timed out. Please try again later.")

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
def main():
    print("Available commands: register, login <url>, logout, list, view, rate <prof_id> <module_code> <year> <semester> <rating>, average <prof_id> <module_code>, exit")
    while True:
        command = input("Enter command: ").strip().lower()
        if command == 'register':
            register()
        elif command.startswith('login'):
            login(command)
        elif command == 'logout':
            logout()
        elif command == 'list':
            list_modules()
        elif command == 'view':
            view_ratings()
        elif command.startswith('rate'):
            rate_professor(command)
        elif command.startswith('average'):
            average_rate(command)
        elif command == 'exit':
            print("Exiting...")
            break
        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()