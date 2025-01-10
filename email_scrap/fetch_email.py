import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import base64
import os
import datetime
from openai import OpenAI

# Define scopes for Gmail API
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)
SCOPES = ["https://mail.google.com/"]

def get_script_dir():
    """Get the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def get_service():
    """Authenticate and return the Gmail API service."""
    script_dir = get_script_dir()
    token_path = os.path.join(script_dir, 'token.json')

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_last_fetch_date():
    """Retrieve the last fetch date from the tracker file."""
    script_dir = get_script_dir()
    tracker_path = os.path.join(script_dir, 'last_fetch_date.json')

    if os.path.exists(tracker_path):
        with open(tracker_path, 'r') as file:
            data = json.load(file)
            return data.get('last_fetch_date')
    return None

def update_last_fetch_date(date):
    """Update the tracker file with the most recent fetch date."""
    script_dir = get_script_dir()
    tracker_path = os.path.join(script_dir, 'last_fetch_date.json')

    with open(tracker_path, 'w') as file:
        json.dump({'last_fetch_date': date}, file)

def get_email_messages(service):
    """Retrieve emails starting from the last fetch date."""
    last_fetch_date = get_last_fetch_date()
    if last_fetch_date:
        query = f"after:{last_fetch_date}"
    else:
        # Default to fetching emails from the last 3 days if no date is tracked
        date_from = (datetime.datetime.utcnow() - datetime.timedelta(days=3)).strftime('%Y/%m/%d')
        query = f"after:{date_from}"

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    emails = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')

        body = ''
        def extract_body(part):
            """Recursively extract body from parts."""
            if 'parts' in part:
                for sub_part in part['parts']:
                    result = extract_body(sub_part)
                    if result:
                        return result
            elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            return None

        payload = msg.get('payload', {})
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            body = extract_body(payload)

        internal_date = int(msg.get('internalDate', 0)) // 1000
        email_date = datetime.datetime.utcfromtimestamp(internal_date).strftime('%Y/%m/%d')

        emails.append({'subject': subject, 'body': body, 'date': email_date})

    return emails

def save_emails_to_txt(emails):
    """Save emails to local .txt files and update the last fetch date."""
    os.makedirs('emails', exist_ok=True)
    os.makedirs('email_cleaned', exist_ok=True)

    last_date = None

    for email in emails:
        filename = os.path.join('emails', f"{email['subject'][:50].replace('/', '_')}.txt")
        subject, date, body = email['subject'], email['date'], email['body']
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"Title: {subject}\n")
            file.write(f"Date: {date}\n")
            file.write(f"Body:\n{body}\n")

        if not last_date or email['date'] > last_date:
            last_date = email['date']

        filename = os.path.join('email_cleaned', f"{email['subject'][:50].replace('/', '_')}.txt")
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this email:\nSubject: {subject}\nBody: {body}\nDate: {date}\nDetermine if it's related to job applications. If irrelevant, output 'irrelevant email'. If relevant, provide output strictly in this format:\nJob Role: xxx\nCompany: xxx\nStatus: xxx (submitted/OA/interview/rejected)\nDate: mm/dd/yyyy",
                }
            ],
            model="gpt-4o-mini",
        )
        analysis = response.choices[0].message.content
        if "irrelevant" in analysis.lower():
            continue
        else:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f"{analysis}\n")
    
    if last_date:
        update_last_fetch_date(last_date)

def fetch_emails():
    """
    Main function to fetch and save emails:
    1. Authenticate with the Gmail API and create a service object.
    2. Retrieve email messages starting from the last fetch date or the default period.
    3. Save the email content to local .txt files in the "emails" directory.
    4. Update the tracker file with the latest email fetch date to avoid duplication in future fetches.
    """
    service = get_service()
    emails = get_email_messages(service)
    save_emails_to_txt(emails)

if __name__ == '__main__':
    fetch_emails()
