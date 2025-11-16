"""Interactive authentication setup script for Garmin Connect MCP."""

import sys
from pathlib import Path

from dotenv import set_key

from ..auth import GarminConfig, get_token_store
from ..client import init_garmin_client


def main():
    """Run the interactive authentication setup."""
    print("=" * 60)
    print("Garmin Connect MCP - Authentication Setup")
    print("=" * 60)
    print()
    print("This script will help you set up authentication with Garmin Connect.")
    print()

    # Get Garmin credentials
    print("Enter your Garmin Connect credentials:")
    print("-" * 60)
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    if not email or not password:
        print("\nError: Email and password are required.")
        return

    # Save to .env file
    env_path = Path.cwd() / ".env"

    if not env_path.exists():
        env_path.touch()

    set_key(str(env_path), "GARMIN_EMAIL", email)
    set_key(str(env_path), "GARMIN_PASSWORD", password)

    print()
    print("✓ Credentials saved to .env")
    print()

    # Attempt authentication now to handle 2FA interactively
    print("-" * 60)
    print("Authenticating with Garmin Connect...")
    print("-" * 60)
    print()
    print("Note: If you have two-factor authentication (2FA) enabled,")
    print("you will be prompted for your MFA code below.")
    print()

    # Create config from the credentials we just saved
    config = GarminConfig(garmin_email=email, garmin_password=password)

    # Attempt to initialize client (will prompt for MFA if needed)
    client = init_garmin_client(config)

    if client is None:
        print()
        print("✗ Authentication failed!")
        print()
        print("Please check your credentials and try again.")
        print("If the problem persists, visit:")
        print("  https://connect.garmin.com")
        print()
        sys.exit(1)

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("✓ Authentication successful!")
    print(f"✓ Tokens saved to: {get_token_store()}")
    print()
    print("You can now use the Garmin Connect MCP server:")
    print("  uv run garmin-connect-mcp")
    print()
    print("Your authentication tokens will be reused automatically.")
    print("Re-run this script only if you need to change credentials")
    print("or re-authenticate.")
    print()


if __name__ == "__main__":
    main()
