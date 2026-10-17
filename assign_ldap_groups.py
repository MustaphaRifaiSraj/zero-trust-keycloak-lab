#!/usr/bin/env python3
"""
assign_ldap_groups.py
After Keycloak has imported the people from the LDAP phone book, this places each person in the
right department group (hr, engineering, finance) using ldap/people.csv. Safe to run again.
"""
import csv
import getpass
import sys

import requests

KEYCLOAK_URL = "http://localhost:8080"
REALM = "acme-corp"
ADMIN_USER = "acmeadmin"
PEOPLE_FILE = "ldap/people.csv"

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


groups_response = api("GET", "/groups", params={"max": 1000})
if groups_response.status_code != 200:
    print(f"Could not read groups (status {groups_response.status_code}). Is the realm '{REALM}' created?")
    sys.exit(1)
group_ids = {group["name"]: group["id"] for group in groups_response.json()}

placed = missing = failed = 0

try:
    with open(PEOPLE_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
except FileNotFoundError:
    print(f"Could not find {PEOPLE_FILE}. Run csv_to_ldif.py first (Step 10.2).")
    sys.exit(1)

for row in rows:
    uid = row["uid"].strip()
    departments = [d for d in row["departments"].split("|") if d]

    found = api("GET", "/users", params={"username": uid, "exact": "true"}).json()
    if not found:
        print(f"MISSING  {uid} (not imported from LDAP yet; run Sync all users first)")
        missing += 1
        continue

    user_id = found[0]["id"]
    ok = True
    for department in departments:
        if department not in group_ids:
            print(f"FAILED   {uid}: group '{department}' does not exist in Keycloak")
            ok = False
            continue
        response = api("PUT", f"/users/{user_id}/groups/{group_ids[department]}")
        if response.status_code != 204:
            print(f"FAILED   {uid}: status {response.status_code} {response.text}")
            ok = False
    if ok:
        print(f"PLACED   {uid} -> {', '.join(departments)}")
        placed += 1
    else:
        failed += 1

print(f"\nDone. Placed: {placed}   Not imported yet: {missing}   Failed: {failed}")
