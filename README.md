# Zero Trust Mini-Company Simulation

A hands-on Identity and Access Management (IAM) lab. I built a pretend company, **Acme Corp**, with three departments and put **Keycloak** in front of every application, so that nobody and nothing is trusted by default.

**Stack:** Keycloak 26, Docker Compose, Ubuntu Server (VMware), OpenLDAP, oauth2-proxy, Python (Admin REST API), Java (custom SPI)

## The problem
A company has several internal applications. Each one handling its own logins means inconsistent security, painful onboarding and offboarding, and no single place to see who can access what.

## The solution
- **Single Sign-On (SSO):** employees log in once to reach every portal they are allowed to use
- **Role-Based Access Control (RBAC):** people belong to department groups, groups carry roles, roles decide which portal opens. Nobody is granted access one by one
- **Multi-Factor Authentication (MFA):** the Finance department must also enter a time-based one-time code (TOTP)
- **Automated onboarding:** a Python script bulk-creates employees from a CSV file using the Keycloak Admin REST API
- **LDAP federation:** Keycloak authenticates employees stored in a separate OpenLDAP directory, as many companies do with Active Directory
- **Infrastructure as Code:** a script builds a complete realm (groups, roles, mappings) from nothing
- **Custom SPI:** a Java authenticator that blocks logins outside business hours

## Architecture

    Browser --> oauth2-proxy (one per portal) --> HR / Engineering / Finance sites
                       |
                       v
                   Keycloak  <---- LDAP lookups ----  OpenLDAP (employee directory)

## Access matrix
| Department | Role | Portal | Extra requirement |
|---|---|---|---|
| hr | hr-access | HR portal | none |
| engineering | engineering-access | Engineering portal | none |
| finance | finance-access | Finance portal | MFA (TOTP) |

## Screenshots
ADD YOUR SCREENSHOTS HERE, for example:
![One login opens all three portals](screenshots/10-all-3-clients-logged-in.png)

![Engineering portal refused for the wrong role](screenshots/09-engineering-forbidden.png)

![Finance portal refused for the wrong role](screenshots/08-finance-forbidden.png)

All screenshots, in the order I built the project, are on the [screenshots page](SCREENSHOTS.md).

## What I learned
I learned that logging in and being allowed in are two different checks: authentication and authorization. My login worked but the portal returned a 500 error until I added an Audience mapper in Keycloak. I also learned that one browser keeps all login cookies for the same address, which made the third portal fail until I raised nginx’s header size limit. Reusing passwords between systems is risky, so I now use a password manager.

## What I would improve next
- Serve everything over HTTPS instead of HTTP
- Enforce MFA with conditional authentication flows instead of per-user required actions
- Map LDAP groups to Keycloak groups automatically
- Move the realm configuration into Terraform

## How to run it
1. Create an Ubuntu Server VM and install Docker
2. Copy `.env.example` to `.env` and fill in your own values
3. `docker compose up -d`
4. Follow the realm, group and role setup, then run `import_users.py`

## Safety note
No real passwords or secrets are stored in this repository. The `.env` file is excluded through `.gitignore`.
