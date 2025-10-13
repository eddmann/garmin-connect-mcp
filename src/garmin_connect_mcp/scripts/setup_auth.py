"""Interactive authentication setup script for Garmin Connect MCP."""

from pathlib import Path

from dotenv import set_key


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
    print("✓ Success! Credentials have been saved to .env")
    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Authentication will be performed automatically when you")
    print("first run the Garmin Connect MCP server.")
    print()
    print("If you have two-factor authentication enabled, you will be")
    print("prompted for your MFA code on first login.")
    print()
    print("You can now use the Garmin Connect MCP server:")
    print("  uv run garmin-connect-mcp")
    print()


if __name__ == "__main__":
    main()
