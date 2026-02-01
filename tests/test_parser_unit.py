"""Unit tests for onedrive_downloader.parser module."""

import pytest
from onedrive_downloader.parser import OneDriveURLParser, parse_and_encode_url


class TestOneDriveURLParser:
    """Tests for OneDriveURLParser class."""

    def test_validates_onedrive_live_com(self):
        parser = OneDriveURLParser("https://onedrive.live.com/?id=test")
        assert parser.validate() is True

    def test_validates_1drv_ms(self):
        parser = OneDriveURLParser("https://1drv.ms/a/c/test")
        assert parser.validate() is True

    def test_validates_onedrive_com(self):
        parser = OneDriveURLParser("https://onedrive.com/share/test")
        assert parser.validate() is True

    def test_rejects_invalid_domain(self):
        parser = OneDriveURLParser("https://example.com/test")
        assert parser.validate() is False

        parser = OneDriveURLParser("https://google.com/drive")
        assert parser.validate() is False

    def test_get_encoded_sharing_url_valid(self):
        parser = OneDriveURLParser("https://1drv.ms/a/c/test")
        result = parser.get_encoded_sharing_url()
        assert result.startswith("u!")

    def test_get_encoded_sharing_url_invalid_raises(self):
        parser = OneDriveURLParser("https://example.com/test")
        with pytest.raises(ValueError) as exc_info:
            parser.get_encoded_sharing_url()
        assert "Invalid OneDrive URL" in str(exc_info.value)


class TestParseAndEncodeUrl:
    """Tests for parse_and_encode_url convenience function."""

    def test_valid_url(self):
        result = parse_and_encode_url("https://1drv.ms/a/c/test123")
        assert result.startswith("u!")

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            parse_and_encode_url("https://example.com/test")

    def test_preserves_full_url(self):
        url = "https://onedrive.live.com/redir?resid=ABC123&authkey=XYZ"
        result = parse_and_encode_url(url)
        # The encoded result should be deterministic
        assert result.startswith("u!")
        # Same input should give same output
        assert result == parse_and_encode_url(url)
