#!/usr/bin/env python3
"""Test full authentication flow."""

import sys
from pathlib import Path
import json
from msal import PublicClientApplication, SerializableTokenCache

# Load config from parent directory
config_path = Path(__file__).parent.parent / 'config.json'
with open(config_path) as f:
    config = json.load(f)

# Filter reserved scopes
reserved_scopes = {'offline_access', 'openid', 'profile'}
filtered_scopes = [s for s in config['scopes'] if s not in reserved_scopes]

# Create MSAL app
cache = SerializableTokenCache()
app = PublicClientApplication(
    client_id=config['client_id'],
    authority=config['authority'],
    token_cache=cache
)

print("Initiating device flow...")
sys.stdout.flush()

flow = app.initiate_device_flow(scopes=filtered_scopes)

if "user_code" not in flow:
    print(f"ERROR: {flow}")
    sys.exit(1)

print("\n" + "="*60)
print("AUTHENTICATION REQUIRED")
print("="*60)
print(flow["message"])
print("="*60 + "\n")
sys.stdout.flush()

print("Waiting for authentication...")
sys.stdout.flush()

result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    print("\n✓ Authentication successful!")
    print(f"Access token received (length: {len(result['access_token'])})")

    # Save token cache
    with open('.token_cache.json', 'w') as f:
        f.write(cache.serialize())
    print("Token cached to .token_cache.json")
else:
    error = result.get("error", "Unknown error")
    error_desc = result.get("error_description", "No description")
    print(f"\n✗ Authentication failed: {error} - {error_desc}")
    sys.exit(1)
