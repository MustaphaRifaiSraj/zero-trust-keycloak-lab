#!/usr/bin/env python3
"""
csv_to_ldif.py
Turns ldap_employees.csv (first_name,last_name,email,department) into an LDIF file that fills the
OpenLDAP "phone book", plus ldap/people.csv, a small list that a later step uses to place each
person in their department group in Keycloak.
"""
import base64
import csv
import re
import sys

CSV_FILE = "ldap_employees.csv"
LDIF_FILE = "ldap/users.ldif"
PEOPLE_FILE = "ldap/people.csv"
BASE_DN = "dc=acme,dc=local"
PASSWORD = "Ldap-Pass-2026"      # the same fake password for everyone in this lab
MAIL_DOMAIN = "ldap.acme.test"   # different from your Keycloak-only people, so emails never clash
DEPARTMENTS = ("hr", "engineering", "finance")

# Three named people so you always have known accounts to test with: (uid, first, last, department)
TEST_PEOPLE = [
    ("ben.carter", "Ben", "Carter", "finance"),
    ("lara.whitfield", "Lara", "Whitfield", "hr"),
    ("nora.ibrahim", "Nora", "Ibrahim", "engineering"),
]


def ldif_line(attribute, value):
    """Write 'attribute: value'. LDIF needs base64 encoding for accents and other unusual text."""
    plain = (
        value.isascii()
        and value.isprintable()
        and not value.startswith((" ", ":", "<"))
        and not value.endswith(" ")
    )
    if plain:
        return f"{attribute}: {value}"
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"{attribute}:: {encoded}"


def person_entry(uid, first, last, departments):
    """Build one phone-book entry for one person."""
    lines = [
        f"dn: uid={uid},ou=people,{BASE_DN}",
        "objectClass: inetOrgPerson",
        f"uid: {uid}",
        ldif_line("cn", f"{first} {last}"),
        ldif_line("givenName", first),
        ldif_line("sn", last),
        f"mail: {uid}@{MAIL_DOMAIN}",
    ]
    for department in departments:
        lines.append(f"departmentNumber: {department}")
    lines.append(f"userPassword: {PASSWORD}")
    return "\n".join(lines)


def make_uid(email, used):
    """Make a short login name from the start of the email address, and keep it unique."""
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower()) or "user"
    uid, number = base, 1
    while uid in used:
        number += 1
        uid = f"{base}{number}"
    used.add(uid)
    return uid


used_uids = {uid for uid, _, _, _ in TEST_PEOPLE}
entries = [
    f"dn: ou=people,{BASE_DN}\nobjectClass: organizationalUnit\nou: people",
    f"dn: ou=groups,{BASE_DN}\nobjectClass: organizationalUnit\nou: groups",
]
people = []  # (uid, departments) pairs for the next step

for uid, first, last, department in TEST_PEOPLE:
    entries.append(person_entry(uid, first, last, [department]))
    people.append((uid, [department]))

skipped = 0
try:
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            first = row["first_name"].strip()
            last = row["last_name"].strip()
            email = row["email"].strip()
            departments = [d.strip().lower() for d in row["department"].split("|") if d.strip()]
            if not first or not last or not email or not departments or any(d not in DEPARTMENTS for d in departments):
                print(f"SKIPPED  {first} {last} ({email}): a field is empty or the department is not one of {DEPARTMENTS}")
                skipped += 1
                continue
            uid = make_uid(email, used_uids)
            entries.append(person_entry(uid, first, last, departments))
            people.append((uid, departments))
except FileNotFoundError:
    print(f"Could not find {CSV_FILE}. Check you are in ~/acme-iam and that the file copy worked.")
    sys.exit(1)

with open(LDIF_FILE, "w", encoding="ascii", newline="\n") as file:
    file.write("\n\n".join(entries) + "\n")

with open(PEOPLE_FILE, "w", encoding="utf-8", newline="\n") as file:
    file.write("uid,departments\n")
    for uid, departments in people:
        file.write(f"{uid},{'|'.join(departments)}\n")

print(f"Wrote {len(people)} people to {LDIF_FILE} ({len(TEST_PEOPLE)} test people + {len(people) - len(TEST_PEOPLE)} from {CSV_FILE}).")
if skipped:
    print(f"Skipped {skipped} row(s). See the SKIPPED lines above.")
print(f"Also wrote {PEOPLE_FILE}.")
