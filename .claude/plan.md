# OneDrive Album Downloader - Implementation Plan (OAuth API Approach)

## Overview
Create a Python utility to download all images from OneDrive albums using the official Microsoft Graph API with OAuth authentication.

Example album URL:
```
https://onedrive.live.com/?view=8&photosData=%2Falbum%2FFD6FC85F3C2441AF%21s837023545ff540c1aa227a96720fd6a3
```

## Technical Approach

### Core Strategy: Microsoft Graph API with OAuth 2.0
Use the official OneDrive API through Microsoft Graph:
1. **OAuth 2.0 Authentication** - Get user consent and access token
2. **Shares API** - Convert sharing URL to driveItem ID
3. **Graph API** - Enumerate all images in the shared album
4. **Concurrent Downloads** - Use aiohttp for efficient downloads

### Authentication Flow
Since the Shares API requires authentication even for public content, we'll use:
- **Device Code Flow** (user-friendly for CLI tools)
- Or **Authorization Code Flow** (more common, requires browser)
- Store and refresh tokens for subsequent runs

## Project Structure

```
onedrive-album-download/
├── .gitignore
├── .env.example              # Example environment variables
├── README.md
├── requirements.txt
├── config.json.example       # Example OAuth config
├── onedrive_downloader/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: python -m onedrive_downloader
│   ├── cli.py               # CLI interface with Click
│   ├── auth.py              # OAuth authentication handler
│   ├── api.py               # Microsoft Graph API client
│   ├── parser.py            # Parse OneDrive URLs and extract share tokens
│   ├── downloader.py        # Async image downloader
│   ├── utils.py             # Helper functions
│   └── config.py            # Configuration constants
└── tests/
    ├── __init__.py
    └── test_api.py
```

## Dependencies (requirements.txt)

```
msal>=1.25.0               # Microsoft Authentication Library
requests>=2.31.0           # HTTP client for Graph API calls
aiohttp>=3.9.0            # Async HTTP client for downloads
aiofiles>=23.2.0          # Async file I/O
click>=8.1.0              # CLI framework
tqdm>=4.66.0              # Progress bars
python-dotenv>=1.0.0      # Environment variable management
```

## OAuth Application Setup

### Prerequisites
User must create a Microsoft Azure AD application:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Configure:
   - **Name**: OneDrive Album Downloader
   - **Supported account types**: Personal Microsoft accounts
   - **Redirect URI**: `http://localhost:8080` (for auth code flow)
5. Save the **Application (client) ID**
6. Create a **Client Secret** under "Certificates & secrets"
7. Under "API permissions", add:
   - `Files.Read.All` (delegated)
   - `Files.ReadWrite.All` (delegated, if needed)
   - `offline_access` (for refresh tokens)

### Configuration File
Create `config.json`:
```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "authority": "https://login.microsoftonline.com/common",
  "redirect_uri": "http://localhost:8080",
  "scopes": ["Files.Read.All", "offline_access"]
}
```

## Implementation Phases

### Phase 1: Project Setup
1. Create directory structure
2. Create `requirements.txt`
3. Create `.gitignore` (exclude tokens, config files)
4. Create `.env.example` and `config.json.example`
5. Create package structure with `__init__.py` files

### Phase 2: Configuration Module (`config.py`)
Constants and default settings:
- Default output directory: `./downloads`
- Concurrent downloads: 5
- Max retries: 3
- Graph API endpoint: `https://graph.microsoft.com/v1.0`
- Token cache file location
- Supported image MIME types

### Phase 3: Utilities Module (`utils.py`)
Helper functions:
- `sanitize_filename()` - Remove invalid filename characters
- `parse_sharing_url()` - Extract share token from OneDrive URL
- `encode_sharing_url()` - Encode sharing URL for API (base64url)
- `get_image_extension()` - Determine extension from MIME type
- `format_size()` - Human-readable file sizes

### Phase 4: URL Parser (`parser.py`)
Parse OneDrive sharing URLs:

```python
def parse_sharing_url(url):
    """
    Parse OneDrive album URL to extract share token.

    Example URL:
    https://onedrive.live.com/?view=8&photosData=%2Falbum%2FFD6FC85F3C2441AF%21s837023545ff540c1aa227a96720fd6a3

    The share token can be extracted from the URL and encoded for the API.
    """
    # Extract share token from URL
    # Return encoded token for Shares API
```

**Encoding for Shares API:**
Per Microsoft docs, sharing URLs must be encoded using base64url:
```python
import base64

def encode_sharing_url(sharing_url):
    """Encode sharing URL for Shares API."""
    # Base64 encode the URL
    encoded = base64.urlsafe_b64encode(sharing_url.encode()).decode()
    # Remove padding and return with 'u!' prefix
    return 'u!' + encoded.rstrip('=')
```

### Phase 5: OAuth Authentication (`auth.py`)
Handle OAuth 2.0 authentication:

**Implementation Options:**

**Option A: Device Code Flow (User-Friendly for CLI)**
```python
from msal import PublicClientApplication
import json

class OneDriveAuth:
    def __init__(self, config_path='config.json'):
        with open(config_path) as f:
            self.config = json.load(f)

        self.app = PublicClientApplication(
            self.config['client_id'],
            authority=self.config['authority']
        )
        self.token_cache_file = '.token_cache.json'

    def acquire_token_interactive(self):
        """Device code flow - user-friendly for CLI."""
        flow = self.app.initiate_device_flow(
            scopes=self.config['scopes']
        )

        if "user_code" not in flow:
            raise ValueError("Failed to create device flow")

        print(flow["message"])

        # Wait for user to authenticate
        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self._save_token_cache(result)
            return result["access_token"]
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")

    def get_access_token(self):
        """Get access token (from cache or new authentication)."""
        # Try to get token from cache
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(
                self.config['scopes'],
                account=accounts[0]
            )
            if result and "access_token" in result:
                return result["access_token"]

        # If no cached token, authenticate
        return self.acquire_token_interactive()
```

**Option B: Authorization Code Flow (Browser-Based)**
```python
def acquire_token_browser(self):
    """Authorization code flow with browser redirect."""
    # Start local server on redirect_uri
    # Generate auth URL
    # Open browser for user consent
    # Capture authorization code from redirect
    # Exchange code for token
```

### Phase 6: Graph API Client (`api.py`)
Interact with Microsoft Graph API:

```python
import requests

class OneDriveAPIClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })

    def get_shared_item(self, encoded_sharing_url):
        """
        Get shared item metadata from sharing URL.

        API: GET /shares/{encoded-sharing-url}/driveItem
        Docs: https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/shares_get
        """
        url = f"{self.base_url}/shares/{encoded_sharing_url}/driveItem"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def list_children(self, drive_id, item_id):
        """
        List children of a folder/album.

        API: GET /drives/{drive-id}/items/{item-id}/children
        """
        url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/children"
        all_items = []

        while url:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            all_items.extend(data.get('value', []))

            # Handle pagination
            url = data.get('@odata.nextLink')

        return all_items

    def get_image_urls(self, drive_id, item_id):
        """
        Get all image items from an album.
        Returns list of (filename, download_url) tuples.
        """
        children = self.list_children(drive_id, item_id)

        image_items = []
        for item in children:
            # Check if it's an image
            if 'image' in item.get('file', {}) or \
               item.get('file', {}).get('mimeType', '').startswith('image/'):

                # Get download URL
                download_url = item.get('@microsoft.graph.downloadUrl')
                if download_url:
                    filename = item['name']
                    image_items.append((filename, download_url))

                # If it's a folder, recursively get images
                if 'folder' in item:
                    subfolder_images = self.get_image_urls(
                        drive_id,
                        item['id']
                    )
                    image_items.extend(subfolder_images)

        return image_items
```

### Phase 7: Download Manager (`downloader.py`)
Same async download logic as original plan:

```python
import aiohttp
import aiofiles
import asyncio
from pathlib import Path

async def download_image(session, url, output_path, semaphore, retries=3):
    """Download a single image with retry logic."""
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()

                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)

                return True, output_path.name

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return False, str(e)

        return False, "Max retries exceeded"

async def download_all_images(image_items, output_dir, concurrent=5):
    """Download all images concurrently."""
    semaphore = asyncio.Semaphore(concurrent)
    output_dir = Path(output_dir)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for filename, url in image_items:
            output_path = output_dir / filename
            task = download_image(session, url, output_path, semaphore)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    return results
```

### Phase 8: CLI Interface (`cli.py`)
Command-line interface:

```python
import click
from tqdm import tqdm
import asyncio

@click.command()
@click.argument('album_url')
@click.option('--output', '-o', default='./downloads', help='Output directory')
@click.option('--concurrent', '-c', default=5, help='Concurrent downloads')
@click.option('--retries', '-r', default=3, help='Max retries per image')
@click.option('--config', default='config.json', help='OAuth config file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(album_url, output, concurrent, retries, config, verbose):
    """Download all images from a OneDrive public album using Microsoft Graph API."""

    from onedrive_downloader.auth import OneDriveAuth
    from onedrive_downloader.api import OneDriveAPIClient
    from onedrive_downloader.parser import encode_sharing_url
    from onedrive_downloader.downloader import download_all_images

    try:
        # Step 1: Authenticate
        click.echo("🔐 Authenticating with Microsoft...")
        auth = OneDriveAuth(config)
        access_token = auth.get_access_token()
        click.echo("✓ Authentication successful")

        # Step 2: Initialize API client
        client = OneDriveAPIClient(access_token)

        # Step 3: Parse and encode sharing URL
        click.echo(f"📂 Accessing album: {album_url}")
        encoded_url = encode_sharing_url(album_url)

        # Step 4: Get shared item metadata
        shared_item = client.get_shared_item(encoded_url)
        drive_id = shared_item['parentReference']['driveId']
        item_id = shared_item['id']
        album_name = shared_item.get('name', 'album')

        click.echo(f"✓ Found album: {album_name}")

        # Step 5: Get all image URLs
        click.echo("🔍 Finding images...")
        image_items = client.get_image_urls(drive_id, item_id)
        click.echo(f"✓ Found {len(image_items)} images")

        if not image_items:
            click.echo("No images found in album.")
            return

        # Step 6: Download images
        click.echo(f"⬇️  Downloading to {output}/{album_name}...")
        output_path = Path(output) / album_name

        # Run async downloads with progress bar
        with tqdm(total=len(image_items), unit='image') as pbar:
            async def download_with_progress():
                results = await download_all_images(
                    image_items,
                    output_path,
                    concurrent
                )
                for result in results:
                    pbar.update(1)
                return results

            results = asyncio.run(download_with_progress())

        # Step 7: Display summary
        successful = sum(1 for success, _ in results if success)
        failed = len(results) - successful

        click.echo(f"\n✓ Download complete!")
        click.echo(f"  Successfully downloaded: {successful}/{len(image_items)} images")
        if failed > 0:
            click.echo(f"  Failed: {failed} images")
        click.echo(f"  Location: {output_path}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

if __name__ == '__main__':
    main()
```

### Phase 9: Entry Point (`__main__.py`)
```python
from onedrive_downloader.cli import main

if __name__ == '__main__':
    main()
```

### Phase 10: Documentation

#### README.md
```markdown
# OneDrive Album Downloader

Download all images from OneDrive albums using the official Microsoft Graph API.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Azure AD Application
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration":
   - **Name**: OneDrive Album Downloader
   - **Supported account types**: Personal Microsoft accounts
   - **Redirect URI**: `http://localhost:8080`
4. Save the **Application (client) ID**
5. Under "Certificates & secrets", create a **Client Secret**
6. Under "API permissions", add:
   - `Files.Read.All` (delegated)
   - `offline_access` (delegated)
7. Click "Grant admin consent"

### 3. Configure Application
Copy `config.json.example` to `config.json` and fill in your credentials:
```json
{
  "client_id": "YOUR_CLIENT_ID_HERE",
  "client_secret": "YOUR_CLIENT_SECRET_HERE",
  "authority": "https://login.microsoftonline.com/common",
  "redirect_uri": "http://localhost:8080",
  "scopes": ["Files.Read.All", "offline_access"]
}
```

## Usage

```bash
# Basic usage
python -m onedrive_downloader "https://onedrive.live.com/..."

# Custom output directory
python -m onedrive_downloader "https://onedrive.live.com/..." -o ./my_photos

# Increase concurrent downloads
python -m onedrive_downloader "https://onedrive.live.com/..." -c 10

# Verbose output
python -m onedrive_downloader "https://onedrive.live.com/..." -v
```

### First Run
On first run, you'll be prompted to authenticate:
1. A browser window will open (or you'll get a device code)
2. Sign in with your Microsoft account
3. Grant permissions to the application
4. Return to the terminal

Your credentials will be cached for future runs.

## How It Works
1. Authenticates with Microsoft using OAuth 2.0
2. Encodes the sharing URL for the Microsoft Graph API
3. Uses the Shares API to access the shared album
4. Enumerates all images in the album
5. Downloads images concurrently with retry logic
6. Saves to organized output directory

## Troubleshooting

### "Authentication failed"
- Verify your `config.json` has correct client_id and client_secret
- Check that your Azure AD app has correct permissions
- Try deleting `.token_cache.json` to force re-authentication

### "Forbidden" or "Unauthorized"
- Make sure you granted admin consent for the API permissions
- Verify the Microsoft account has access to the shared album

### "Cannot access shared content"
- The OneDrive API requires authentication even for public albums
- Make sure you're signed in with an account that has access
```

#### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp

# Downloaded images
downloads/
output/
images/

# Credentials and tokens
config.json
.env
.token_cache.json
*.pem
*.key

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

#### config.json.example
```json
{
  "client_id": "YOUR_CLIENT_ID_HERE",
  "client_secret": "YOUR_CLIENT_SECRET_HERE",
  "authority": "https://login.microsoftonline.com/common",
  "redirect_uri": "http://localhost:8080",
  "scopes": ["Files.Read.All", "offline_access"]
}
```

## Implementation Order

1. **Project structure** - Create directories and empty files
2. **requirements.txt** - Define dependencies
3. **config.py** - Configuration constants
4. **utils.py** - Helper functions (URL encoding, filename sanitization)
5. **parser.py** - URL parsing and encoding for Shares API
6. **auth.py** - OAuth authentication with MSAL (CRITICAL)
7. **api.py** - Microsoft Graph API client (CRITICAL)
8. **downloader.py** - Async download manager
9. **cli.py** - CLI interface orchestrating everything (CRITICAL)
10. **__main__.py** - Entry point
11. **README.md** - Setup and usage documentation (CRITICAL)
12. **.gitignore** - Exclude credentials and downloads
13. **config.json.example** - Template for OAuth config

## Key Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| OAuth authentication complexity | Use MSAL library; device code flow for CLI-friendly auth |
| Sharing URL format | Encode URL using base64url with 'u!' prefix per API docs |
| Token management | Cache tokens locally; handle refresh automatically |
| API pagination | Follow @odata.nextLink to get all items |
| Rate limiting | Use semaphore for concurrent downloads; respect API limits |
| Nested folders | Recursively enumerate folders to find all images |
| Authentication errors | Clear error messages; guide user through Azure AD setup |
| Public album access | Requires auth even for public content; document in README |

## Testing Strategy

1. Test OAuth flow (device code and auth code)
2. Test URL encoding for Shares API
3. Test accessing a shared album
4. Test image enumeration (including nested folders)
5. Test downloading small batch
6. Test error handling (invalid URL, expired token, network failure)
7. Test token refresh
8. Test with large album (100+ images)

## API References

- [Microsoft Graph API Overview](https://learn.microsoft.com/en-us/graph/overview)
- [OneDrive API Documentation](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/)
- [Access Shared Items API](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/shares_get)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
