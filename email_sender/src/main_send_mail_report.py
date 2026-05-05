import json
import time
import subprocess
import sys
from pathlib import Path

# Resolve base paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = BASE_DIR / "script"
TOKEN_FILE = ROOT_DIR / "live_token" / "token.json"

#proxy config is in added develop branch code

def is_token_valid():
    """
    Returns True if token exists and is not expired
    """
    if not TOKEN_FILE.exists():
        return False

    data = json.loads(TOKEN_FILE.read_text())
    expires_at = data.get("expiry_time")

    if not expires_at:
        return False

    return int(time.time()) < int(expires_at)


def run_auth():
    """
    Runs auth.py to generate token.json
    """
    print("Token missing or expired. Running auth.py...")

    result = subprocess.run(
        [sys.executable, SCRIPT_DIR / "auth.py"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Auth failed:")
        print(result.stderr)
        raise RuntimeError("Authentication failed")

    print("Auth completed successfully")


def run_send_mail():
    """
    Runs send_mail.py using existing token
    """
    print("Running send_mail.py...")

    # Forward CLI arguments (excluding trigger.py itself)
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "send_mail.py"),
        *sys.argv[1:]
    ]

    result = subprocess.run(
        cmd,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        print("Mail sending failed:")
        print(result.stderr)
        raise RuntimeError("Mail sending failed")

    print("Mail sent successfully")

def main():
    if not is_token_valid():
        run_auth()
    else:
        print("Valid token found. Skipping auth.")

    run_send_mail()

if __name__ == "__main__":
    main()
