# Security and threat modeling

Use throughout design, especially across users, tenants, services, tools and external inputs. Sources: [OWASP threat modeling](sources.md#security-and-privacy), [OWASP authorization and tenant security](sources.md#security-and-privacy), [NIST Privacy Framework](sources.md#security-and-privacy).

## A compact threat model

1. Draw actors, assets, data stores, entry points, data flows and trust boundaries. Classify sensitive data and high-impact actions.
2. At each boundary, ask what can go wrong: spoofed identity, unauthorized object/action, input abuse, data disclosure, tampering, denial of service, compromised dependency or operator error. STRIDE is one optional prompt, not a required checklist.
3. Rank plausible threats by impact and likelihood when evidence exists. For each, identify prevention, detection, response/recovery, owner and a verification method.
4. Revisit after adding a new data flow, integration, privileged tool or tenancy model.

## Controls to review

- Authenticate principals; authorize every sensitive action and object in the service that owns it. A gateway check alone is insufficient. Bind tenant context to authenticated membership; never treat a caller-supplied tenant ID as authority. Verify isolation in caches, queues, search, storage and logs.
- Give humans and services least-privilege identities. Manage secrets with access controls, rotation and audit. Protect transport and stored data according to the threat model; minimize collection first.
- Validate untrusted input; limit requests, cost and fan-out; protect against abuse. Record useful audit events without secrets or excess personal data.
- Define retention, deletion propagation, backups, key disposal, access review, dependency/CI integrity, and a security incident path.

Encryption does not compensate for broken authorization or compromised application code. Legal retention, deletion and residency claims require current authoritative research for the relevant jurisdiction; this reference is design guidance, not a legal rulebook.
