from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent

from email_scrap.fetch_email import fetch_emails
from sheet_modify.add_application import get_service, get_or_create_spreadsheet, add_new_application, update_application_status

load_dotenv()
SPREADSHEET_SERVICE = get_service()
SPREADSHEET_ID = get_or_create_spreadsheet(SPREADSHEET_SERVICE)

documents = SimpleDirectoryReader("emails").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

def agentic_fetch_emails():
    """
    Fetches emails using the fetch_emails function and handles any exceptions that occur.

    This function attempts to call the fetch_emails function and returns a success message if no exceptions are raised.
    If an exception occurs, it catches the exception and returns an error message with the exception details.

    Returns:
        str: A message indicating the result of the email fetching operation. 
             It returns "email fetched" if successful, or an error message if an exception is raised.
    """
    try:
        fetch_emails()
        return "emails fetched"
    except Exception as e:
        return f"Error: {str(e)}"
    
def agentic_add_new_application_to_spreadsheet(job_title, company, application_date, status):
    """
    Adds a new job application record to the specified Google Spreadsheet.

    Parameters:
        job_title (str): The role/title of the job application.
        company (str): The name of the company where the application was sent.
        application_date (str): The date of the application in YYYY-MM-DD format.
        status (str): The current status of the application (e.g., 'Applied', 'Interview Scheduled').

    Raises:
        ValueError: If any of the inputs are empty or improperly formatted.
    """
    try:
        return add_new_application(SPREADSHEET_SERVICE, SPREADSHEET_ID, job_title, company, application_date, status)
    except Exception as e:
        return f"Error: {str(e)}"

def agentic_update_application_status(job_title, company, new_status):
    """
    Updates the status of an existing job application in the specified Google Spreadsheet.

    Parameters:
        job_title (str): The role/title of the job application to be updated.
        company (str): The name of the company where the application was sent.
        new_status (str): The new status to be updated (e.g., 'Interview Scheduled', 'Rejected').

    Raises:
        ValueError: If any of the inputs are empty or improperly formatted.
        KeyError: If the job application record is not found in the spreadsheet.
    """
    try:
        return update_application_status(SPREADSHEET_SERVICE, SPREADSHEET_ID, job_title, company, new_status)
    except Exception as e:
        return f"Error: {str(e)}"


tools = [
    FunctionTool.from_defaults(agentic_fetch_emails),
    FunctionTool.from_defaults(agentic_add_new_application_to_spreadsheet), 
    FunctionTool.from_defaults(agentic_update_application_status),
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="get_email",
            description=(
                "Each .txt file contains a single email message."
                "This tool allows you to query the email messages."
            ),
        ),
    ),
]

agent = ReActAgent.from_tools(
    llm=OpenAI(model="gpt-4o-mini"), tools=tools, verbose=True
)

response = agent.chat("get the latest update on my application for Google, search for needed information and add to Google Spreadsheet")
print(str(response))