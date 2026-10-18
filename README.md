# Zero Trust Mini-Company Simulation

A hands-on Identity and Access Management (IAM) lab built with Keycloak, Docker and Ubuntu on VMware.

**Status: in progress.** I am building this step by step and recording each stage in this repository's history.

## Progress
- [x] Virtual machine and Docker
- [x] Keycloak running
- [x] Company realm, departments and roles (RBAC)
- [x] Bulk employee import from CSV via the Admin REST API
- [x] Single Sign-On across three department apps
- [x] Multi-Factor Authentication for Finance
- [x] LDAP federation

## Design: who can open what (RBAC)

| Department (group) | Role (badge) | Portal they may open |
|---|---|---|
| hr | hr-access | HR portal |
| engineering | engineering-access | Engineering portal |
| finance | finance-access | Finance portal (also requires MFA) |

People are never given roles directly. They join a department, and the department carries the role. Offboarding is one action: remove the person from the group.

## Automation scripts
| Script | What it does |
|---|---|
| `import_users.py` | Reads a CSV and creates employees and department memberships through the Keycloak Admin REST API |
| `require_mfa.py` | Requires every member of the Finance group to enrol an authenticator app |
| `provision_realm.py` | Builds a full company setup (realm, groups, roles, role mappings) from scratch |
| `csv_to_ldif.py` | Converts a CSV employee list into an LDIF file that fills the OpenLDAP directory |
| `assign_ldap_groups.py` | Places users imported from LDAP into their Keycloak department groups |

All scripts ask for the admin password at run time, so no secrets are stored in the repository.

## Custom Keycloak plug-in (SPI)
`business-hours-spi/` contains a custom Authenticator written in Java. It blocks logins outside configurable business hours and is applied only to the Finance portal through a per-client authentication flow override.
