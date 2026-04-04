#!/usr/bin/env python3
"""
Validate WhatsApp Cloud API configuration.

Checks environment variables and tests API connectivity.

Usage:
    python validate_config.py
    python validate_config.py --env-file /path/to/.env
"""

import argparse
import os
import re
import sys

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment only.")
    load_dotenv = None

GRAPH_API = "https://graph.facebook.com/v21.0"

REQUIRED_VARS = [
    ("WHATSAPP_TOKEN", "Access token for WhatsApp Cloud API"),
    ("PHONE_NUMBER_ID", "Phone Number ID from API Setup"),
    ("WABA_ID", "WhatsApp Business Account ID"),
    ("APP_SECRET", "App Secret from App Settings > Basic"),
    ("VERIFY_TOKEN", "Custom token for webhook verification"),
]

# Any token-like substring (>=20 alphanumeric chars) is redacted from output.
_SECRET_RE = re.compile(r"[A-Za-z0-9_\-]{20,}")


def _redact(text: str) -> str:
    """Redact anything that looks like a credential from free-form text."""
    return _SECRET_RE.sub("[REDACTED]", text)


def check_env_vars() -> tuple[bool, list[str]]:
    """Check if all required environment variables are set."""
    missing = []
    for var_name, description in REQUIRED_VARS:
        value = os.environ.get(var_name)
        if not value or value.startswith("your_"):
            missing.append(f"  {var_name} - {description}")

    return len(missing) == 0, missing


def _auth_headers() -> dict:
    """Build authorization headers without ever binding the token to a named local."""
    return {"Authorization": f"Bearer {os.environ.get('WHATSAPP_TOKEN', '')}"}


def test_api_connection() -> tuple[bool, dict]:
    """Test connection to WhatsApp Cloud API.

    Returns (ok, info) where info contains only non-sensitive diagnostic fields.
    """
    phone_id = os.environ.get("PHONE_NUMBER_ID", "")

    try:
        response = httpx.get(
            f"{GRAPH_API}/{phone_id}",
            params={"fields": "verified_name,code_verification_status,display_phone_number,quality_rating"},
            headers=_auth_headers(),
            timeout=10.0,
        )
    except httpx.ConnectError:
        return False, {"error": "Connection failed. Check your internet connection."}
    except httpx.TimeoutException:
        return False, {"error": "Request timed out after 10 seconds."}
    except Exception as e:
        return False, {"error": _redact(f"Unexpected error: {e}")}

    if response.status_code != 200:
        err = response.json().get("error", {})
        return False, {
            "error": f"API Error {err.get('code', '?')}: {err.get('message', 'Unknown')}"
        }

    data = response.json()
    # Only expose the specific non-sensitive fields we asked for.
    return True, {
        "phone": str(data.get("display_phone_number", "N/A")),
        "name": str(data.get("verified_name", "N/A")),
        "status": str(data.get("code_verification_status", "N/A")),
        "quality": str(data.get("quality_rating", "N/A")),
    }


def test_waba_access() -> tuple[bool, dict]:
    """Test access to WhatsApp Business Account.

    Returns (ok, info) where info only contains aggregate counts — never raw response data.
    """
    waba_id = os.environ.get("WABA_ID", "")

    try:
        response = httpx.get(
            f"{GRAPH_API}/{waba_id}/phone_numbers",
            headers=_auth_headers(),
            timeout=10.0,
        )
    except Exception as e:
        return False, {"error": _redact(f"Error: {e}")}

    if response.status_code != 200:
        err = response.json().get("error", {})
        return False, {
            "error": f"API Error {err.get('code', '?')}: {err.get('message', 'Unknown')}"
        }

    count = len(response.json().get("data", []))
    return True, {"phone_number_count": count}


def main():
    parser = argparse.ArgumentParser(description="Validate WhatsApp Cloud API configuration")
    parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    args = parser.parse_args()

    # Load environment
    if load_dotenv and os.path.exists(args.env_file):
        load_dotenv(args.env_file)
        print(f"Loaded: {args.env_file}")
    elif not os.path.exists(args.env_file):
        print(f"Warning: {args.env_file} not found. Using system environment.")

    print()
    print("=" * 50)
    print("WhatsApp Cloud API - Configuration Validator")
    print("=" * 50)
    print()

    all_ok = True

    # Check 1: Environment variables
    print("[1/3] Checking environment variables...")
    env_ok, missing = check_env_vars()
    if env_ok:
        print("  OK - All required variables are set")
    else:
        print("  FAIL - Missing variables:")
        for m in missing:
            print(f"    {m}")
        all_ok = False

    print()

    if not env_ok:
        print("Cannot test API without required variables. Fix the above and retry.")
        sys.exit(1)

    # Check 2: API connection
    print("[2/3] Testing API connection (Phone Number)...")
    api_ok, api_info = test_api_connection()
    if api_ok:
        print("  OK - Connected successfully")
        # Print only the explicit, non-sensitive fields we captured.
        print(f"  Phone:   {api_info.get('phone', 'N/A')}")
        print(f"  Name:    {api_info.get('name', 'N/A')}")
        print(f"  Status:  {api_info.get('status', 'N/A')}")
        print(f"  Quality: {api_info.get('quality', 'N/A')}")
    else:
        print(f"  FAIL - {_redact(str(api_info.get('error', 'unknown error')))}")
        all_ok = False

    print()

    # Check 3: WABA access
    print("[3/3] Testing WABA access...")
    waba_ok, waba_info = test_waba_access()
    if waba_ok:
        print(f"  OK - WABA accessible. {waba_info.get('phone_number_count', 0)} phone number(s) found.")
    else:
        print(f"  FAIL - {_redact(str(waba_info.get('error', 'unknown error')))}")
        all_ok = False

    print()
    print("=" * 50)
    if all_ok:
        print("All checks passed! Your configuration is valid.")
        print("You can start sending messages.")
    else:
        print("Some checks failed. Please fix the issues above.")
        print("Need help? Read: references/setup-guide.md")
    print("=" * 50)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
