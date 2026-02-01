"""Unit tests for onedrive_downloader.models module."""

import pytest
from onedrive_downloader.models import ImageItem


class TestImageItem:
    """Tests for ImageItem NamedTuple."""

    def test_create_image_item(self):
        item = ImageItem(
            filename="photo.jpg",
            download_url="https://example.com/photo.jpg",
            size=1024,
            mime_type="image/jpeg"
        )
        assert item.filename == "photo.jpg"
        assert item.download_url == "https://example.com/photo.jpg"
        assert item.size == 1024
        assert item.mime_type == "image/jpeg"

    def test_is_tuple(self):
        item = ImageItem(
            filename="test.png",
            download_url="https://example.com/test.png",
            size=2048,
            mime_type="image/png"
        )
        # NamedTuple is still a tuple
        assert isinstance(item, tuple)
        assert len(item) == 4

    def test_unpacking(self):
        item = ImageItem(
            filename="test.jpg",
            download_url="https://example.com/test.jpg",
            size=512,
            mime_type="image/jpeg"
        )
        filename, url, size, mime = item
        assert filename == "test.jpg"
        assert url == "https://example.com/test.jpg"
        assert size == 512
        assert mime == "image/jpeg"

    def test_immutable(self):
        item = ImageItem(
            filename="test.jpg",
            download_url="https://example.com/test.jpg",
            size=512,
            mime_type="image/jpeg"
        )
        with pytest.raises(AttributeError):
            item.filename = "other.jpg"

    def test_fields(self):
        assert ImageItem._fields == ('filename', 'download_url', 'size', 'mime_type')
