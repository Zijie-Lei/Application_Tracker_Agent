import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_script_dir():
    """Get the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def get_service():
    """
    Authenticates and returns the Google Sheets API service object.
    """
    script_dir = get_script_dir()
    token_path = os.path.join(script_dir, 'token.json')

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service

def get_or_create_spreadsheet(service):
    """
    Checks for an existing spreadsheet ID in a .json file.
    If the file doesn't exist, creates a new spreadsheet and saves the ID.
    """
    script_dir = get_script_dir()
    json_file = os.path.join(script_dir, 'spreadsheet_id.json')
    # json_file = 'spreadsheet_id.json'

    try:
        # Check if the JSON file exists
        with open(json_file, 'r') as file:
            data = json.load(file)
            spreadsheet_id = data.get('spreadsheet_id')
            if spreadsheet_id:
                print(f"Using existing spreadsheet ID: {spreadsheet_id}")
                return spreadsheet_id
    except FileNotFoundError:
        print("No existing spreadsheet ID found. Creating a new spreadsheet.")

    # Create a new spreadsheet
    spreadsheet_body = {
        'properties': {
            'title': 'Job Application Status 2025'
        },
        'sheets': [
            {
                'properties': {
                    'title': 'Job Applications'
                }
            }
        ]
    }
    try:
        spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        print(f"Created new spreadsheet with ID: {spreadsheet_id}")

        # Save the spreadsheet ID to a .json file
        with open(json_file, 'w') as file:
            json.dump({'spreadsheet_id': spreadsheet_id}, file)

        return spreadsheet_id
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise

def add_new_application(service, spreadsheet_id, job_title, company, application_date, status):
    """
    Adds a new job application record to the specified Google Spreadsheet.

    Parameters:
        service (googleapiclient.discovery.Resource): The Google Sheets API service instance.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        job_title (str): The role/title of the job application.
        company (str): The name of the company where the application was sent.
        application_date (str): The date of the application in YYYY-MM-DD format.
        status (str): The current status of the application (e.g., 'Applied', 'Interview Scheduled').

    Raises:
        ValueError: If any of the inputs are empty or improperly formatted.
    """
    # Input validation
    if not all([job_title, company, application_date, status]):
        raise ValueError("All parameters must be non-empty.")
    
    if not isinstance(application_date, str) or len(application_date.split('-')) != 3:
        raise ValueError("application_date must be in YYYY-MM-DD format.")

    # Prepare data to append
    values = [[job_title, company, application_date, status]]
    body = {'values': values}

    # Append data to the spreadsheet
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range='Job Applications',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    return (f"Added new application for {job_title} at {company}.")

def update_application_status(service, spreadsheet_id, job_title, company, new_status):
    """
    Updates the status of an existing job application in the specified Google Spreadsheet.

    Parameters:
        service (googleapiclient.discovery.Resource): The Google Sheets API service instance.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        job_title (str): The role/title of the job application to identify.
        company (str): The company name to identify the job application.
        new_status (str): The new status to update the application with (e.g., 'Interview Scheduled').

    Raises:
        ValueError: If any of the inputs are empty or improperly formatted.
        Exception: If the specified application could not be found.
    """
    # Input validation
    if not all([job_title, company, new_status]):
        raise ValueError("job_title, company, and new_status must be non-empty.")

    # Read all data from the spreadsheet
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range='Job Applications').execute()
    values = result.get('values', [])

    # Check if data is present
    if not values:
        raise Exception("No data found in the spreadsheet.")

    # Search for the matching row
    for i, row in enumerate(values):
        if len(row) >= 2 and row[0] == job_title and row[1] == company:
            # Update the status
            range_to_update = f'Job Applications!D{i + 1}'  # Column D is the Status column
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_to_update,
                valueInputOption='USER_ENTERED',
                body={'values': [[new_status]]}
            ).execute()
            print(f"Updated status to '{new_status}' for {job_title} at {company}.")
            return

    raise Exception(f"Application for {job_title} at {company} not found.")

if __name__ == '__main__':
    # Setup
    service = get_service()
    spreadsheet_id = get_or_create_spreadsheet(service)

    # Add a new application
    add_new_application(
        service, spreadsheet_id,
        job_title="Software Engineer",
        company="Google",
        application_date="2025-01-09",
        status="Applied"
    )

    # Update an existing application's status
    update_application_status(
        service, spreadsheet_id,
        job_title="Software Engineer",
        company="Google",
        new_status="Interview Scheduled"
    )