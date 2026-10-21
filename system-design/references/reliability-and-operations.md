# Reliability and operations

Use this for: a fast pass on production readiness, incident or scaling review, and recovery design.

Sources: [Google SRE](sources.md#sre-reliability-operations), [AWS Reliability Pillar](sources.md#sre-reliability-operations), [OpenTelemetry](sources.md#sre-reliability-operations), [NIST incident response](sources.md#sre-reliability-operations).

**Canonical guide:** [Reliability, performance, and production operations](reliability-operations.md). That file is the source of truth for SLO, RTO, and RPO guidance; this page is only a first pass.

## Decision rules

- Measure service level indicators on critical user journeys, then set an SLO with a window, denominator, and owner. An error budget is the tolerated gap. An SLA is contractual and need not equal the internal SLO. Never substitute "high availability" for a target.
- Derive RTO and RPO from business impact, assign them to services and data classes, and test a restore. A configured backup or a green backup job is not proof of recoverability.
- For each dependency, list failure mode, affected users, detection, isolation or degradation, failover, and recovery. Include overload, regional failure, data corruption, expired credentials, bad deploy, and operator error.
- Instrument metrics, logs, and traces with correlation IDs so an operator can name the failing journey. Bound label cardinality and keep secrets and personal data out of telemetry.
- Roll out progressively: staged rollout, canary, or blue/green where risk justifies, plus feature flags with ownership and expiry, health criteria, and a tested rollback. A rollback that depends on a schema change is not a rollback unless the change is backward compatible or the forward-repair path is rehearsed. Redundancy adds coordination, split-brain, and cost, so explain its assumptions.
- Avoid "zero downtime" and "zero data loss" unless the design and the tests support the literal promise, and do not pick targets from current uptime alone. Set separate objectives for critical paths, asynchronous completion, and data freshness when needed.
- Capacity: forecast peaks, watch saturation, queue age, and hot partitions. Load test with representative data and failure modes, and define abort conditions.
- Incidents need a named responder, escalation, runbooks, communications, and a blameless postmortem. Run failover and disaster recovery drills; run chaos experiments only with a hypothesis and safety limits.

**Review test:** can an operator detect the failure, tell which users are affected, stop further damage, and restore the service within its stated targets?

## Where to go next

- Full objectives, resilience, observability, and launch-readiness guidance: [reliability, performance, and production operations](reliability-operations.md).
- Capacity sizing and load testing: [requirements and capacity](requirements-and-capacity.md).
- Backup scope, restore drills, and data lifecycle: [data architecture](data-architecture.md).
- Security incident path and tenant isolation: [security and privacy](security-privacy.md).
