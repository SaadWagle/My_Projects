📧 Send Mail Service – Microsoft Graph API

1\. Overview
This project provides a standalone Python service to send ETL-generated reports via Office 365 (Microsoft Graph API) with file attachments.
The service is designed for:
Daily automated report delivery
Ad-hoc resend of specific reports
Secure authentication using Azure AD (OAuth2)
Use in DEV / STAGING / PROD environments
The mail sender is independent of report generation logic.

2\. Key Features
Uses Microsoft Graph API (not SMTP)

Supports:
Latest report by pattern
Specific file resend by filename
Token-based authentication with expiry handling
Provider-to-recipient mapping via YAML config
Centralized logging
Secure (no credentials in code)

3\. Folder Structure

email\_sender/

│

├── src/

│   ├── main\_send\_mail\_report.py   (trigger / entry point)

│   ├── logging\_config.py

│   └── script/

│       ├── auth.py

│       ├── send\_mail.py

│       └── mail\_utils.py

│

├── mapping/

│   └── cc\_mapping.yaml

│

├── live\_token/

│   └── token.json

│

├── logs/

│   └── email\_sender.log

4\. How It Works (Flow)
User runs the trigger script with arguments
Script checks if token is valid
If expired → runs auth.py to generate new token
Calls send\_mail.py with given arguments
Finds the correct report file
Reads recipient emails from mapping file
Sends email using Microsoft Graph API
Logs success or failure

5\. Command Line Usage
Send latest report by type and provider
python main\_send\_mail\_report.py mpireport worldline
Send specific historical file
python main\_send\_mail\_report.py mpireport worldline mpireport\_billing\_2026-01-19\_to\_2026-01-20\_lyraindia\_worldline.csv

Arguments:
report\_type (required if no specific file)
provider (required)
specific\_file (optional)

6\. Mapping File (Recipients)
File: mapping/cc\_mapping.yaml

Example:
    providers:
&nbsp; - provider: worldline
&nbsp;   to: saad.wagle@company.com,ops@worldline.com
&nbsp; - provider: stripe
&nbsp;   to: saad.wagle@company.com,charles@company.com

This file is used only to fetch recipient email addresses.

7\. Security \& Compliance
Uses Azure AD OAuth2 (client credentials)
No passwords or tokens stored in code
Token stored securely in token.json
No sensitive data logged
Attachments are read-only files
TLS encryption via HTTPS

8\. Logging
Logs are written to:
logs/email_sender_date.log

Logs include:
Provider
Report type
File name
Success / failure
Timestamp
No secrets or tokens are logged.

9\. Environment Support
DEV
STAGING
PROD

Configurable using:
.env variables
YAML mapping
Separate Azure App registrations per environment

10\. Error Handling
Missing file → clear error message

Invalid provider → validation error
Token expired → auto re-authentication
Graph API failure → logged with stack trace

11\. Owner
Maintained by: Data Analyst - Saad
Technology: Python + Microsoft Graph API
