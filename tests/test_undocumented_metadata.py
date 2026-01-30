#!/usr/bin/env python3
"""Test script to discover undocumented metadata fields in Microsoft Graph API."""

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
    print("Copy test_config.py.example to test_config.py and configure your test URL.")
    sys.exit(1)


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def make_request(url, token, description):
    """Make API request and print results."""
    print(f"Testing: {description}")
    print(f"URL: {url}\n")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✓ SUCCESS! Response data:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"\n✗ Failed: {response.status_code}")
            try:
                error = response.json()
                print(json.dumps(error, indent=2))
            except:
                print(response.text)
            return None

    except Exception as e:
        print(f"\n✗ Exception: {e}")
        return None


def main():
    print_section("DISCOVERING UNDOCUMENTED ONEDRIVE METADATA")

    # Get authentication token
    print("Getting access token...")
    token = get_authenticated_token()
    print("✓ Authenticated\n")

    # Parse and encode the album URL
    album_url = TEST_ALBUM_URL
    print(f"Album URL: {album_url}")
    encoded_url = parse_and_encode_url(album_url)
    print(f"Encoded: {encoded_url}\n")

    # Test 1: Beta API with all fields
    print_section("TEST 1: Beta API with $select=*")
    beta_url = f"https://graph.microsoft.com/beta/shares/{encoded_url}/driveItem?$select=*"
    beta_data = make_request(beta_url, token, "Beta endpoint with all fields")

    # Test 2: Beta API with expand
    print_section("TEST 2: Beta API with $expand")
    expand_url = f"https://graph.microsoft.com/beta/shares/{encoded_url}/driveItem?$expand=children,thumbnails"
    make_request(expand_url, token, "Beta endpoint with expand")

    # Test 3: Request specific vision-related fields
    print_section("TEST 3: Request Vision/AI Fields")
    vision_fields = [
        "image",
        "photo",
        "video",
        "tags",
        "description",
        "caption",
        "labels",
        "faces",
        "objects",
        "text",
        "insights",
        "analytics",
        "aiMetadata",
        "computerVision",
        "contentType",
        "searchableText"
    ]
    select_fields = ",".join(vision_fields)
    vision_url = f"https://graph.microsoft.com/beta/shares/{encoded_url}/driveItem?$select={select_fields}"
    make_request(vision_url, token, "Specific vision/AI fields")

    # Test 4: Get children with all metadata
    print_section("TEST 4: Children with All Metadata")
    children_url = f"https://graph.microsoft.com/beta/shares/{encoded_url}/driveItem/children?$select=*&$top=1"
    children_data = make_request(children_url, token, "First child item with all fields")

    # Test 5: Thumbnails endpoint (might contain analysis data)
    print_section("TEST 5: Thumbnails Endpoint")
    if children_data and 'value' in children_data and len(children_data['value']) > 0:
        first_child = children_data['value'][0]
        child_id = first_child.get('id')

        # Get parent drive ID from the child's parentReference
        parent_ref = first_child.get('parentReference', {})
        drive_id = parent_ref.get('driveId')

        if drive_id and child_id:
            thumb_url = f"https://graph.microsoft.com/beta/drives/{drive_id}/items/{child_id}/thumbnails"
            make_request(thumb_url, token, "Thumbnails for first image")

    # Test 6: Analytics endpoint
    print_section("TEST 6: Analytics Endpoint")
    if children_data and 'value' in children_data and len(children_data['value']) > 0:
        first_child = children_data['value'][0]
        child_id = first_child.get('id')
        parent_ref = first_child.get('parentReference', {})
        drive_id = parent_ref.get('driveId')

        if drive_id and child_id:
            analytics_url = f"https://graph.microsoft.com/beta/drives/{drive_id}/items/{child_id}/analytics"
            make_request(analytics_url, token, "Analytics for first image")

    # Test 7: Search API (might expose AI tags)
    print_section("TEST 7: Search API")
    if beta_data:
        drive_id = beta_data.get('parentReference', {}).get('driveId')
        if drive_id:
            # Search for all images in this drive
            search_url = f"https://graph.microsoft.com/beta/drives/{drive_id}/root/search(q='.jpg')?$top=1"
            search_data = make_request(search_url, token, "Search API results")

    # Test 8: Get item with all possible expansions
    print_section("TEST 8: Everything Expanded")
    everything_url = f"https://graph.microsoft.com/beta/shares/{encoded_url}/driveItem?$expand=children($select=*;$expand=thumbnails),thumbnails,permissions,analytics"
    make_request(everything_url, token, "All expansions at once")

    print_section("DISCOVERY COMPLETE")
    print("Review the output above to see what fields are available.")
    print("Look for any fields related to: tags, captions, labels, faces, objects, text, insights")


if __name__ == '__main__':
    main()
