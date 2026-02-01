"""Microsoft Graph API client for OneDrive operations."""

import requests
from typing import List, Dict, Any
from onedrive_downloader.config import GRAPH_API_ENDPOINT, DEFAULT_TIMEOUT_SECONDS, USER_AGENT
from onedrive_downloader.models import ImageItem
from onedrive_downloader.utils import is_image_file


class OneDriveAPIClient:
    """Client for interacting with Microsoft Graph API."""

    def __init__(self, access_token):
        """
        Initialize the API client with an access token.

        Args:
            access_token: OAuth access token for Microsoft Graph API
        """
        self.access_token = access_token
        self.base_url = GRAPH_API_ENDPOINT
        self.timeout = DEFAULT_TIMEOUT_SECONDS

        # Create session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT
        })

    def get_shared_item(self, encoded_sharing_url):
        """
        Get metadata for a shared OneDrive item using its encoded sharing URL.

        API Reference:
        https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/shares_get

        Args:
            encoded_sharing_url: Encoded sharing URL (format: u!{base64url})

        Returns:
            Dict containing the shared item metadata

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/shares/{encoded_sharing_url}/driveItem"

        response = self.session.get(url, timeout=self.timeout)

        if response.status_code == 401:
            raise Exception(
                "Authentication failed. Your access token may have expired. "
                "Try deleting .token_cache.json and authenticating again."
            )
        elif response.status_code == 404:
            raise Exception(
                "Shared item not found. The sharing URL may be invalid or expired."
            )

        response.raise_for_status()
        return response.json()

    def list_children(self, drive_id, item_id):
        """
        List all children (files/folders) of a OneDrive item.

        Handles pagination automatically to retrieve all items.

        API Reference:
        https://learn.microsoft.com/en-us/graph/api/driveitem-list-children

        Args:
            drive_id: The drive ID containing the item
            item_id: The item ID to list children for

        Returns:
            List of item dictionaries

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/children"
        all_items = []

        while url:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Add items from this page
            all_items.extend(data.get('value', []))

            # Check for next page
            url = data.get('@odata.nextLink')

        return all_items

    def list_shared_children(self, encoded_sharing_url):
        """
        List all children of a shared item using the Shares API.

        This is used for shared albums where direct drive access may not work.
        Handles pagination automatically to retrieve all items.

        Args:
            encoded_sharing_url: Encoded sharing URL (format: u!{base64url})

        Returns:
            List of item dictionaries

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/shares/{encoded_sharing_url}/driveItem/children"
        all_items = []

        while url:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Add items from this page
            all_items.extend(data.get('value', []))

            # Check for next page
            url = data.get('@odata.nextLink')

        return all_items

    def get_image_items(self, drive_id: str, item_id: str, recursive: bool = True) -> List[ImageItem]:
        """
        Get all image items from a OneDrive folder/album.

        Args:
            drive_id: The drive ID
            item_id: The folder/album item ID
            recursive: If True, recursively search subfolders

        Returns:
            List of ImageItem objects

        Raises:
            requests.HTTPError: If API requests fail
        """
        children = self.list_children(drive_id, item_id)
        image_items: List[ImageItem] = []

        for item in children:
            # Check if it's a folder
            if 'folder' in item and recursive:
                # Recursively get images from subfolder
                subfolder_images = self.get_image_items(
                    drive_id,
                    item['id'],
                    recursive=True
                )
                image_items.extend(subfolder_images)

            # Check if it's an image file
            elif is_image_file(item):
                # Get download URL
                download_url = item.get('@microsoft.graph.downloadUrl')

                if download_url:
                    image_items.append(ImageItem(
                        filename=item['name'],
                        download_url=download_url,
                        size=item.get('size', 0),
                        mime_type=item.get('file', {}).get('mimeType', 'image/jpeg'),
                    ))

        return image_items

    def get_shared_album_images(self, encoded_sharing_url: str, recursive: bool = False) -> List[ImageItem]:
        """
        Get all image items from a shared album using the Shares API.

        This method works entirely through the Shares API path and doesn't
        require direct drive access.

        Args:
            encoded_sharing_url: Encoded sharing URL (format: u!{base64url})
            recursive: If True, recursively search subfolders (currently only
                       top-level items are returned via Shares API)

        Returns:
            List of ImageItem objects

        Raises:
            requests.HTTPError: If API requests fail
        """
        children = self.list_shared_children(encoded_sharing_url)
        image_items: List[ImageItem] = []

        for item in children:
            # Check if it's an image file
            if is_image_file(item):
                # Get download URL
                download_url = item.get('@microsoft.graph.downloadUrl')

                if download_url:
                    image_items.append(ImageItem(
                        filename=item['name'],
                        download_url=download_url,
                        size=item.get('size', 0),
                        mime_type=item.get('file', {}).get('mimeType', 'image/jpeg'),
                    ))

        return image_items

    def get_album_info(self, encoded_sharing_url):
        """
        Get information about an album (name, image count, etc.).

        Args:
            encoded_sharing_url: Encoded sharing URL

        Returns:
            Dict with album information: {
                'name': str,
                'drive_id': str,
                'item_id': str,
                'item_count': int (if folder),
                'encoded_url': str
            }

        Raises:
            requests.HTTPError: If API requests fail
        """
        shared_item = self.get_shared_item(encoded_sharing_url)

        info = {
            'name': shared_item.get('name', 'Unknown Album'),
            'drive_id': shared_item['parentReference']['driveId'],
            'item_id': shared_item['id'],
            'encoded_url': encoded_sharing_url,
        }

        # Add folder-specific info
        if 'folder' in shared_item:
            info['item_count'] = shared_item['folder'].get('childCount', 0)

        return info

    def test_connection(self):
        """
        Test the API connection and token validity.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple test request to /me/drive
            url = f"{self.base_url}/me/drive"
            response = self.session.get(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False


def get_images_from_album(access_token, encoded_sharing_url):
    """
    Convenience function to get all images from an album.

    Args:
        access_token: OAuth access token
        encoded_sharing_url: Encoded sharing URL

    Returns:
        Tuple of (album_info, image_items)
        - album_info: Dict with album metadata
        - image_items: List of (filename, download_url, file_size, mime_type)

    Example:
        >>> from onedrive_downloader.parser import parse_and_encode_url
        >>> encoded = parse_and_encode_url("https://1drv.ms/a/c/YOUR_ALBUM_ID")
        >>> album_info, images = get_images_from_album(token, encoded)
        >>> print(f"Found {len(images)} images in {album_info['name']}")
    """
    client = OneDriveAPIClient(access_token)

    # Get album info
    album_info = client.get_album_info(encoded_sharing_url)

    # Get all images via Shares API
    image_items = client.get_shared_album_images(encoded_sharing_url)

    return album_info, image_items
