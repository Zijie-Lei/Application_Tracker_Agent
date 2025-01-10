# LLM ReAct Agent for Job Application Management

## Initiative

This project aims to simplify job application management by leveraging a Local Large Language Model (LLM) to automate email analysis and track application progress.

## What It Does

- **Reasoning and Tool Utilization**: The agent takes natural language input, performs thorough reasoning to understand user intent, and calls relevant tool functions. For example:
  - Fetching emails related to job applications.
  - Querying through saved emails for specific information.
  - Adding new applications to a Google Spreadsheet.
  - Modifying existing statuses in the tracking spreadsheet.
  - Performing many other job management tasks seamlessly.
- Fetches and analyzes emails to identify job application updates.
- Maintains a spreadsheet to track application status, including interview invitations and follow-ups.

## How to Use

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Review necessary documentation:
   - [Google API Documentation](https://developers.google.com/gmail/api): For configuring email access and integrating with Google services.
   - [LlamaIndex Documentation](https://llamaindex.ai/docs): For understanding the LLM-based indexing and reasoning mechanism used in the project.

