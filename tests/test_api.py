#!/usr/bin/env python3
"""Test API access to shared item."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import requests
from onedrive_downloader.auth import get_authenticated_token
from onedrive_downloader.parser import parse_and_encode_url

# Note: This test uses an old album view URL format (for testing failure cases)
# For actual working tests, use test_share_link.py

# Get token
print("Getting access token...")
token = get_authenticated_token()
print(f"✓ Token received (length: {len(token)})\n")

# Parse URL (example invalid format)
album_url = "https://onedrive.live.com/?view=8&photosData=%2Falbum%2FEXAMPLE_ID"
print(f"Album URL: {album_url}")

encoded_url = parse_and_encode_url(album_url)
print(f"Encoded URL: {encoded_url}\n")

# Try API call
api_url = f"https://graph.microsoft.com/v1.0/shares/{encoded_url}/driveItem"
print(f"API URL: {api_url}\n")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

print("Making API request...")
response = requests.get(api_url, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}\n")

if response.status_code == 200:
    print("✓ SUCCESS!")
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print("✗ ERROR!")
    print(f"Response Text: {response.text}")
    try:
        error_data = response.json()
        print(f"\nError JSON: {json.dumps(error_data, indent=2)}")
    except:
        pass
