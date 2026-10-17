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
