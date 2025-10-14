"""Garmin Connect API client wrapper with error handling."""

import sys
from pathlib import Path
from typing import Any

from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError

from .auth import GarminConfig, get_token_base64_path, get_token_store


class GarminAPIError(Exception):
    """Custom exception for Garmin API errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class GarminRateLimitError(GarminAPIError):
    """Exception raised when rate limit is exceeded (HTTP 429)."""

    def __init__(self, original_error: Exception | None = None):
        super().__init__(
            "Rate limit exceeded. Please wait a few minutes before trying again.",
            original_error=original_error,
        )


class GarminNotFoundError(GarminAPIError):
    """Exception raised when resource is not found (HTTP 404)."""

    def __init__(self, resource: str = "Resource", original_error: Exception | None = None):
        super().__init__(
            f"{resource} not found. Please check the ID or date and try again.",
            original_error=original_error,
        )


class GarminAuthenticationError(GarminAPIError):
    """Exception raised when authentication fails (HTTP 401/403)."""

    def __init__(self, original_error: Exception | None = None):
        super().__init__(
            "Authentication failed. Please run 'garmin-connect-mcp-auth' to re-authenticate.",
            original_error=original_error,
        )


def init_garmin_client(config: GarminConfig) -> Garmin | None:
    """
    Initialize and authenticate Garmin client.

    Follows the authentication pattern from the original garmin_mcp project:
    1. Try token-based login first
    2. Fall back to credential-based login with MFA support
    3. Persist tokens for future use

    Args:
        config: Garmin configuration with credentials

    Returns:
        Authenticated Garmin client or None on failure
    """
    try:
        tokenstore = get_token_store()

        # Try token-based login first
        try:
            # Check if tokens exist
            token_path = Path(tokenstore)
            if token_path.exists() and any(token_path.iterdir()):
                # Try to login with existing tokens
                garmin = Garmin()
                garmin.login(tokenstore)
                print("Logged in using token data from directory.", file=sys.stderr)
                return garmin
            else:
                raise FileNotFoundError("No tokens found")

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError) as e:
            # Token login failed, try credential login
            print(f"Token login failed: {e}. Attempting credential-based login...", file=sys.stderr)

            # Create Garmin client with credentials
            garmin = Garmin(config.garmin_email, config.garmin_password)

            # Attempt login
            result = garmin.login()

            # Check if MFA is needed
            if result and len(result) >= 2:
                oauth1_token, oauth2_token = result

                # Check if MFA is required (oauth1_token will have mfa_token)
                mfa_token = getattr(oauth1_token, "mfa_token", None)
                if mfa_token:
                    print("MFA required. Please enter your MFA code.", file=sys.stderr)
                    mfa_code = input("MFA one-time code: ")

                    # Resume login with MFA code
                    garmin.resume_login(result, mfa_code)

            # Save tokens for future use
            garmin.garth.dump(tokenstore)
            print(f"OAuth tokens saved to directory: {tokenstore}", file=sys.stderr)

            # Also save base64 encoded tokens
            token_base64_path = get_token_base64_path()
            Path(token_base64_path).write_text(garmin.garth.dumps())
            print(f"OAuth tokens encoded as base64: {token_base64_path}", file=sys.stderr)

            return garmin

    except GarminConnectAuthenticationError as err:
        print(f"Authentication error: {err}", file=sys.stderr)
        return None

    except Exception as err:
        print(f"Unexpected error during login: {err}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return None


class GarminClientWrapper:
    """Wrapper around Garmin client for consistent error handling."""

    def __init__(self, client: Garmin):
        self.client = client

    def safe_call(self, method_name: str, *args, **kwargs) -> Any:
        """
        Safely call a Garmin client method with error handling.

        This method uses `Any` as the return type because it dynamically proxies calls
        to the external garminconnect library, which doesn't have type stubs. The actual
        return type depends on which Garmin API method is called.

        Args:
            method_name: Name of the Garmin client method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Method result or raises GarminAPIError

        Raises:
            GarminAuthenticationError: Authentication failed (401/403)
            GarminNotFoundError: Resource not found (404)
            GarminRateLimitError: Rate limit exceeded (429)
            GarminAPIError: Other API errors
        """
        try:
            method = getattr(self.client, method_name)
            return method(*args, **kwargs)
        except AttributeError as e:
            raise GarminAPIError(
                f"Method '{method_name}' not found on Garmin client", original_error=e
            ) from e
        except GarminConnectAuthenticationError as e:
            raise GarminAuthenticationError(original_error=e) from e
        except GarthHTTPError as e:
            # Parse HTTP status code from error
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                raise GarminRateLimitError(original_error=e) from e
            elif "404" in error_str or "Not Found" in error_str:
                raise GarminNotFoundError(original_error=e) from e
            elif "401" in error_str or "403" in error_str or "Unauthorized" in error_str:
                raise GarminAuthenticationError(original_error=e) from e
            else:
                raise GarminAPIError(f"Garmin API error: {str(e)}", original_error=e) from e
        except Exception as e:
            raise GarminAPIError(f"Unexpected error: {str(e)}", original_error=e) from e
