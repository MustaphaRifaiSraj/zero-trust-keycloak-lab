#!/usr/bin/env python3
"""
import_users.py
Reads employees.csv and creates each employee in Keycloak using the Admin REST API.
Safe to run more than once: employees that already exist are skipped.
"""
import csv
import getpass
import sys

import requests

# ---- Settings you may change -------------------------------------------------
KEYCLOAK_URL = "http://localhost:8080"   # this script runs ON the VM, so localhost is correct
REALM = "acme-corp"
ADMIN_USER = "acmeadmin"
CSV_FILE = "employees.csv"
START_PASSWORD = "Welcome-Acme-2026"     # first password given to every new employee
PASSWORD_MUST_CHANGE = False             # True = employee must choose a new password at first login
# ------------------------------------------------------------------------------

# Ask for the admin password while you run the script, so it is never saved in the file.
admin_password = getpass.getpass(f"Keycloak admin password for '{ADMIN_USER}': ")


def get_token():
    """Log in to Keycloak as the admin and return a short-lived access token."""
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
    """Call the Admin REST API. If the token has expired (401), log in again and retry once."""
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


# Look up the departments (groups) that exist in Keycloak, so we can place people in them.
groups_response = api("GET", "/groups", params={"max": 1000})
if groups_response.status_code != 200:
    print(f"Could not read groups (status {groups_response.status_code}). Is the realm '{REALM}' created?")
    sys.exit(1)
group_ids = {group["name"]: group["id"] for group in groups_response.json()}
print("Departments found in Keycloak:", ", ".join(sorted(group_ids)) or "none")

created = skipped = failed = 0

with open(CSV_FILE, newline="", encoding="utf-8-sig") as file:
    for row in csv.DictReader(file):
        email = row["email"].strip().lower()
        departments = [d.strip().lower() for d in row["department"].split("|") if d.strip()]

        missing = [d for d in departments if d not in group_ids]
        if missing:
            print(f"FAILED  {email}: department(s) not found in Keycloak: {missing}")
            failed += 1
            continue

        user = {
            "username": email,
            "email": email,
            "emailVerified": True,
            "firstName": row["first_name"].strip(),
            "lastName": row["last_name"].strip(),
            "enabled": True,
            "credentials": [
                {"type": "password", "value": START_PASSWORD, "temporary": PASSWORD_MUST_CHANGE}
            ],
        }

        response = api("POST", "/users", json=user)

        if response.status_code == 201:
            # Keycloak tells us the new user's id in the "Location" header.
            user_id = response.headers["Location"].rstrip("/").split("/")[-1]
            for department in departments:
                api("PUT", f"/users/{user_id}/groups/{group_ids[department]}")
            print(f"CREATED {email} -> {', '.join(departments)}")
            created += 1
        elif response.status_code == 409:
            print(f"EXISTS  {email} (skipped)")
            skipped += 1
        else:
            print(f"FAILED  {email}: status {response.status_code} {response.text}")
            failed += 1

print(f"\nDone. Created: {created}   Already existed: {skipped}   Failed: {failed}")
