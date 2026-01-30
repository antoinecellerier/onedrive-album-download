#!/usr/bin/env python3
"""Test listing children of the album."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import requests
from onedrive_downloader.auth import get_authenticated_token

try:
    from test_config import TEST_DRIVE_ID, TEST_ITEM_ID
except ImportError:
    print("ERROR: test_config.py not found!")
    print("Copy test_config.py.example to test_config.py and configure your test IDs.")
    sys.exit(1)

# Get token
print("Getting access token...")
token = get_authenticated_token()
print(f"✓ Token received\n")

drive_id = TEST_DRIVE_ID
item_id = TEST_ITEM_ID

print(f"Drive ID: {drive_id}")
print(f"Item ID: {item_id}\n")

# Try API call
api_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children"
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
    print(f"Found {len(items)} items\n")

    # Show first few items
    for i, item in enumerate(items[:5]):
        print(f"{i+1}. {item.get('name')} - {item.get('size', 0)} bytes")
        if 'image' in item:
            print(f"   Image: {item['image']}")
else:
    print("✗ ERROR!")
    print(f"Response Text: {response.text}")
    try:
        error_data = response.json()
        print(f"\nError JSON: {json.dumps(error_data, indent=2)}")
    except:
        pass
