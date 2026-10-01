# Security, privacy, and threat modeling

## Threat-model workflow

Treat security and privacy as continuous design constraints. Define assets and data classes, actors and capabilities, entry points, data flows, trust boundaries, deployment dependencies, and misuse cases. Draw a data-flow diagram. Use STRIDE, attack trees, abuse cases, or another method as useful; no one taxonomy is complete. For each prioritized threat, record scenario, affected asset/tenant, impact and likelihood basis, prevention, detection, response/recovery, owner, test/evidence, and residual risk. Revisit after material changes and incidents.

## Identity and authorization

Separate human, service, workload, machine, and external identities. Prefer established identity protocols and short-lived/federated credentials when suitable. Define issuer, audience, expiry, rotation/revocation, recovery, session, and account lifecycle. Authentication identifies a caller; authorize each action/resource/property server-side, deny by default, use least privilege, and audit privileged/data-export actions. Bind tenant context to authenticated membership; never trust a client-supplied tenant ID alone.

Test object-level, property-level, function-level, nested-resource, background-job, export, search, pagination, batch, and admin paths, including denied and cross-tenant cases. Login does not itself provide tenant isolation.

## Multi-tenant isolation

Map tenant boundaries across compute, database, cache, search, object storage, queue, encryption keys, logs/metrics, backup, admin/support, analytics, and AI retrieval. Compare shared-pool, hybrid, and silo isolation against blast radius, noisy neighbors, residency, custom controls, cost, performance, provisioning, migration, and deletion. Propagate tenant context safely and test confused-deputy, IDOR, join, cache-key, and background-task leakage. Isolation is a continuum; choose per threat and customer promise.

## Data privacy and lifecycle

Map each data element's purpose, source, subject, sensitivity, storage, recipient/processor, geographic location, access, derived copies, and retention. Minimize collection and copies. Define retention and deletion across live stores, replicas, indexes, caches, logs, backups, exports, analytics, prompts, and embeddings; state unavoidable backup expiry limits. Define access/correction/export processes when applicable. Pseudonymization is not anonymization; encryption does not itself establish privacy compliance. Verify current law, jurisdiction, organizational role, and data class using authoritative sources; do not infer a legal conclusion.

## Secrets, cryptography, and supply chain

Keep secrets out of source, images, logs, tickets, prompts, client bundles, and build output. Define secret access, distribution, rotation, revocation, audit, and break-glass. Protect keys separately from ciphertext, including backup and recovery. Select current protocols/algorithms from current standards or provider documentation; do not invent cryptographic parameters. Encryption does not solve authorization, key compromise, plaintext exposure, or misuse.

Review dependency and base-image provenance/updates, CI/CD identities, artifact access/signing where warranted, environment separation, vulnerability response, patching, and secure build practices. Use a verifiable framework such as OWASP ASVS for requirements/testing when appropriate; Top 10 lists are awareness aids, not assurance.

## Detection and assurance

Audit identity, authorization failures, admin changes, exports, key/secret access, policy changes, and security events. Protect log integrity and restrict access; avoid recording unnecessary personal data. Plan alert/triage/containment/recovery, credential revocation, tenant isolation, evidence preservation, communication, and drills. Map important threats to controls and tests: negative authZ/tenant tests, secrets/dependency checks, infrastructure policy, deletion/restore exercises, tabletop or penetration testing proportional to risk.

## Trade-offs to state

- Shared pool lowers cost but expands cross-tenant blast radius and enforcement requirements; silo improves isolation but increases provisioning, cost, upgrades, and support work.
- Federated identity reduces local credential handling but adds IdP availability, claim mapping, account-linking, and recovery concerns.
- Managed KMS/secrets reduces operational burden but adds vendor trust, quotas, latency, and cost; self-managed custody requires mature rotation/recovery expertise.
- Short retention minimizes exposure but may reduce debugging/analytics; define purpose, access, redaction, and exceptions.
- Fine-grained/client-side encryption can reduce provider visibility but complicates search, recovery, sharing, and key loss.

Check current OWASP ASVS/API Security, NIST, OAuth/OIDC, cloud IAM, cryptography, and jurisdictional guidance before claiming current conformance or legal compliance. See [sources](sources.md).
