#!/usr/bin/env python3
"""
require_mfa.py
Makes every member of the 'finance' group set up an authenticator app (TOTP) at their next login.
Safe to run again: it never adds the same requirement twice.
"""
import getpass
import sys

import requests

KEYCLOAK_URL = "http://localhost:8080"
REALM = "acme-corp"
ADMIN_USER = "acmeadmin"
GROUP_NAME = "finance"

admin_password = getpass.getpass(f"Keycloak admin password for '{ADMIN_USER}': ")


def get_token():
    response = requests.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": admin_password,
            "grant_type": "password",
        },
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Could not log in as admin (status {response.status_code}): {response.text}")
        sys.exit(1)
    return response.json()["access_token"]


token = get_token()


def api(method, path, **kwargs):
    global token
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}{path}"
    response = None
    for attempt in (1, 2):
        response = requests.request(
            method, url, headers={"Authorization": f"Bearer {token}"}, timeout=30, **kwargs
        )
        if response.status_code == 401 and attempt == 1:
            token = get_token()
            continue
        break
    return response


groups = api("GET", "/groups", params={"max": 1000}).json()
group = next((g for g in groups if g["name"] == GROUP_NAME), None)
if group is None:
    print(f"Group '{GROUP_NAME}' not found. Check Part 6.")
    sys.exit(1)

members = api("GET", f"/groups/{group['id']}/members", params={"max": 1000}).json()
print(f"Found {len(members)} member(s) in '{GROUP_NAME}'.")

for member in members:
    # Read the full user record, add the requirement, and save it back.
    user = api("GET", f"/users/{member['id']}").json()
    actions = user.get("requiredActions", [])
    if "CONFIGURE_TOTP" in actions:
        print(f"ALREADY {user['username']}")
        continue
    user["requiredActions"] = actions + ["CONFIGURE_TOTP"]
    response = api("PUT", f"/users/{member['id']}", json=user)
    if response.status_code == 204:
        print(f"MFA REQUIRED {user['username']}")
    else:
        print(f"FAILED {user['username']}: {response.status_code} {response.text}")
