"""Parser for OneDrive sharing URLs."""

from urllib.parse import urlparse
from onedrive_downloader.utils import encode_sharing_url


class OneDriveURLParser:
    """Parser for OneDrive album and sharing URLs."""

    def __init__(self, url):
        """
        Initialize the parser with a OneDrive URL.

        Args:
            url: OneDrive sharing or album URL
        """
        self.url = url
        self.parsed_url = urlparse(url)

    def validate(self):
        """
        Validate that the URL is a OneDrive URL.

        Returns:
            True if valid, False otherwise
        """
        valid_hosts = [
            'onedrive.live.com',
            '1drv.ms',
            'onedrive.com',
        ]

        return self.parsed_url.netloc.lower() in valid_hosts

    def get_encoded_sharing_url(self):
        """
        Get the encoded sharing URL for use with Microsoft Graph Shares API.

        Returns:
            Encoded sharing URL in format: u!{base64url}

        Raises:
            ValueError: If URL is invalid
        """
        if not self.validate():
            raise ValueError(
                f"Invalid OneDrive URL. Must be from onedrive.live.com, "
                f"1drv.ms, or onedrive.com. Got: {self.parsed_url.netloc}"
            )

        return encode_sharing_url(self.url)


def parse_and_encode_url(url):
    """
    Parse and encode a OneDrive URL for the Shares API.

    This is a convenience function that combines validation and encoding.

    Args:
        url: OneDrive sharing or album URL

    Returns:
        Encoded sharing URL ready for Graph API

    Raises:
        ValueError: If URL is invalid

    Example:
        >>> url = "https://onedrive.live.com/?id=..."
        >>> encoded = parse_and_encode_url(url)
        >>> encoded.startswith('u!')
        True
    """
    parser = OneDriveURLParser(url)
    return parser.get_encoded_sharing_url()
