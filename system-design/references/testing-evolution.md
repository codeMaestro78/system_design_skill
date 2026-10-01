# Architecture testing, migration, and evolution

## Verification portfolio

Tie tests to requirements, risks, and failure modes. Use the lowest-cost test that gives credible evidence, but do not substitute unit tests for cross-boundary behavior.

- Unit/domain tests: invariants, authorization rules, state transitions.
- Contract/schema tests: provider-consumer compatibility, event evolution, generated API docs.
- Integration tests: actual database, queue, identity, and external adapters.
- End-to-end journey tests: critical user outcomes and degraded behavior.
- Property/model-based tests: stateful protocols, idempotency, concurrency, invariants.
- Performance/load/soak tests: latency percentiles, throughput, queue drain, resource saturation, realistic data.
- Resilience tests: timeout, failover, dependency outage, overload, zone loss, restore, network fault, recovery.
- Security/privacy tests: negative authorization, tenant isolation, abuse/limits, secrets, data deletion, audit.
- Operational exercises: deploy/rollback, backup restore, incident drills, failover and runbooks.

Specify test environment, data safety, success criteria, abort conditions, and production blast radius. Tests should prove properties meaningful to the user, not just mirror code structure.

## Migrations

Plan expand/contract changes for APIs, database schemas, events, and infrastructure. Support mixed-version deployment where necessary. For data movement, state source of truth, backfill idempotency, checkpoints, rate limits, validation/reconciliation, dual-read/write window, cutover signal, rollback/forward repair, and cleanup. Estimate migration load and lock impact; rehearse on production-like volume. Never assume rollback is safe after irreversible writes.

For service extraction, first establish module ownership/contracts and measure the reason for separation. Move one bounded capability, add telemetry and reconciliation, then remove old paths only after traffic and correctness evidence. Strangler migration should include routing, coexistence, data ownership, rollback, and retirement plan.

## Evolution and fitness functions

Architecture changes as requirements and evidence change. Use lightweight fitness functions (automated checks or operational measures) for key constraints: dependency direction, API compatibility, latency budget, tenant isolation, cost ceiling, or restore objective. Make checks enforceable only where ownership and false-positive handling exist. Keep ADRs, diagrams, contracts, and runbooks current as part of change work.

Use feature flags with owner and expiry. Avoid permanent dual systems and compatibility paths without retirement criteria. Revisit decisions when demand, team ownership, regulations, platform capabilities, cost, or failure evidence crosses a stated trigger.
