#!/usr/bin/env python3
"""
provision_realm.py
Builds a whole company setup in Keycloak from scratch: a realm, one group and one role per
department, and the role-to-group links (RBAC). Safe to run again.
"""
import getpass
import sys

import requests

KEYCLOAK_URL = "http://localhost:8080"
ADMIN_USER = "acmeadmin"
REALM = "acme-corp-test"            # a separate test company, so your real lab stays untouched
DISPLAY_NAME = "Acme Corp (test)"
DEPARTMENTS = ["hr", "engineering", "finance"]

admin_password = getpass.getpass(f"Keycloak admin password for '{ADMIN_USER}': ")

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
headers = {"Authorization": f"Bearer {response.json()['access_token']}"}


def call(method, path, **kwargs):
    return requests.request(
        method, f"{KEYCLOAK_URL}/admin{path}", headers=headers, timeout=30, **kwargs
    )


def report(what, response):
    if response.status_code in (201, 204):
        print(f"CREATED  {what}")
    elif response.status_code == 409:
        print(f"EXISTS   {what}")
    else:
        print(f"FAILED   {what}: {response.status_code} {response.text}")
        sys.exit(1)


# 1. The company (realm)
report(f"realm {REALM}", call("POST", "/realms", json={
    "realm": REALM, "displayName": DISPLAY_NAME, "enabled": True,
}))

# 2. One role (badge) and one group (department) for each department
for department in DEPARTMENTS:
    report(f"role {department}-access", call("POST", f"/realms/{REALM}/roles", json={
        "name": f"{department}-access",
        "description": f"Can open the {department} portal",
    }))
    report(f"group {department}", call("POST", f"/realms/{REALM}/groups", json={"name": department}))

# 3. Give each department its badge
groups = {g["name"]: g["id"] for g in call("GET", f"/realms/{REALM}/groups", params={"max": 1000}).json()}
for department in DEPARTMENTS:
    role = call("GET", f"/realms/{REALM}/roles/{department}-access").json()
    result = call("POST", f"/realms/{REALM}/groups/{groups[department]}/role-mappings/realm", json=[role])
    report(f"link {department} -> {department}-access", result)

print(f"\nDone. Open the Keycloak console and look at the realm '{REALM}'.")
