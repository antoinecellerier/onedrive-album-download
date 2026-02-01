"""Unit tests for onedrive_downloader.utils module."""

import pytest
from onedrive_downloader.utils import (
    sanitize_filename,
    encode_sharing_url,
    parse_album_id,
    get_image_extension,
    format_size,
    is_image_file,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_basic_filename(self):
        assert sanitize_filename("photo.jpg") == "photo.jpg"

    def test_removes_invalid_chars(self):
        assert sanitize_filename('file<>:"/\\|?*.jpg') == "file_________.jpg"

    def test_strips_leading_trailing_dots_spaces(self):
        assert sanitize_filename("  ..photo.jpg.. ") == "photo.jpg"

    def test_empty_becomes_unnamed(self):
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("...") == "unnamed"

    def test_truncates_long_filenames(self):
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".jpg")

    def test_preserves_unicode(self):
        assert sanitize_filename("фото_日本語.jpg") == "фото_日本語.jpg"


class TestEncodeSharingUrl:
    """Tests for encode_sharing_url function."""

    def test_returns_u_prefix(self):
        result = encode_sharing_url("https://example.com")
        assert result.startswith("u!")

    def test_base64url_encoding(self):
        # Known encoding test
        url = "https://onedrive.live.com/?id=test"
        result = encode_sharing_url(url)
        assert result.startswith("u!")
        # Should not have padding
        assert "=" not in result

    def test_no_padding_chars(self):
        # Test various URL lengths to ensure no padding
        for length in range(10, 50):
            url = "x" * length
            result = encode_sharing_url(url)
            assert "=" not in result


class TestParseAlbumId:
    """Tests for parse_album_id function."""

    def test_extracts_from_photos_data(self):
        url = "https://onedrive.live.com/?view=8&photosData=%2Falbum%2FTEST_ID_123"
        assert parse_album_id(url) == "TEST_ID_123"

    def test_extracts_from_id_param(self):
        url = "https://onedrive.live.com/?id=ITEM_ID_456"
        assert parse_album_id(url) == "ITEM_ID_456"

    def test_extracts_from_resid_param(self):
        url = "https://onedrive.live.com/?resid=RES_ID_789"
        assert parse_album_id(url) == "RES_ID_789"

    def test_returns_none_for_invalid_url(self):
        assert parse_album_id("https://example.com") is None
        assert parse_album_id("not a url") is None

    def test_returns_none_for_empty(self):
        assert parse_album_id("") is None


class TestGetImageExtension:
    """Tests for get_image_extension function."""

    def test_extracts_from_filename(self):
        assert get_image_extension("photo.jpg") == ".jpg"
        assert get_image_extension("image.PNG") == ".png"

    def test_uses_mime_type_fallback(self):
        assert get_image_extension("", "image/jpeg") == ".jpg"
        assert get_image_extension("", "image/png") == ".png"
        assert get_image_extension("", "image/gif") == ".gif"

    def test_defaults_to_jpg(self):
        assert get_image_extension("") == ".jpg"
        assert get_image_extension("", "unknown/type") == ".jpg"

    def test_filename_takes_priority(self):
        assert get_image_extension("photo.png", "image/jpeg") == ".png"


class TestFormatSize:
    """Tests for format_size function."""

    def test_zero_bytes(self):
        assert format_size(0) == "0 B"

    def test_bytes(self):
        assert format_size(500) == "500 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.00 KB"
        assert format_size(1536) == "1.50 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.00 MB"
        assert format_size(1024 * 1024 * 2.5) == "2.50 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_terabytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"


class TestIsImageFile:
    """Tests for is_image_file function."""

    def test_detects_image_facet(self):
        item = {"name": "photo", "image": {"width": 100, "height": 100}}
        assert is_image_file(item) is True

    def test_detects_image_mime_type(self):
        item = {"name": "photo", "file": {"mimeType": "image/jpeg"}}
        assert is_image_file(item) is True

    def test_detects_image_extension(self):
        item = {"name": "photo.jpg"}
        assert is_image_file(item) is True

        item = {"name": "photo.PNG"}
        assert is_image_file(item) is True

    def test_rejects_non_image(self):
        item = {"name": "document.pdf", "file": {"mimeType": "application/pdf"}}
        assert is_image_file(item) is False

    def test_rejects_folder(self):
        item = {"name": "folder", "folder": {"childCount": 5}}
        assert is_image_file(item) is False
