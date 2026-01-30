"""Utility functions for OneDrive Album Downloader."""

import re
import base64
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote


def sanitize_filename(filename):
    """
    Remove invalid characters from filenames for cross-platform compatibility.

    Args:
        filename: The original filename

    Returns:
        A sanitized filename safe for all platforms
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Limit length to 255 characters (common filesystem limit)
    if len(sanitized) > 255:
        name, ext = Path(sanitized).stem, Path(sanitized).suffix
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext

    return sanitized or 'unnamed'


def encode_sharing_url(sharing_url):
    """
    Encode a OneDrive sharing URL for use with the Microsoft Graph Shares API.

    The Shares API requires sharing URLs to be encoded using base64url encoding
    with a 'u!' prefix and without padding.

    Reference: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/shares_get

    Args:
        sharing_url: The OneDrive sharing URL

    Returns:
        Encoded sharing token in format: u!{base64url_encoded_url}

    Example:
        >>> url = "https://onedrive.live.com/?id=..."
        >>> encode_sharing_url(url)
        'u!aHR0cHM6Ly9vbmVkcml2ZS5saXZlLmNvbS8_aWQ9Li4u'
    """
    # Encode URL to bytes
    url_bytes = sharing_url.encode('utf-8')

    # Base64 URL-safe encode (replaces + with - and / with _)
    encoded = base64.urlsafe_b64encode(url_bytes).decode('utf-8')

    # Remove padding (=) as per Microsoft Graph API requirements
    encoded = encoded.rstrip('=')

    # Add the required 'u!' prefix
    return f'u!{encoded}'


def parse_album_id(album_url):
    """
    Extract the album ID from a OneDrive album URL.

    Args:
        album_url: OneDrive album URL

    Returns:
        Album ID if found, None otherwise

    Example:
        >>> url = "https://onedrive.live.com/?view=8&photosData=%2Falbum%2FEXAMPLE_ID"
        >>> parse_album_id(url)
        'EXAMPLE_ID'
    """
    try:
        parsed = urlparse(album_url)
        params = parse_qs(parsed.query)

        # Try to extract from photosData parameter
        if 'photosData' in params:
            photos_data = unquote(params['photosData'][0])
            # Extract ID from path like /album/{ID}
            match = re.search(r'/album/([^/?]+)', photos_data)
            if match:
                return match.group(1)

        # Try to extract from id parameter
        if 'id' in params:
            return params['id'][0]

        # Try to extract from resid parameter
        if 'resid' in params:
            return params['resid'][0]

    except Exception:
        pass

    return None


def get_image_extension(filename, mime_type=None):
    """
    Determine the appropriate file extension for an image.

    Args:
        filename: Original filename
        mime_type: Optional MIME type of the image

    Returns:
        File extension with leading dot (e.g., '.jpg')
    """
    # First try to get extension from filename
    if filename:
        ext = Path(filename).suffix.lower()
        if ext:
            return ext

    # Fallback to MIME type
    mime_to_ext = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/bmp': '.bmp',
        'image/tiff': '.tiff',
        'image/heic': '.heic',
        'image/heif': '.heif',
    }

    if mime_type:
        return mime_to_ext.get(mime_type.lower(), '.jpg')

    # Default fallback
    return '.jpg'


def format_size(size_bytes):
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Format with appropriate decimal places
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def is_image_file(item):
    """
    Check if a OneDrive item is an image file.

    Args:
        item: OneDrive item dict from Graph API

    Returns:
        True if the item is an image, False otherwise
    """
    # Check if it has the 'image' facet
    if 'image' in item:
        return True

    # Check MIME type
    mime_type = item.get('file', {}).get('mimeType', '')
    if mime_type.startswith('image/'):
        return True

    # Check file extension
    name = item.get('name', '')
    ext = Path(name).suffix.lower()
    from onedrive_downloader.config import SUPPORTED_IMAGE_EXTENSIONS
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return True

    return False
