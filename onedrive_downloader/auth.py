"""OAuth authentication for Microsoft Graph API."""

import json
import os
from pathlib import Path
from msal import PublicClientApplication, SerializableTokenCache
from onedrive_downloader.config import TOKEN_CACHE_FILE, OAUTH_SCOPES


class OneDriveAuthenticator:
    """Handle OAuth 2.0 authentication for OneDrive/Microsoft Graph API."""

    def __init__(self, config_path='config.json'):
        """
        Initialize the authenticator with OAuth configuration.

        Args:
            config_path: Path to config file with client_id, client_secret, etc.

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is missing required fields
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                f"Please copy config.json.example to config.json and fill in your credentials."
            )

        with open(self.config_path) as f:
            self.config = json.load(f)

        # Validate required fields
        required_fields = ['client_id', 'authority']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Config file missing required field: {field}")

        # Use scopes from config or default
        self.scopes = self.config.get('scopes', OAUTH_SCOPES)

        # Initialize token cache
        self.cache = SerializableTokenCache()
        self._load_token_cache()

        # Initialize MSAL application
        self.app = PublicClientApplication(
            client_id=self.config['client_id'],
            authority=self.config['authority'],
            token_cache=self.cache
        )

    def _load_token_cache(self):
        """Load token cache from file if it exists."""
        cache_path = Path(TOKEN_CACHE_FILE)
        if cache_path.exists():
            with open(cache_path) as f:
                self.cache.deserialize(f.read())

    def _save_token_cache(self):
        """Save token cache to file."""
        if self.cache.has_state_changed:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                f.write(self.cache.serialize())

    def acquire_token_device_code(self):
        """
        Acquire access token using device code flow (user-friendly for CLI).

        This flow displays a code and URL for the user to authenticate in a browser.

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        # Filter out reserved scopes (MSAL handles these automatically)
        reserved_scopes = {'offline_access', 'openid', 'profile'}
        filtered_scopes = [s for s in self.scopes if s not in reserved_scopes]

        # Initiate device flow
        flow = self.app.initiate_device_flow(scopes=filtered_scopes)

        if "user_code" not in flow:
            error_msg = flow.get("error_description", flow.get("error", "Unknown error"))
            raise ValueError(
                f"Failed to create device flow: {error_msg}\n"
                "Check your client_id and authority in config.json\n"
                "Also ensure your Azure AD app is configured to allow public client flows:\n"
                "Authentication -> Allow public client flows -> Yes"
            )

        # Display instructions to user
        import sys
        print("\n" + "="*60)
        print("AUTHENTICATION REQUIRED")
        print("="*60)
        print(flow["message"])
        print("="*60 + "\n")
        sys.stdout.flush()

        # Wait for user to authenticate
        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self._save_token_cache()
            return result["access_token"]
        else:
            error = result.get("error", "Unknown error")
            error_desc = result.get("error_description", "No description")
            raise Exception(f"Authentication failed: {error} - {error_desc}")

    def acquire_token_silent(self):
        """
        Try to acquire token silently from cache.

        Returns:
            Access token string if successful, None otherwise
        """
        # Filter out reserved scopes (MSAL handles these automatically)
        reserved_scopes = {'offline_access', 'openid', 'profile'}
        filtered_scopes = [s for s in self.scopes if s not in reserved_scopes]

        accounts = self.app.get_accounts()

        if accounts:
            # Try to get token silently for the first account
            result = self.app.acquire_token_silent(
                scopes=filtered_scopes,
                account=accounts[0]
            )

            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]

        return None

    def get_access_token(self):
        """
        Get a valid access token (from cache or by authenticating).

        This is the main method to use. It will:
        1. Try to get token from cache
        2. If not available, prompt user to authenticate

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        # Try to get token silently first
        token = self.acquire_token_silent()

        if token:
            return token

        # If no cached token, authenticate with device code flow
        return self.acquire_token_device_code()

    def clear_cache(self):
        """Clear the token cache (forces re-authentication next time)."""
        cache_path = Path(TOKEN_CACHE_FILE)
        if cache_path.exists():
            cache_path.unlink()
            print(f"Token cache cleared: {TOKEN_CACHE_FILE}")


def get_authenticated_token(config_path='config.json'):
    """
    Convenience function to get an authenticated access token.

    Args:
        config_path: Path to OAuth config file

    Returns:
        Access token string

    Example:
        >>> token = get_authenticated_token()
        >>> # Use token with Graph API
    """
    authenticator = OneDriveAuthenticator(config_path)
    return authenticator.get_access_token()
