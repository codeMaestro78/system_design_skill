# Complex design brief and architecture review

Use this as a structure for complex, high-impact, cross-team, or production architecture work. Omit sections that do not affect the decision, and say why in one line. Label each statement **Observed**, **Given**, **Assumed**, **Estimated**, **Recommended**, or **Open** when its status could be confused. The fill-in twin of this structure, with a table or prompt for every section, is the [design doc template](../templates/design-doc.md); this file carries the rules a reviewer applies.

## Tiering: state the tier before writing

Every brief opens with a tier line and a reason, then only the sections that tier requires.

| Tier | Use when | Required |
|---|---|---|
| A | Reversible change in one service and one team: no new data class, no new dependency, no contract another team consumes | 1, 2, 7, 11 |
| B | Feature or cross-team change: new tenant-visible endpoint, event, or data class, new dependency, new team in the path | 1 to 7, 9, 11, 12 |
| C | New system, migration of a system of record, autonomous AI action, regulated data at a new boundary, cross-region, irreversible cutover | 1 to 22 |

Sections 8 and 10 stay conditional in every tier; Tier C adds 14 to 22 to the 1 to 12 core.

- State the tier and the reason in the first two lines. A tier with no stated reason was chosen after the fact.
- Do not inflate: a Tier A brief is four sections and about a page, and a brief whose size does not vary by tier has been padded.
- Do not under-serve: a Tier C brief missing the readiness checklist, cost model, migration plan, glossary, or evidence appendix is incomplete and is returned for those sections.
- Escalate on trigger, not size: A becomes B on a cross-team contract, a new data class, a new dependency, or an irreversible step; B becomes C on regulated data, a system of record, an autonomous agent, or a second region. Write the missing sections.
- A deliberately omitted section says why in one line.

## 1. Executive decision

- Goal and system boundary
- Recommended architecture in a few sentences
- Most important trade-offs and why this fits
- Confidence, top risks, decisions needed from stakeholders

## 2. Context and requirements

A table of item, requirement, status or source, priority, and how it is verified, plus exclusions, actors, data classes, jurisdictions, owners, and horizon. Every assumption gets an owner or a validation action.

## 3. Workload and capacity model

Average and peak request rates, read/write mix, fan-out, concurrency, payloads, storage and retention, queue arrival and service rates, locality, headroom, and cost drivers, with formulas, units, source, uncertainty, and decision sensitivity. Name the first likely bottleneck and its scale trigger. Detail: [requirements and capacity](requirements-and-capacity.md).

## 4. Domain, APIs, and data

- Domain boundaries, owners, invariants, source of truth
- API/event contracts, auth context, compatibility, quotas and error semantics
- Data model/access patterns, classification, retention/deletion, consistency and transaction boundaries
- Derived data, caches, queues, search/analytics, rebuild/reconciliation paths
- Schema evolution, backfill and migration assumptions

Detail: [data architecture](data-architecture.md), [API design](api-design.md).

## 5. Architecture diagrams

Only diagrams that answer a decision: context and deployment, container and component, sequence (critical path plus the main failure, retry, or compensation path), data model. Mark illustrative and vendor-specific elements, and imply no guarantee the design lacks. Follow [diagram style](diagram-style.md).

## 6. Critical flow contracts

Per critical flow: steps, caller deadline, authz check, data read and write, transaction, async handoff, idempotency key or dedupe, ordering and freshness, response to the user, observability, and failure recovery. Cover ambiguous timeout after a write and duplicate delivery.

## 7. Decisions and alternatives

A table of decision, option chosen, alternatives, evidence, costs and risks, and the revisit trigger, including the simplest viable option. Durable decisions become ADRs indexed in section 20; a row with no ADR behind it is marked "promote to ADR if <condition>".

## 8. Security, privacy, and abuse

Assets, actors, entry points, trust boundaries, data flows, and tenant boundaries, then prioritized threats with impact, likelihood basis, prevention, detection, response, owner, evidence, and residual risk. Cover authentication versus authorization, object and property checks, secrets, minimization, retention and deletion, audit, supply chain, and AI prompt or tool boundaries. Flag legal facts for authoritative review. Detail: [security and privacy](security-privacy.md).

## 9. Reliability and operational model

- SLIs/SLOs, user-facing alert conditions, error budget if useful
- Failure domains, dependencies, overload limits, degradation, failover, RTO/RPO
- Retries/timeouts/bulkheads/circuit breakers with semantics and budgets
- Backups and successful restore evidence; recovery runbooks
- Metrics/logs/traces with privacy/cardinality policy
- Deployment, rollout/rollback, on-call ownership, incident process
- Capacity, quotas, cost signals, retention, exit considerations

Detail: [reliability, performance, and production operations](reliability-operations.md).

## 10. Risk register

A table of risk, impact, likelihood with its confidence, mitigation and detection, recovery and owner, and the test or evidence behind it. Rank only where evidence supports it; state uncertainty rather than false precision.

## 11. Delivery and validation plan

Phased milestones with dependency, owner, acceptance evidence, rollout, rollback, and a stop and continue gate. Include contract, security, performance, recovery, restore, and migration tests. For a repository review, separate findings by severity and cite file paths and symbols. Do not change code unless requested. Rollout and rollback are section 13.

## 12. Open decisions

Per question: why it changes the design, who can answer, and the default assumption if no answer arrives.

## 13. Rollout and rollback plan

Delivery is the work order; rollout reaches users and rollback withdraws. The common failure is a change that deploys cleanly and is then undone badly.

- Stages and population, with a per-stage gate: a metric, a window, a threshold. "Healthy" is not a gate.
- Stop and continue gates both ways: condition, who may call it, the default if nobody does, the delay before the default fires.
- Blast radius: the flag, tenant allowlist, region pinning, or capacity partition that bounds who is affected when the change is wrong.
- Rollback safety: what it reverts (code, schema, new-path data, emitted events) and what it cannot (money moved, mail sent). A half-migrated schema means forward repair.
- Incompatibility list: every state that stops the old version serving, such as a new non-null column, an unparseable event field, a changed default or unit, a removed enum value, or a new mandatory request field. For each, the mechanism and its window.
- Mixed versions: which deployments coexist, the order, the supported range.

## 14. Operational readiness checklist

Status values, used identically everywhere: **VERIFIED** (tested, and the test is named), **CONFIGURED BUT UNPROVEN** (it exists, nothing has exercised it), **UNKNOWN** (nobody checked). An unknown is a finding, not a formality.

Items: on-call owner named for every new component and alert; dashboards live with production-shaped data; alert thresholds set with a stated rationale; runbook linked for every user-facing alert; rollback rehearsed end to end; restore drill performed with the measured RTO and RPO; capacity headroom known for peak, failover, and loss of one dependency; credential, certificate, and quota expiry monitored; on-call briefed on the new failure mode; cost anomaly detection and budget signal live. Per item: status, evidence or test, owner, and the action if not verified. Every row reading VERIFIED means the checklist was not performed. Detail: [launch readiness checklist](../templates/launch-readiness-checklist.md).

## 15. Cost model

Per-unit economics, not a copied monthly total. Vendor prices do not live here: take them from the named platform's pricing page, record the date checked, and model the effect of a change.

- Unit of account: one per request path (per call, per tenant, per GB stored, per million events), stated once.
- Formula, with units on every term: `monthly_cost = fixed_platform_cost + requests_per_month * cost_per_request + stored_gb * cost_per_gb_month + egress_gb * cost_per_gb_egress + write_ops * cost_per_write + engineering_hours * loaded_hour_cost`.
- Fixed versus variable: what is paid whether or not traffic arrives. The floor sets the smallest scale worth running; the slope sets the cost of growth.
- Drivers by sensitivity at expected load and at 3x load; per-tenant economics per month, per active user, smallest-tier floor, since pricing and packaging are design inputs.
- Run-rate shape: base, peak, and a failure scenario. Budget guardrail: a threshold, who is notified, the response.
- Cost of the rejected options, and the excluded costs named, so the number is not read as complete.

## 16. Migration plan

Required for Tier C and any Tier B that changes a system of record.

- Source of truth per field during and after; a field written by two systems with no owner diverges.
- Phases: expand, backfill, dual write, cutover, contract, each with entry and exit criteria and an owner.
- Dual write: the authoritative side, how divergence is detected, the comparison cadence, the tolerated difference, the kill switch. Without a comparison it is two systems disagreeing quietly.
- Backfill: batch, throttle, checkpoint, idempotency key, source rate limit, lock impact, mid-flight row change. A backfill that starves production is an incident.
- Cutover signal and the observation window, set before the cutover; rollback versus forward repair, decided in advance.
- Cleanup criteria, owner, and date before the old path, schema, code, and compatibility layer go; mixed versions and old client contracts; reconciliation tooling and how a human resolves it. Detail: [migration plan](../templates/migration-plan.md).

## 17. API contract artifact

One worked request, response, and error-catalogue example, not a list of field names, with the unit and currency of every numeric field, required versus optional and what an omitted field means, the default and maximum page size, the error codes a client can branch on, the server deadline, and the idempotency key scope, retention, and mismatch rule. Attach the machine-readable schema and the compatibility check. Detail: [API contract](../templates/api-contract.md).

    POST /v1/payments HTTP/1.1
    Idempotency-Key: 7f3c1a52-9d0e-4f6b-8a11-2c4d6e8f0a13
    { "order_id": "ord_8812", "amount": { "value": 4250, "currency": "USD" },
      "payment_method_id": "pm_5510" }

    HTTP/1.1 201 Created
    Location: /v1/payments/pay_9f21
    { "id": "pay_9f21", "status": "pending",
      "amount": { "value": 4250, "currency": "USD" } }

    HTTP/1.1 409 Conflict
    Content-Type: application/problem+json
    { "type": "https://errors.example.com/idempotency-key-reuse",
      "status": 409, "code": "idempotency_key_payload_mismatch",
      "detail": "The key was first used with a different request body.",
      "instance": "/v1/payments", "request_id": "req_1a77",
      "retryable": false }

## 18. Ownership table

| Component or data | Owning team | On-call | Escalation | Data owned and class |
|---|---|---|---|---|
| | | | | |

One row per deployable component and per dataset. A dataset has exactly one owning team; a table written by two teams is a finding, not a convention. Detail: [team topology](team-topology.md).

## 19. AI and agent boundary

Required for Tier C when an agent acts rather than only producing text for a human.

- Autonomy level: the highest action the agent may take with no human in the loop, and the conditions that raise or lower it. Name the levels, for example read-only, propose-and-approve, act-within-a-cap, act-autonomously. An agent that can act is not a chat feature.
- Tool inventory: per tool, what it reads, what it changes, who owns the resource, the trust boundary crossed, whether the effect is reversible, the blast radius of misuse, including tools reached indirectly through an API.
- Approval gates: which actions pause, what the approver sees, the default on timeout, how long an approval stays valid.
- Evaluation plan: task set, pass criteria, production shadow period, regression gate, who blocks a release. Offline benchmarks do not measure production behaviour.
- Injection and exfiltration posture: what is untrusted input, whether retrieved or user text can carry instructions, what the model may never reveal, the egress boundary, the logging policy. Failure behaviour, audit, and a stop mechanism complete it. Detail: [AI and agent system architecture](ai-systems.md).

## 20. ADR index

| ADR | Title | Status | Date | Decision summary | Link |
|---|---|---|---|---|---|
| 0001 | | Proposed/Accepted/Superseded/Deprecated/Rejected | | | |

Durable decisions only: a choice that constrains future work and would be expensive to reverse. Each ADR holds the context, the options, the decision, and the accepted consequences. A decision in section 7 with no ADR behind it will be re-litigated. Detail: [ADR template](../templates/adr.md).

## 21. Glossary

The domain nouns a reader outside the team needs, one line each: words that mean something specific here, the acronyms used in the diagrams, and internal system names.

## 22. Evidence appendix

Every external claim the brief depends on, mapped to a source that can be re-checked: author or publisher, date or version, platform, and scope. The [source guide](sources.md) holds the curated index; the appendix holds only what this brief used. The source is primary (specification, official documentation, first-party report) unless the claim is case-specific, in which case say so. Record the date or version checked, because platform limits and protocol versions change. State the scope: one vendor, one region, one product edition, one scale.

## Parallel specialty review

For a truly cross-domain design, the lead may delegate bounded reviews: requirements/capacity (workload, targets, bottlenecks), data/API (ownership, invariants, contracts, compatibility), reliability (failure domains, overload, recovery, operations), security/privacy (trust boundaries, abuse, tenancy, lifecycle), cost/platform (deployment, quotas, cost, portability, team burden).

Give reviewers the same assumptions and design snapshot. Request concise evidence-backed findings, not alternative full designs or file changes. The lead resolves disagreements, records unresolved questions, and remains accountable for the final recommendation. Use the available agent count proportionally.

## Reviewer audit trail

For each delegated reviewer record the scope it was given, what it found, and what happened to every finding. Each finding ends as **Accepted** (the design changed), **Rejected** (the finding was wrong or its premise was already excluded, with the reason), or **Deferred** (valid, but belonging to a later milestone, which is named). A finding with no disposition means the review is not finished. Record the findings the lead disagreed with as prominently as the accepted ones.
