import msal
import json
from pathlib import Path
from dotenv import load_dotenv
import os
import time

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

def get_graph_token():
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )
    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"Token request failed: {result}")
    return result

def main():
    token_result = get_graph_token()

    # Ensure directory exists
    token_dir = ROOT_DIR / "live_token"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_file = token_dir / "token.json"

    current_time_epoch = time.time()  # Get current time as Unix timestamp (seconds since epoch)
    expires_in_seconds = token_result['expires_in']

    # Calculate absolute expiration time
    expiry_timestamp = current_time_epoch + expires_in_seconds
    token_info = {
        'token': token_result['access_token'],
        'expiry_time': expiry_timestamp,
        'issued_at': current_time_epoch
    }

    # Open a file in write mode ('w')
    with open(token_file, 'w', encoding='utf-8') as f:
        json.dump(token_info, f, indent=4)
    print(f"Token saved to {token_file} with expiry timestamp: {expiry_timestamp}")

if __name__ == "__main__":
    main()