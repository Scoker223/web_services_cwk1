import requests
import re
from tabulate import tabulate
from datetime import datetime

current_year = datetime.now().year  # Get the current year

BASE_URL = None  # Change this to your deployed URL if needed
token = None  # To store authentication token


# ------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------

def is_logged_in():
    """Check if a user is already logged in."""
    return token is not None

def make_api_request(endpoint, method='GET', data=None):
    """Helper function to make API requests."""
    headers = {'Authorization': f'Token {token}'} if token else {}
    url = f'{BASE_URL}/{endpoint}'

    try:
        if method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            response = requests.get(url, headers=headers, timeout=5)

        if response.content.strip() == b'':
            print("Received an empty response from the server.")
            return None
        if response.status_code == 401:
            print("Authentication failed. Please login again.")
            return None

        return response.json()
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


# ------------------------------------------------------------------------
# Authentication Functions
# ------------------------------------------------------------------------

def register():
    """Register a new user."""
    global token

    if is_logged_in():
        print("You are already logged in. Please log out before registering a new account.")
        return

    username = input("Enter username: ")
    email = input("Enter email: ")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print("Invalid email format. Please use the format 'user@example.com'.")
        return
    password = input("Enter password: ")

    response = make_api_request('register/', method='POST', data={
        'username': username,
        'email': email,
        'password': password
    })

    if response:
        print("Registration successful!")
    else:
        print("Registration failed.")


def login(command):
    """Log in a user."""
    global BASE_URL, token

    if is_logged_in():
        print("You are already logged in. Please log out first.")
        return

    parts = command.split()
    if len(parts) != 2:
        print("Invalid command syntax. Use: login <url>")
        return

    BASE_URL = parts[1].rstrip('/')

    username = input("Enter username: ")
    password = input("Enter password: ")

    response = make_api_request('login/', method='POST', data={
        'username': username,
        'password': password
    })

    if response and 'token' in response:
        token = response['token']
        print("Login successful!")
    else:
        print("Login failed.")


def logout():
    """Log out the current user."""
    global token

    if not is_logged_in():
        print("You are not logged in.")
        return

    response = make_api_request('logout/', method='POST')

    if response is not None:
        token = None
        print("Logout successful!")
    else:
        print("Logout failed.")


# ------------------------------------------------------------------------
# Data Viewing Functions
# ------------------------------------------------------------------------

def list_modules():
    """List all available modules."""
    if not is_logged_in():
        print("You need to log in to view modules.")
        return

    modules = make_api_request('module-instances/')
    professors = make_api_request('professors/')

    if modules and professors:
        professor_dict = {prof['id']: prof['name'] for prof in professors}
        table_data = [
            [
                module['id'],
                module['module_code'],
                module['module_name'],
                module['year'],
                module['semester'],
                "\n".join(f"{prof_id}, {professor_dict.get(prof_id, 'Unknown')}" for prof_id in module['professors'])
            ]
            for module in modules
        ]
        print(tabulate(table_data, headers=["ID", "Code", "Name", "Year", "Semester", "Taught by"], tablefmt="grid"))
    else:
        print("Failed to retrieve modules.")


def view_ratings():
    """View ratings submitted by the logged-in user."""
    if not is_logged_in():
        print("You need to log in to view ratings.")
        return

    ratings = make_api_request('ratings/')
    if ratings:
        table_data = [
            [
                f"{rate['professor__id']}, {rate['professor__name']}",
                rate["module_instance__module__module_name"],
                rate['rating']
            ]
            for rate in ratings
        ]
        print(tabulate(table_data, headers=["Professor", "Module", "Rating"], tablefmt="grid"))
    else:
        print("You have not rated any professors.")


# ------------------------------------------------------------------------
# Rating Functions
# ------------------------------------------------------------------------

def rate_professor(command):
    """Submit a rating for a professor."""
    if not is_logged_in():
        print("You need to log in to rate a professor.")
        return

    parts = command.split()
    if len(parts) != 6:
        print("Invalid command format. Use: rate <prof_id> <module_code> <year> <semester> <rating>")
        return

    professor_id, module_code, year, semester, rating_val = parts[1].upper(), parts[2].upper(), parts[3], parts[4], parts[5]

    module_instances = make_api_request('module-instances/')
    if not module_instances:
        print("Failed to retrieve module instances.")
        return

    matching_instance = next((instance for instance in module_instances if instance['module_code'] == module_code and
                              instance['year'] == int(year) and instance['semester'] == int(semester)), None)

    if not matching_instance:
        print(f"No module instance found for {module_code} in {year} semester {semester}.")
        return

    if professor_id not in matching_instance['professors']:
        print(f"Professor {professor_id} did not teach {module_code} in {year} semester {semester}.")
        return

    response = make_api_request('rate/', method='POST', data={
        'professor_id': professor_id,
        'module_instance_id': matching_instance['id'],
        'rating': int(rating_val)
    })

    if response:
        print("Rating submitted successfully!")
    else:
        print("Failed to submit rating.")


def average_rate(command):
    """Get the average rating for a professor for a specific module."""
    if not is_logged_in():
        print("You need to log in to view ratings.")
        return

    parts = command.split()
    if len(parts) != 3:
        print("Invalid command format. Use: average <prof_id> <module_code>")
        return

    professor_id, module_code = parts[1].upper(), parts[2].upper()
    response = make_api_request(f'average/{professor_id}/{module_code}')

    if response and 'average_rating' in response:
        print(f"Average rating for Professor {professor_id} in module {module_code}: {response['average_rating']:.1f}")
    else:
        print("No ratings available for this professor in this module.")


# ------------------------------------------------------------------------
# Main Program
# ------------------------------------------------------------------------

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
