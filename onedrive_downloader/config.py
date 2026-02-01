"""Configuration constants for OneDrive Album Downloader."""

from onedrive_downloader import __version__

# Microsoft Graph API
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Default settings
DEFAULT_OUTPUT_DIR = "./downloads"
DEFAULT_CONCURRENT_DOWNLOADS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_CHUNK_SIZE = 65536  # 64KB - optimized for download speed

# Token cache
TOKEN_CACHE_FILE = ".token_cache.json"

# Supported image MIME types
SUPPORTED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/heic",
    "image/heif",
]

# Supported image extensions
SUPPORTED_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
    ".heic",
    ".heif",
]

# HTTP headers
USER_AGENT = f"OneDriveAlbumDownloader/{__version__}"

# OAuth settings
OAUTH_SCOPES = ["Files.Read.All", "offline_access"]
OAUTH_AUTHORITY = "https://login.microsoftonline.com/common"
