# Complex design brief and architecture review

Use this as a structure for complex, high-impact, cross-team, or production architecture work. Omit sections that do not affect the decision. Label each statement **Observed**, **Given**, **Assumed**, **Estimated**, **Recommended**, or **Open** when its status could be confused.

## 1. Executive decision

- Goal and system boundary
- Recommended architecture in a few sentences
- Most important trade-offs and why this fits
- Confidence, top risks, and decisions needed from stakeholders

## 2. Context and requirements

| Item | Requirement/constraint | Status/source | Priority | Verification |
|---|---|---|---|---|
| Critical user journey | | | | |
| Availability/recovery | | | | |
| Latency/throughput/freshness | | | | |
| Security/privacy/tenancy | | | | |
| Cost/team/region/regulation | | | | |

Include explicit exclusions, actors, data classes, jurisdictions, operational owners, and design horizon. List assumptions with an owner or validation action.

## 3. Workload and capacity model

Show low/base/peak or current/future scenarios only when useful. Record average/peak request rates, read/write mix, fan-out, concurrency, payloads, storage/retention, queue arrival/service rates, data locality, failure headroom, and cost drivers. Include formulas, units, source/assumption, uncertainty, and decision sensitivity. Identify the first likely bottleneck and scale trigger.

## 4. Domain, APIs, and data

- Domain boundaries, owners, invariants, source of truth
- API/event contracts, auth context, compatibility, quotas and error semantics
- Data model/access patterns, classification, retention/deletion, consistency and transaction boundaries
- Derived data, caches, queues, search/analytics, and rebuild/reconciliation paths
- Schema evolution, backfill and migration assumptions

## 5. Architecture diagrams

Include only diagrams that answer a decision:

1. Context/deployment: actors, external systems, trust boundaries, regions/zones, owners.
2. Container/component: responsibilities, deployments, protocols, data stores and dependency direction.
3. Sequence: critical success path and the most important failure/retry/compensation path.
4. Data model: entities, keys, invariants, ownership, lifecycle.

Mark illustrative elements and vendor-specific choices. Do not imply guarantees the design does not provide.

## 6. Critical flow contracts

For each critical flow, show steps, caller deadline, authz check, data read/write, transaction, async handoff, idempotency key/deduplication, ordering/freshness, response to user, observability, and failure recovery. Explicitly cover ambiguous timeout after a write and duplicate delivery when relevant.

## 7. Decisions and alternatives

| Decision | Option chosen | Alternatives considered | Evidence/fit | Costs and risks | Revisit trigger |
|---|---|---|---|---|---|
| Architecture style | | | | | |
| Data/consistency | | | | | |
| API/messaging | | | | | |
| Deployment/recovery | | | | | |

Include simplest viable option. Record ADRs for durable decisions, with context and accepted consequences.

## 8. Security, privacy, and abuse

Map assets, actors, entry points, trust boundaries, data flows, tenant boundaries, and prioritized abuse/threat cases. For each material threat: impact, likelihood basis, prevention, detection, response, owner, evidence/test, residual risk. Include authentication vs authorization, object/property checks, secrets/keys, data minimization/retention/deletion, audit, supply chain, and AI prompt/tool boundaries where applicable. Flag jurisdictional/legal facts requiring authoritative review.

## 9. Reliability and operational model

- SLIs/SLOs, user-facing alert conditions, error budget if useful
- Failure domains, dependencies, overload limits, degradation, failover, RTO/RPO
- Retries/timeouts/bulkheads/circuit breakers with semantics and budgets
- Backups and successful restore evidence; recovery runbooks
- Metrics/logs/traces with privacy/cardinality policy
- Deployment, rollout/rollback, on-call ownership, incident process
- Capacity, quotas, cost signals, backup/telemetry retention, and exit considerations

## 10. Risk register

| Risk/scenario | Impact | Likelihood/confidence | Mitigation/detection | Recovery/owner | Test/evidence |
|---|---|---|---|---|---|
| | | | | | |

Rank only when evidence supports it; state uncertainty and avoid false precision.

## 11. Delivery and validation plan

Use phased milestones with dependency, owner, acceptance evidence, rollout, rollback, and stop/continue gate. Include contract/security/performance/recovery/restore and migration tests. For a repository review, separate findings by severity and cite exact file paths and symbols. Do not change code unless requested.

## 12. Open decisions

For each question, state why it changes the design, who can answer, and a default assumption if no answer arrives. Do not block progress on details that do not materially alter the architecture.

## Parallel specialty review

For a truly cross-domain design, the lead may delegate bounded reviews:

- Requirements/capacity reviewer: challenge workload, targets, and bottlenecks.
- Data/API reviewer: challenge ownership, invariants, contracts, and compatibility.
- Reliability reviewer: challenge failure domains, overload, recovery, and operations.
- Security/privacy reviewer: challenge trust boundaries, abuse, tenancy, and lifecycle.
- Cost/platform reviewer: challenge deployment, quotas, cost, portability, and team burden.

Give reviewers the same assumptions and design snapshot. Request concise evidence-backed findings, not alternative full designs or file changes. The lead resolves disagreements, records unresolved questions, and remains accountable for final recommendations. Use the available agent count proportionally; do not parallelize tightly coupled reasoning just to use agents.
