<!-- Use when a complex, high-impact, cross-team, or production design needs one document that carries the decision, the model, the alternatives, and the plan. -->

# <System or feature> design doc

Tier: A | B | C, because <the trigger that sets the tier>
Required sections for this tier: <list>
Author: <role or name>
Date: YYYY-MM-DD
Status: Draft | In review | Approved
Reviewers: <roles who must sign off, and the date each signed>
Scope: <what this design covers, and what it explicitly excludes>
Labels: Observed | Given | Assumed | Estimated | Recommended | Open

Omit a section only when it does not affect the decision, and say why in one line under its heading: "Not applicable: <reason>". A blank heading is not a valid omission. Label any statement whose status could be confused.

## 1. Executive decision

- Goal and system boundary: <what is inside the boundary, what is outside, and for which actors>
- Recommended architecture: <a few sentences naming the components and the shape>
- Most important trade-offs: <the two or three that actually decided the outcome, and why this fit>
- Confidence: <high, medium, low, and what drives the confidence>
- Top risks: <risk, and the mitigation>
- Decisions needed from stakeholders: <decision, who makes it, and the default if no answer arrives>

## 2. Context and requirements

| Item | Requirement/constraint | Status/source | Priority | Verification |
|---|---|---|---|---|
| Critical user journey | | | Must/Should/Could/Out of scope | <how it is verified> |
| Availability/recovery | | | | |
| Latency/throughput/freshness | | | | |
| Security/privacy/tenancy | | | | |
| Cost/team/region/regulation | | | | |

Exclusions: <what this design deliberately does not do>
Actors: <human and machine actors, and their capabilities>
Data classes: <classification per data set, and its jurisdiction>
Jurisdictions: <regions and legal regimes in scope>
Operational owners: <who runs this in production, and who is on call>
Design horizon: <date or release the design is expected to hold>

Assumptions, each with an owner or a validation action:

| Assumption | Owner | Validation action | Due |
|---|---|---|---|
| | | | |

## 3. Workload and capacity model

Scenarios: <low/base/high or current/future, with the reason for each>

| Quantity | Low | Base | Peak | Units | Source/assumption | Uncertainty | Decision sensitivity |
|---|---|---|---|---|---|---|---|
| Request rate (average) | | | | req/s | | | |
| Peak factor | | | | x | | | |
| Read/write mix | | | | % | | | |
| Fan-out | | | | requests per request | | | |
| Concurrency (Little's Law) | | | | in flight | | | |
| Payload size | | | | bytes | | | |
| Storage/retention | | | | GB and days | | | |
| Queue arrival vs service rate | | | | msg/s | | | |
| Data locality | | | | % | | | |
| Failure headroom | | | | % of capacity | | | |
| Cost drivers | | | | see section 15 | | | |

Formulas used, with units:

- Average rate = <requests> / <seconds>
- Peak rate = average rate x <peak factor>
- Concurrency = arrival rate [req/s] x mean duration [s] = in flight (Little's Law; an average, not a ceiling)
- Storage = writes/day x bytes/row x retention days x replica and overhead factor
- Bandwidth = requests/s x payload bytes x fan-out x (1 + protocol overhead)

First likely bottleneck: <the component that saturates first, and the headroom that remains at peak>
Scale trigger: <the metric and threshold that starts scaling work, and who watches it>

Detail: [capacity-model.md](capacity-model.md)

## 4. Domain, APIs, and data

- Bounded contexts and owners: <context, owning team, what it owns>
- Invariants: <business rule, where it is enforced, and how concurrency is handled>
- Source of truth: <the authoritative store per fact>

| Contract | Type | Owner | Consumers | Compatibility policy | Quota/error semantics |
|---|---|---|---|---|---|
| | REST/gRPC/event/file | | | | |

- Auth context: <identity type, claims, tenant binding, where authorization is enforced>
- Data model: entities, keys, constraints, ownership, lifecycle, retention and deletion
- Consistency and transaction boundaries: <what commits atomically, what is eventually consistent, and the user-visible delay>
- Derived data: caches, materialized views, search indexes, analytics feeds, and for each: source of truth, freshness target, invalidation method, rebuild and reconciliation path
- Schema evolution, backfill, and migration assumptions: <see section 16>

Detail: [data-model.md](data-model.md), [api-contract.md](api-contract.md)

## 5. Architecture diagrams

Include only diagrams that answer a decision. Mark illustrative elements and vendor-specific choices. Do not imply guarantees the design does not provide.

1. Context and deployment: actors, external systems, trust boundaries, regions and zones, owners.
2. Container and component: responsibilities, deployments, protocols, data stores, dependency direction.
3. Sequence: the critical success path, and the most important failure, retry, or compensation path.
4. Data model: entities, keys, invariants, ownership, lifecycle.

## 6. Critical flow contracts

For each critical flow: steps, caller deadline, authorization check, data read and write, transaction, async handoff, idempotency key or deduplication, ordering and freshness, response to the user, observability, failure recovery.

| Flow | Deadline | Authz check | Idempotency/dedup | Ordering/freshness | Timeout-after-write behaviour | Failure recovery |
|---|---|---|---|---|---|---|
| | | | | | | |

Explicitly cover the ambiguous timeout after a write and duplicate delivery.

## 7. Decisions and alternatives

| Decision | Option chosen | Alternatives considered | Evidence/fit | Costs and risks | Revisit trigger |
|---|---|---|---|---|---|
| Architecture style | | | | | |
| Data/consistency | | | | | |
| API/messaging | | | | | |
| Deployment/recovery | | | | | |

Include the simplest viable option. Durable decisions become ADRs indexed in section 20: [adr.md](adr.md). Until then, mark a row "promote to ADR if <condition>".

| Decision | Promote to ADR if | ADR link |
|---|---|---|
| | | |

## 8. Security, privacy, and abuse

Assets: <what must be protected>
Actors and capabilities: <who acts, with what access>
Entry points: <surface>
Trust boundaries: <where trust changes>
Data flows: <where data moves, and its class>
Tenant boundaries: <how tenants are separated, and across which layers>

Prioritized threats, each with impact, likelihood basis, prevention, detection, response, owner, evidence, and residual risk: [threat-model.md](threat-model.md)

Also cover: authentication versus authorization, object and property checks, secrets and keys, data minimization, retention and deletion, audit, supply chain, and AI prompt or tool boundaries where applicable.

Jurisdictional or legal claims requiring authoritative review: <claim, and who reviews it>

## 9. Reliability and operational model

- SLIs/SLOs: <indicator, target, window> ([slo-and-error-budget.md](slo-and-error-budget.md))
- User-facing alert conditions: <symptom, threshold, who is paged>
- Error budget: <if used, how it gates releases>
- Failure domains: <process, host, zone, region, dependency, vendor, human>
- Overload limits and degradation: <what sheds load, what degrades, what is refused>
- Failover: <mechanism, detection, and the data loss it can cause>
- RTO and RPO: <per service and data class>
- Retries, timeouts, bulkheads, circuit breakers: <semantics, budgets, and where the budget is enforced>
- Backups and successful restore evidence: <what is backed up, and the date of the last successful restore drill>
- Recovery runbooks: [runbook.md](runbook.md)
- Metrics, logs, and traces: <signal, cardinality policy, privacy rule>
- Deployment, rollout/rollback: <mechanism, staged percentages, stop conditions>
- On-call ownership and incident process: <rotation, escalation, incident commander>
- Capacity, quotas, cost signals, and backup/telemetry retention: <see sections 3 and 15>
- Exit considerations: <portability, data export, contract termination>

## 10. Risk register

| Risk/scenario | Impact | Likelihood/confidence | Mitigation/detection | Recovery/owner | Test/evidence |
|---|---|---|---|---|---|
| | | | | | |

Rank only when evidence supports it. State uncertainty rather than false precision.

## 11. Delivery and validation plan

| Milestone | Depends on | Owner | Acceptance evidence | Rollout | Rollback | Stop/continue gate |
|---|---|---|---|---|---|---|
| | | | | | | |

Include contract, security, performance, recovery, restore, and migration tests. For a repository review, separate findings by severity and cite exact file paths and symbols. Do not change code unless requested. Rollout and rollback are specified separately in section 13.

## 12. Open decisions

| Question | Why it changes the design | Who can answer | Default assumption if no answer |
|---|---|---|---|
| | | | |

Do not block progress on details that do not materially alter the architecture.

## 13. Rollout and rollback plan

- Stages and population: <the sequence, internal then small percentage then increasing, or the cohorts, one tenant, one region, one client version. State what stays constant in each stage and what may change>
- Per-stage observation window and gate metric: <metric, comparison window, threshold. "Healthy" is not a gate>
- Stop and continue gates in both directions: <the stop condition, who may call it, the default action if nobody calls it, and the maximum time before the default fires>
- Blast radius control: <the flag, tenant allowlist, region pinning, or capacity partition that bounds who is affected when the change is wrong>
- Rollback safety: <what rollback actually reverts, separating code only, code plus schema, data written by the new path, and already-emitted events. Name what it cannot revert>
- Incompatibility list:

| Incompatible state | Effect on the old version | Compatibility mechanism | Window |
|---|---|---|---|
| | | | |

- Mixed-version operation: <which deployments coexist, the rollout order, and the version range supported at each point>
- Data written by the new path: <how it is repaired or reconciled if the rollout stops, and who owns the repair>

## 14. Operational readiness checklist

Status values, used identically everywhere in this brief:

- **VERIFIED**: tested or exercised in a production-like environment, and the test is named.
- **CONFIGURED BUT UNPROVEN**: the thing exists but nothing has exercised it. A dashboard with no traffic, a runbook never followed, a backup job with no restore.
- **UNKNOWN**: nobody checked, or the check is not yet possible. An unknown is a finding, not a formality.

| Check | Status | Evidence or test | Owner | Action if not verified |
|---|---|---|---|---|
| On-call owner named for every new component and every new alert | | | | |
| Dashboards live and populated with production-shaped data | | | | |
| Alert thresholds set, each with a stated rationale for the value | | | | |
| Runbook linked for every user-facing alert | | | | |
| Rollback rehearsed end to end, not only described | | | | |
| Restore drill performed, with the measured RTO and RPO recorded | | | | |
| Capacity headroom known for peak, failover, and loss of one dependency | | | | |
| Credentials, certificates, and quota ceilings monitored with expiry alerts | | | | |
| Support and on-call briefed on the new failure mode | | | | |
| Cost anomaly detection and budget signal live | | | | |

Remove rows that do not apply and explain the removal. A checklist where every row reads VERIFIED is a checklist that was not performed. Full checklist: [launch-readiness-checklist.md](launch-readiness-checklist.md).

## 15. Cost model

Unit of account: <one per request path, for example per API call, per active tenant, per gigabyte stored, per million events>

```
monthly_cost = fixed_platform_cost
             + requests_per_month * cost_per_request
             + stored_gb * cost_per_gb_month
             + egress_gb * cost_per_gb_egress
             + write_ops * cost_per_write
             + engineering_hours * loaded_hour_cost
```

| Term | Unit price | Source and date checked | Quantity at base | Cost at base | Quantity at 3x | Cost at 3x |
|---|---|---|---|---|---|---|
| Fixed platform | | | | | | |
| Requests | | | | | | |
| Storage | | | | | | |
| Egress | | | | | | |
| Write operations | | | | | | |
| Engineering hours | | | | | | |

- Fixed and variable split: <what is paid whether or not traffic arrives, and what scales with it>
- Cost drivers ranked by sensitivity: <which term moves the number most at base load and at 3x, and why>
- Per-tenant economics: <cost per tenant per month, per active user, and the smallest-tier floor>
- Monthly run-rate shape: <base, expected peak, and at least one failure scenario, for example a region unavailable or a runaway retry loop>
- Budget guardrail: <threshold, who is notified, and the response>
- Cost of the rejected options: <what each alternative costs per month>
- Excluded costs: <what is deliberately not modelled, so the number is not read as complete>

## 16. Migration plan

- Source of truth during and after the migration:

| Data set or field | Source of truth before | Source of truth during | Source of truth after |
|---|---|---|---|
| | | | |

- Phases:

| Phase | Entry criteria | Changes | Exit criteria | Sign-off owner |
|---|---|---|---|---|
| Expand | | | | |
| Backfill | | | | |
| Dual write | | | | |
| Cutover | | | | |
| Contract | | | | |

- Dual-write mechanics: <which write is authoritative, how divergence is detected, the comparison cadence, the tolerated difference, and the kill switch>
- Backfill: <batch size, throttle, checkpoint, idempotency key, rate limit against the source, lock impact, and behaviour when a source row changes mid-backfill>
- Cutover signal: <the measured condition that ends the dual-write window, and the observation window defined before the cutover>
- Rollback versus forward repair: <which one is available at the cutover point, decided in advance>
- Cleanup criteria: <what must be observed, and for how long, before the old path, schema, code, and compatibility layer are removed. Named owner and date>
- Mixed-version deployment: <which versions run simultaneously, how long, and what contract old clients get>
- Reconciliation and repair tooling: <what runs, on what schedule, what it reports, and how a human resolves findings>

Full plan: [migration-plan.md](migration-plan.md)

## 17. API contract artifact

One worked example, not a list of field names. Replace the values, keep the shape.

Request:

```http
POST /v1/payments HTTP/1.1
Idempotency-Key: 7f3c1a52-9d0e-4f6b-8a11-2c4d6e8f0a13
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": "ord_8812",
  "amount": { "value": 4250, "currency": "USD" },
  "payment_method_id": "pm_5510"
}
```

Response:

```http
HTTP/1.1 201 Created
Location: /v1/payments/pay_9f21

{
  "id": "pay_9f21",
  "status": "pending",
  "amount": { "value": 4250, "currency": "USD" },
  "created_at": "2026-04-02T10:14:31Z"
}
```

Error, RFC 9457 problem details:

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{
  "type": "https://errors.example.com/idempotency-key-reuse",
  "title": "Idempotency key reused with a different payload",
  "status": 409,
  "code": "idempotency_key_payload_mismatch",
  "detail": "The key was first used with a different request body.",
  "instance": "/v1/payments",
  "request_id": "req_1a77",
  "retryable": false
}
```

Also state: the unit and currency of every numeric field, which fields are required versus optional and what an omitted field means, the default and maximum page size, the error codes a client can branch on, the deadline the server enforces, and the idempotency key scope, retention, and mismatch rule. Attach the machine-readable schema and the compatibility check that runs against it. Full contract: [api-contract.md](api-contract.md).

## 18. Ownership table

| Component or data | Owning team | On-call | Escalation | Data owned and class | Notes |
|---|---|---|---|---|---|
| | | | | | |

One row per deployable component and per dataset. A dataset has exactly one owning team. On-call names the rotation. Escalation names the path and the timeout.

## 19. AI and agent boundary

- Autonomy level: <the highest action the agent may take without a human in the loop, and the conditions that raise or lower it>
- Tool inventory:

| Tool | Reads | Changes | Resource owner | Trust boundary crossed | Reversible? | Blast radius of misuse |
|---|---|---|---|---|---|---|
| | | | | | | |

- Approval gates: <which actions pause, what the approver sees, the default on timeout, and how long an approval stays valid>
- Evaluation plan: <task set, pass criteria, production shadow period, regression gate, and who blocks a release>
- Prompt injection and exfiltration posture: <what is untrusted input, whether retrieved or user text can carry instructions, what the model may never reveal, the egress boundary, and the logging policy>
- Failure behaviour: <what happens when output is malformed, a tool call is rejected, or the model is unavailable>
- Audit: <what is recorded per action, retained for how long, and who can review it>
- Stop mechanism: <the kill switch, who holds it, and the maximum time to stop the agent>

## 20. ADR index

| ADR | Title | Status | Date | Decision summary | Link |
|---|---|---|---|---|---|
| 0001 | | Proposed/Accepted/Superseded by ADR NNNN/Deprecated/Rejected | | | [adr.md](adr.md) |

Durable decisions only. Each ADR holds the context, the options considered, the decision, and the accepted consequences, including the ones nobody wanted. A decision in section 7 with no ADR behind it is a decision that will be re-litigated.

## 21. Glossary

| Term | Meaning in this design |
|---|---|
| | |

Domain nouns a reader outside the team needs, the acronyms used in the diagrams, and the internal names of systems. Exclude what a general engineering reader already knows.

## 22. Evidence appendix

| Claim in the brief | Source | Author or publisher | Date or version | Platform | Scope and limits |
|---|---|---|---|---|---|
| | | | | | |

Primary sources only, unless the claim is inherently case-specific. Record the date or version checked and the scope: one vendor, one region, one product edition, one company scale. Curated index: [sources.md](../references/sources.md).

## Parallel specialty review

For a truly cross-domain design, the lead may delegate bounded reviews. Give every reviewer the same assumptions and this snapshot. Request concise evidence-backed findings, not alternative full designs.

| Reviewer specialty | Question asked | Findings | Reviewer | Date |
|---|---|---|---|---|
| Requirements/capacity | <what to challenge> | | | |
| Data/API | | | | |
| Reliability | | | | |
| Security/privacy | | | | |
| Cost/platform | | | | |

The lead resolves disagreements, records unresolved questions, and remains accountable for the recommendation.

## Reviewer audit trail

| Reviewer | Scope given | Finding | Disposition | Rationale | Owner of follow-up |
|---|---|---|---|---|---|
| Requirements and capacity reviewer | | | Accepted/Rejected/Deferred | | |
| Data and API reviewer | | | | | |
| Reliability reviewer | | | | | |
| Security and privacy reviewer | | | | | |
| Cost and platform reviewer | | | | | |

A finding with no disposition means the review is not finished. Record the findings the lead disagreed with as prominently as the accepted ones, and state whether any reviewer disagreed with the recommended architecture.

## Before you deliver

- The tier is stated with its reason, and every section required for that tier is present.
- Every omitted section says why in one line. A blank heading is not an omission.
- No invented numbers. Every rate, size, duration, price, and cost carries units, a source or a stated assumption, and a range where uncertainty is material.
- Every component maps to a requirement, a constraint, or a named risk reduction. Components that map to nothing are removed.
- Every diagram agrees with the prose, and no diagram implies a guarantee the design does not provide.
- The status vocabulary is used identically: VERIFIED, CONFIGURED BUT UNPROVEN, or UNKNOWN, and nothing is marked VERIFIED without a named test.
- Restore and rollback are drills with an owner and a date, not intentions.
- Open decisions have a default assumption so the work is not blocked on a question that does not change the architecture.
