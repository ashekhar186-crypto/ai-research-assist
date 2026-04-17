# Security Policy

## Supported Usage

This repository is intended for active development use. Security fixes should be applied to the default branch and released through normal repository updates.

## Reporting a Vulnerability

Please do not open a public issue for security-sensitive reports.

Instead:

1. Contact the maintainer privately through GitHub
2. Include a clear description of the issue, impact, and reproduction steps
3. Share only the minimum information needed to validate the report safely

## Sensitive Data Handling

- Never commit real API keys, tokens, or passwords
- Never commit user-uploaded research documents
- Never commit local database files or vector indexes

If a credential is exposed, rotate it immediately before any further publishing or deployment activity.
