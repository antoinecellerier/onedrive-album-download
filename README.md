# OneDrive Album Downloader

Download all images from OneDrive public albums using the official Microsoft Graph API.

## Features

- ✅ Uses official Microsoft Graph API (no web scraping)
- ✅ OAuth 2.0 authentication with token caching
- ✅ Concurrent downloads for fast performance
- ✅ Automatic retry logic with exponential backoff
- ✅ Progress bars and detailed statistics
- ✅ Recursive folder support
- ✅ Resumes interrupted downloads (skips existing files)
- ✅ Cross-platform (Windows, macOS, Linux)

## Prerequisites

- Python 3.8 or higher
- A Microsoft account
- Azure AD application (free to create)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### Step 1: Create Azure AD Application

You need to create an Azure AD application to use the Microsoft Graph API:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure the application:
   - **Name**: `OneDrive Album Downloader` (or any name you prefer)
   - **Supported account types**: Select "Personal Microsoft accounts only"
   - **Redirect URI**: Leave blank (not needed for device code flow)
5. Click **Register**

### Step 2: Note Your Application (Client) ID

After registration, you'll see the application overview. Copy the **Application (client) ID** - you'll need this.

### Step 3: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Add these permissions:
   - `Files.Read.All` - Read all files user can access
   - `offline_access` - Maintain access to data (for refresh tokens)
6. Click **Add permissions**
7. (Optional) Click **Grant admin consent** if you have admin rights

Note: You don't need a client secret for device code flow, but you can add one if you want to use authorization code flow in the future.

### Step 4: Create Configuration File

1. Copy the example config file:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` and add your Application (client) ID:
   ```json
   {
     "client_id": "YOUR_APPLICATION_CLIENT_ID_HERE",
     "authority": "https://login.microsoftonline.com/common",
     "scopes": ["Files.Read.All", "offline_access"]
   }
   ```

Note: The `client_secret` field is not needed for device code flow.

## Usage

### Getting the Share Link

**IMPORTANT:** You must use a proper OneDrive sharing link, not an album view URL.

To get the correct sharing link:

1. Open your OneDrive album in a web browser
2. Click the **Share** button (or right-click → Share)
3. Copy the sharing link that OneDrive generates
4. The link should look like: `https://1drv.ms/...` or `https://onedrive.live.com/redir?...`

**✅ Correct URL formats:**
- `https://1drv.ms/a/c/...` (short link)
- `https://onedrive.live.com/redir?resid=...`

**❌ Incorrect URL formats:**
- `https://onedrive.live.com/?view=8&photosData=...` (album view URL - won't work)
- Browser URLs from navigating OneDrive web interface

### Basic Usage

```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID"
```

### Options

```
Options:
  -o, --output DIR          Output directory (default: ./downloads)
  -c, --concurrent INT      Concurrent downloads (default: 5)
  -r, --retries INT         Max retries per image (default: 3)
  --config PATH             OAuth config file (default: config.json)
  --no-recursive            Don't recursively download from subfolders
  -v, --verbose             Verbose output
  --help                    Show this message and exit
```

### Examples

Download album to default directory:
```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID"
```

Download to custom directory:
```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" -o ./my_photos
```

Increase concurrent downloads for faster performance:
```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" -c 10
```

Verbose output with detailed progress:
```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" -v
```

Don't download from subfolders:
```bash
python -m onedrive_downloader "https://1drv.ms/a/c/YOUR_ALBUM_ID" --no-recursive
```

## First Run - Authentication

On the first run, you'll be prompted to authenticate:

```
====================================================================
AUTHENTICATION REQUIRED
====================================================================
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code XXXXXXXXX to authenticate.
====================================================================
```

1. Open the URL in your web browser
2. Enter the code shown
3. Sign in with your Microsoft account
4. Grant permissions to the application
5. Return to the terminal - download will start automatically

Your authentication is cached in `.token_cache.json` and will be reused for future runs.

## How It Works

1. **Authentication**: Uses OAuth 2.0 device code flow to get user consent
2. **URL Encoding**: Encodes the OneDrive sharing URL for the Microsoft Graph API
3. **Access Album**: Uses the Shares API to access the shared album
4. **Enumerate Images**: Recursively finds all images in the album and subfolders
5. **Concurrent Downloads**: Downloads multiple images in parallel with retry logic
6. **Progress Tracking**: Shows real-time progress with statistics

## File Structure

```
onedrive-album-download/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── config.json.example           # Example OAuth configuration
├── config.json                   # Your OAuth config (create this)
├── .token_cache.json             # Cached authentication tokens (auto-created)
├── onedrive_downloader/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── cli.py                   # Command-line interface
│   ├── auth.py                  # OAuth authentication
│   ├── api.py                   # Microsoft Graph API client
│   ├── parser.py                # URL parsing and encoding
│   ├── downloader.py            # Async image downloader
│   ├── utils.py                 # Helper functions
│   └── config.py                # Configuration constants
└── downloads/                    # Downloaded images (default location)
```

## Troubleshooting

### "Config file not found: config.json"

Create a `config.json` file by copying `config.json.example` and filling in your Azure AD application's client ID.

### "Authentication failed"

- Verify your `config.json` has the correct `client_id`
- Check that your Azure AD app has the correct permissions (`Files.Read.All`, `offline_access`)
- Try deleting `.token_cache.json` to force re-authentication

### "Cannot access shared content" or "Forbidden"

- The OneDrive API requires authentication even for public albums
- Make sure you're signed in with an account that has access to the shared content
- If the album is truly public, any Microsoft account should work

### "Invalid OneDrive URL" or "Invalid shares key"

This usually means you're using an album view URL instead of a sharing link.

**Solution:**
1. Go to your OneDrive album in a web browser
2. Click the **Share** button
3. Copy the generated sharing link (starts with `https://1drv.ms/` or similar)
4. Use that link instead

**Valid domains:**
- `1drv.ms` (preferred short links)
- `onedrive.live.com/redir` (redirect links)
- Direct OneDrive sharing URLs

**Invalid URLs:**
- URLs containing `?view=8&photosData=` (these are album view URLs, not sharing links)

### "No images found in album"

- The album might be empty
- The album might contain only non-image files (videos, documents)
- Try using `-v` (verbose) flag to see more details

### Clear Authentication Cache

If you want to sign in with a different account:

```bash
rm .token_cache.json
```

## API Rate Limits

Microsoft Graph API has rate limits. If you encounter throttling:
- Reduce concurrent downloads with `-c 3` or `-c 1`
- The tool automatically retries with exponential backoff

## Privacy & Security

- Your authentication tokens are stored locally in `.token_cache.json`
- Never share your `config.json` or `.token_cache.json` files
- The `.gitignore` is configured to exclude these files from version control
- The tool only requests read-only access to files (`Files.Read.All`)

## API References

- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview)
- [OneDrive API Documentation](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/)
- [Access Shared Items](https://learn.microsoft.com/en-us/onedrive/developer/rest-api/api/shares_get)
- [MSAL Python](https://msal-python.readthedocs.io/)

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Built with [Microsoft Graph API](https://graph.microsoft.com)
- Authentication via [MSAL (Microsoft Authentication Library)](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- Async downloads with [aiohttp](https://github.com/aio-libs/aiohttp)
- CLI with [Click](https://click.palletsprojects.com/)
- Progress bars with [tqdm](https://github.com/tqdm/tqdm)
