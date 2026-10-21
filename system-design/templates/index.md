<!-- Use when choosing which artifact to produce, or when a request implies a written document the skill has not shipped. -->

# Templates

Copy-and-fill skeletons for the artifacts this skill produces. Every template opens with a one-line comment stating when to use it, carries real structural headings and real column headers, and closes with a "Before you deliver" checklist.

Rules for use:

- Replace every `<placeholder>` and every `TBD`. Do not ship a template with a placeholder still in it.
- Delete sections that do not apply and say why in the scope line, or mark them "Out of scope: <reason>". A missing section with a stated reason is a decision; an unfilled section is not.
- Fill from observed evidence. Label anything else **Given**, **Assumed**, **Estimated**, or **Open**, and give every estimate a source or a validation owner.
- Link from these templates to [the design brief structure](../references/design-brief.md) for guidance, and to [the source guide](../references/sources.md) when a claim needs a current primary reference.

## Routing table

| Template | Use when | Trigger phrases in a request |
|---|---|---|
| [Design doc](design-doc.md) | A cross-team, high-impact, or production design needs one document that carries the decision, the model, the alternatives, and the plan. Section-for-section twin of the design brief. | "design doc", "design document", "architecture proposal", "write up the design", "technical design", "sign-off document", "produce a proposal" |
| [ADR](adr.md) | A decision is expensive to reverse, had at least two viable options, and outlives the current sprint. Records the decision and the trigger that would invalidate it. | "ADR", "architecture decision record", "record this decision", "decision log", "why did we choose", "capture the tradeoff" |
| [Threat model](threat-model.md) | A system handles sensitive data, spans trust boundaries, is multi-tenant, is exposed to agents or users, or is entering a regulated or externally reachable environment. | "threat model", "security review", "abuse cases", "attack surface", "STRIDE", "who could attack this", "security assessment" |
| [SLO and error budget](slo-and-error-budget.md) | Reliability needs to be stated as a number with a window, and release risk must connect to a budget rather than to uptime. | "SLO", "SLI", "error budget", "availability target", "reliability target", "alert thresholds", "how much downtime can we take" |
| [Capacity model](capacity-model.md) | Load is unknown, growing, or spiky enough that a sizing argument, a bottleneck, and a scale trigger are required before committing to a design. | "capacity plan", "sizing", "how much load can it take", "will it scale", "growth projection", "cost at scale", "we might get 10x traffic" |
| [Data model](data-model.md) | Entities, keys, invariants, ownership, and lifecycle must be fixed before storage or service boundaries are chosen. | "data model", "schema", "entity design", "table design", "invariants", "source of truth", "who owns this data" |
| [API contract](api-contract.md) | A public or cross-service interface must be specified precisely enough that two teams can implement against it without ambiguity, including errors, idempotency, and compatibility. | "API contract", "endpoint spec", "OpenAPI", "REST design", "idempotency", "how do we version this", "error response format", "rate limit" |
| [Migration plan](migration-plan.md) | A schema, contract, ownership, or storage change must land on a live system with old and new code coexisting. | "migration plan", "backfill", "schema change", "dual write", "cutover", "migrate from", "zero downtime migration", "decommission old path" |
| [Runbook](runbook.md) | A recurring operational failure needs a written, executable response with containment, recovery, and escalation. | "runbook", "on-call procedure", "playbook", "what do we do if", "how do we recover", "operational manual" |
| [Incident report](incident-report.md) | A production incident has been resolved and the record must capture symptom, timeline, hypotheses, contributing conditions, and corrective work without blame. | "incident report", "postmortem", "retro", "root cause analysis", "outage writeup", "incident review", "what went wrong" |
| [Launch readiness checklist](launch-readiness-checklist.md) | A consequential change is about to reach users and needs a go or no-go decision from evidence rather than confidence. | "launch checklist", "go/no-go", "production readiness", "release readiness", "are we ready to ship", "readiness review" |

## What these templates do not cover

- The design brief itself and the references. The [design brief](../references/design-brief.md) is the narrative structure; [design-doc.md](design-doc.md) is its fill-in twin.
- Evidence. [sources.md](../references/sources.md) points at primary documentation for protocol semantics, platform limits, security guidance, and law. A template cannot supply a citation.
- Diagrams. Templates reserve the place for context, container, sequence, and data-model diagrams. Mermaid renders inside markdown; keep prose and diagram consistent.
- Estimates. No template ships a number. Compute each one and write the formula, units, source, and uncertainty next to it.

## Before you deliver

- The chosen template matches the request. If two apply, deliver the one the reader will act on and link the other.
- Every `<placeholder>` and `TBD` is gone, or the artifact states explicitly what remains open and who owns it.
- Every number carries units and a source or a stated assumption; no invented traffic, latency, availability, growth, or cost figures.
- Every component in the artifact maps to a requirement, a constraint, or a named risk reduction.
- Restore and rollback are described as drills with an owner and a date, not as intentions.
