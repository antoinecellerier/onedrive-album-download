"""Data models for OneDrive Album Downloader."""

from typing import NamedTuple


class ImageItem(NamedTuple):
    """Represents an image item from OneDrive."""
    filename: str
    download_url: str
    size: int
    mime_type: str
