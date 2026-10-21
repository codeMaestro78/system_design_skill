# Security and threat modeling

Use this for: a fast pass on threat modeling, authorization, tenancy, and privacy across users, tenants, services, tools, and external inputs.

Sources: [OWASP threat modeling](sources.md#security-and-privacy), [OWASP authorization and tenant security](sources.md#security-and-privacy), [NIST Privacy Framework](sources.md#security-and-privacy).

**Canonical guide:** [Security, privacy, and threat modeling](security-privacy.md). That file is the source of truth for the full isolation inventory and privacy lifecycle; this page is only a first pass.

## Decision rules

- Draw actors, assets, data stores, entry points, data flows, and trust boundaries before writing controls. Classify sensitive data and high-impact actions.
- At each boundary ask what can go wrong: spoofed identity, unauthorized object or action, input abuse, data disclosure, tampering, denial of service, compromised dependency, operator error. STRIDE is one optional prompt, not a required checklist.
- Rank plausible threats by impact and likelihood where evidence exists. For each, record prevention, detection, response, owner, and a verification method. Revisit after a new data flow, integration, privileged tool, or tenancy model.
- Authenticate principals, then authorize every sensitive action and object in the service that owns it. A gateway check alone is insufficient, and a client-supplied tenant ID is never authority.
- Tenant isolation spans compute, database, cache, search, object storage, queue, encryption keys, logs and metrics, backups, admin and support paths, analytics, and AI retrieval. Compare shared-pool, hybrid, and silo isolation against blast radius, noisy neighbors, residency, cost, and deletion. Verify isolation in caches, queues, search, storage, and logs, not only in the primary database; login does not itself provide tenant isolation.
- Least-privilege identities for humans and services. Authorize every action and object in the service that owns it, deny by default, and audit privileged and data-export actions. Manage secrets with access control, rotation, and audit. Validate untrusted input and limit request cost and fan-out. Minimize collection and copies first; protect transport and stored data according to the threat model.
- Define retention, deletion propagation, backups, key disposal, access review, dependency and CI integrity, and a security incident path. Record useful audit events without secrets or excess personal data. Encryption does not compensate for broken authorization or compromised code.
- Legal retention, deletion, and residency claims require current authoritative research for the relevant jurisdiction. This is design guidance, not a legal rulebook.

## Where to go next

- Full threat-model workflow, isolation models, privacy lifecycle, and trade-offs: [security and privacy](security-privacy.md).
- Data classification and ownership that drive the controls: [data architecture](data-architecture.md).
- Detection, drills, and incident practice: [reliability, performance, and production operations](reliability-operations.md).
