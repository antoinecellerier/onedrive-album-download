#!/usr/bin/env python3
"""Test API access with proper sharing link."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import requests
from onedrive_downloader.auth import get_authenticated_token
from onedrive_downloader.parser import parse_and_encode_url

try:
    from test_config import TEST_ALBUM_URL
except ImportError:
    print("ERROR: test_config.py not found!")
    print("Copy test_config.py.example to test_config.py and configure your test URLs.")
    sys.exit(1)

# Get token
print("Getting access token...")
token = get_authenticated_token()
print(f"✓ Token received\n")

# Parse URL
album_url = TEST_ALBUM_URL
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

print(f"Status Code: {response.status_code}\n")

if response.status_code == 200:
    print("✓ SUCCESS!")
    data = response.json()
    print(f"Album Name: {data.get('name', 'Unknown')}")
    print(f"Item ID: {data.get('id')}")
    print(f"Drive ID: {data.get('parentReference', {}).get('driveId')}")

    if 'folder' in data:
        child_count = data['folder'].get('childCount', 0)
        print(f"Child Count: {child_count}")

    print(f"\nFull response:")
    print(json.dumps(data, indent=2))
else:
    print("✗ ERROR!")
    print(f"Response Text: {response.text}")
    try:
        error_data = response.json()
        print(f"\nError JSON: {json.dumps(error_data, indent=2)}")
    except:
        pass
