#!/usr/bin/env python3
"""Test authentication setup."""

import sys
import json
from msal import PublicClientApplication

# Load config
with open('config.json') as f:
    config = json.load(f)

print(f"Client ID: {config['client_id']}")
print(f"Authority: {config['authority']}")
print(f"Scopes: {config['scopes']}")
print()

# Filter reserved scopes
reserved_scopes = {'offline_access', 'openid', 'profile'}
filtered_scopes = [s for s in config['scopes'] if s not in reserved_scopes]
print(f"Filtered scopes: {filtered_scopes}")
print()

# Create MSAL app
app = PublicClientApplication(
    client_id=config['client_id'],
    authority=config['authority']
)

print("Initiating device flow...")
try:
    flow = app.initiate_device_flow(scopes=filtered_scopes)

    if "user_code" in flow:
        print("\n" + "="*60)
        print("SUCCESS! Device flow initiated")
        print("="*60)
        print(flow["message"])
        print("="*60)
    else:
        print("\nERROR: No user_code in flow response")
        print(f"Response: {json.dumps(flow, indent=2)}")

except Exception as e:
    print(f"\nEXCEPTION: {e}")
    import traceback
    traceback.print_exc()
