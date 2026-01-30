#!/usr/bin/env python3
"""Test listing children through Shares API."""

import sys
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

album_url = TEST_ALBUM_URL
encoded_url = parse_and_encode_url(album_url)

print(f"Encoded URL: {encoded_url}\n")

# Try API call through Shares API
api_url = f"https://graph.microsoft.com/v1.0/shares/{encoded_url}/driveItem/children"
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
    items = data.get('value', [])
    print(f"Found {len(items)} items on this page\n")

    # Count images
    image_count = sum(1 for item in items if 'image' in item or item.get('file', {}).get('mimeType', '').startswith('image/'))
    print(f"Images on this page: {image_count}\n")

    # Show first few items
    for i, item in enumerate(items[:10]):
        name = item.get('name')
        size = item.get('size', 0)
        is_image = 'image' in item or item.get('file', {}).get('mimeType', '').startswith('image/')
        item_type = "IMAGE" if is_image else "OTHER"
        print(f"{i+1}. [{item_type}] {name} - {size} bytes")

    # Check for pagination
    next_link = data.get('@odata.nextLink')
    if next_link:
        print(f"\n✓ More pages available: {next_link[:80]}...")
else:
    print("✗ ERROR!")
    print(f"Response Text: {response.text}")
    try:
        error_data = response.json()
        print(f"\nError JSON: {json.dumps(error_data, indent=2)}")
    except:
        pass
