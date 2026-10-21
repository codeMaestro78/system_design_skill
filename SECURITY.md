# Security Policy

## Scope

This repository distributes an Agent Skills package. The skill reads a user's repository, configuration files, and documentation, and produces architecture guidance.

Reports about the skill itself are in scope, including:

- Prompt injection that reaches the skill through repository content, issue text, pull request text, or evaluation fixtures, and that changes the guidance the skill produces.
- Instruction handling that lets untrusted content override the skill's workflow.
- Unsanitized handling of repository content that leaks credentials, tokens, or private paths into a response.
- Insecure code in the repository's own scripts, workflows, or dependencies.

Design disagreements are not security reports. Use a feature request or an issue for those.

## Reporting a vulnerability

Report privately through GitHub's vulnerability reporting on the repository:

<https://github.com/codeMaestro78/system_design_skill/security/advisories/new>

If that form is unavailable, contact the maintainer (@codeMaestro78) through GitHub and ask for a private channel. Do not open a public issue for a vulnerability that is not yet fixed.

Include:

- What the skill does that is wrong, and the path in the skill that allows it.
- The untrusted input that triggers it, and the resulting behavior.
- How to reproduce it, with the smallest example that shows the problem.
- The impact you expect, and whether you know of a way to limit it.

## Response

The maintainer will acknowledge a report, confirm whether it is in scope, and work on a fix. Fixes are released in a new version and listed in [CHANGELOG.md](CHANGELOG.md). Reports are credited unless you ask otherwise.

Please give a reasonable amount of time for a fix before disclosing the issue publicly.
