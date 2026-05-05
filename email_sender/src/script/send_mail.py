# from logging import raiseExceptions
import requests
import json
import base64
from pathlib import Path
import yaml
import time
import sys
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from mail_utils import get_latest_file, zip_file, summary

#root path
ROOT_DIR = Path(__file__).resolve().parents[2]
Mapping_Folder = ROOT_DIR / 'mapping'
dotenv_path = ROOT_DIR / "email.env"
load_dotenv(dotenv_path)

#Log_config
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"email_sender_{datetime.now().strftime('%Y%m%d')}.log"
#log path is diff in develop branch

LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO")
PROFILE = os.getenv("PROFILE", "dev")

logging.basicConfig(
    level=LOG_LEVEL_NAME,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

logger.info(f"Profile: {PROFILE}")
logger.info(f"Log level: {LOG_LEVEL_NAME}")

#mal mapping
cc_mapping_file = Mapping_Folder / 'cc_mapping.yaml'
#token file
token_file = ROOT_DIR / "live_token" / "token.json"
user_id = "donotreply@lyra-network.co.in"


def load_token():
    if not token_file.exists():
        logger.error("Token file missing | path=%s", token_file)
        raise FileNotFoundError("Run auth.py first")

    data = json.loads(token_file.read_text())

    now = int(time.time())
    expires_at = data.get("expiry_time")

    if not expires_at or now >= expires_at:
        logger.error("Access token expired")
        raise RuntimeError("Access token expired. Re-run auth.py")

    logger.info("Access token loaded successfully")
    return data['token']

def build_recipients(cc_str: str):
    emails = [e.strip() for e in cc_str.split(",")]
    return [{"emailAddress": {"address": email}} for email in emails]

def parse_args():
    report_type = None
    provider = None
    specific_file = None

    if len(sys.argv) > 1:
        report_type = sys.argv[1]

    if len(sys.argv) > 2:
        provider = sys.argv[2]

    if len(sys.argv) > 3:
        specific_file = sys.argv[3]

    return report_type, provider, specific_file


## Arguments provider, report_type, specific_file[optional] (if "specific_file" then no provider, report_type required)
report_type, provider, specific_file = parse_args()

logger.info(
    "Script started | report_type=%s | provider=%s | specific_file=%s",
    report_type, provider, specific_file
)

# testing
# report_type = "mpireport"
# provider = "stripe"
# specific_file = r"D:\Lyra_Dev\AuthenticationReport\data\output\dummy_SR.xlsx"

file_path, report_type, provider = get_latest_file(report_type, provider, specific_file)
logger.info(
    "Resolved file | path=%s | report_type=%s | provider=%s",
    file_path, report_type, provider
)

# If files exists
try:
    if file_path.exists():
        logger.info(
            "Report file found | report_type=%s | provider=%s | file=%s",
            report_type, provider, file_path.name
        )

        file_size_bytes = file_path.stat().st_size
        logger.info(
            "Attachment file size | file=%s | size_mb=%.2f",
            file_path.name,
            file_size_bytes / 1000000
        )

        if file_size_bytes > 11999999: #i.e. more than 12 mb it will get zipped.
            file_path = zip_file(file_path)
            logger.info("File compressed for email | file=%s", file_path.name)

        else:
            logger.info("File below size threshold, sending as-is | file=%s", file_path.name)

        attachments = []
        for path in [file_path]:
            logger.debug("Attaching file | %s", path.name)
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": path.name,
                "contentBytes": content,
                "contentType": "text/csv"
            })

        # load authentication token
        access_token = load_token()

        # reading file to calculate aggregated values & add summary
        htmltable = summary(file_path)

        subject = f"Lyra PG - 3DS report - {provider.upper()}"

        body_content = f"""
        <html>
        <body>

        <p>Dear Partner,</p>

        <p>
        Please find attached your daily 3DS <b>{report_type}</b> for <b>{provider.upper()}</b>.
        </p>

        {htmltable}

        <p>
        Regards,<br>
        Lyra Network Pvt Ltd
        </p>

        </body>
        </html>
        """

        with open(cc_mapping_file) as f:
            mapping = yaml.safe_load(f)
        logger.info("Loaded CC mapping file | %s", cc_mapping_file)

        providers_map = mapping.get("providers", {})

        if provider.lower() not in providers_map:
            logger.warning(
                "Provider not found in mapping | provider=%s | file=%s",
                provider, cc_mapping_file
            )
            raise ValueError(
                f"Provider '{provider}' not found in mapping file: {cc_mapping_file}"
            )

        recipients = build_recipients(providers_map[provider.lower()])
        logger.info("Recipients mail_id | %s", recipients)

        email_data = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_content},
                "toRecipients": recipients,
                "attachments": attachments
            },
            "saveToSentItems": True
        }

        # user for sending email
        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_id}/sendMail"

        # logger.info(
        #     "Sending email | provider=%s | subject=%s | recipients=%d",
        #     provider, subject, recipients
        # )

        # returns a Response object, which contains the server's response.
        response = requests.post(endpoint, headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }, json=email_data)

        if response.status_code == 202:
            logger.info(
                "Email sent successfully | provider=%s | status=%s",
                provider, response.status_code
            )
            print(f"Email sent for {provider}")
        else:
            logger.error(
                "Email send failed | provider=%s | status=%s | response=%s",
                provider, response.status_code, response.text
            )
            print(f"Failed for {provider}: {response.status_code} - {response.text}")

except Exception as e:
    logger.exception(
        "Unhandled error occurred | provider=%s | error=%s",
        provider, str(e)
    )