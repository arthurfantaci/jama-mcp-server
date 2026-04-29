# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately via GitHub's [private vulnerability reporting](https://github.com/arthurfantaci/jama-mcp-server/security/advisories/new) feature, **not** via public issues.

When reporting, include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce.
- The affected version or commit.
- Any suggested mitigations.

You should receive an acknowledgment within 5 business days. We aim to release a fix within 30 days for critical vulnerabilities.

## Scope

In-scope vulnerabilities include:

- Credential leakage from logs, error messages, or persisted state.
- Authorization bypass against the Jamacloud REST API.
- MCP protocol-level injection or sandbox escape.
- Dependency-chain vulnerabilities (verified via `actions/dependency-review-action` on PRs).

Out-of-scope:

- Vulnerabilities in upstream Jamacloud, the MCP specification, or external libraries (please report those to the respective maintainers).
- Issues that require physical access to the user's machine.

## Secret hygiene

This project never commits secrets:

- `.env` files are gitignored; only `.env.example` (with empty placeholder values) is tracked.
- `gitleaks` runs as a pre-commit hook and scans every commit for accidentally staged credentials.
- OAuth client credentials are provisioned per-developer via Jama Connect's REST API credentials panel and rotated after sharing or compromise.

If you accidentally commit a secret, rotate the affected credential immediately and follow up with a private vulnerability report so the repository history can be rewritten if necessary.
