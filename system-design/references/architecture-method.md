# Architecture method and decision records

Use this for: framing a design, comparing architectural styles, and recording durable decisions as ADRs. This file is the canonical definition of the ADR format used across the reference set.

Sources: [AWS Well-Architected](sources.md#architecture-foundations), [Azure Architecture Center](sources.md#architecture-foundations), [C4 model](sources.md#architecture-foundations), [Microsoft cloud design patterns](sources.md#patterns).

## Architecture starts with context

Capture purpose, users, critical journeys, business outcomes, external dependencies, deployment environment, team topology, support model, constraints, and explicit exclusions. Record what is known from evidence separately from assumptions. Identify the design horizon and expected evolution. Architecture is the set of consequential decisions and constraints that shape system properties; it is not only a box diagram.

## Requirements and quality attributes

Functional requirements describe behavior and business invariants. Quality attribute scenarios make nonfunctional expectations testable:

> Given [stimulus and operating condition], when [response], the system should achieve [measurable response] within [boundary/time].

Examples: under a specified peak, 99% of interactive reads complete within a target; after a zone loss, critical writes resume within an RTO; a user can export and delete personal data within a specified period. These are examples only: elicit actual targets. Keep availability, durability, consistency, freshness, confidentiality, integrity, recoverability, maintainability, portability, accessibility, sustainability, and cost distinct.

For each important quality attribute, document workload/conditions, measure, target, scope, and verification method. Resolve conflicts explicitly (e.g., freshness vs cache hit rate; strong cross-region consistency vs latency; resilience vs cost). Track which targets are contractual SLAs, internal SLOs, or provisional requirements. Workload modeling and sizing live in [requirements and capacity](requirements-and-capacity.md).

## Domain and boundaries

Model users, workflows, nouns, verbs, invariants, and ownership before services. Use domain-driven design concepts as a way to discover boundaries, not as a requirement to adopt a framework. A bounded context should have a coherent model, owner, and change cadence. A service boundary is valuable when it provides meaningful ownership, independent change/scaling, security isolation, or failure containment; it costs network calls, operational overhead, duplicated data, and distributed consistency.

Prefer a modular monolith when one team and shared transaction boundaries dominate. Consider services when independent deployment, scale, or isolation has measurable value and the team can operate them. Define APIs/events and data ownership before extracting; see [data architecture](data-architecture.md) for ownership and transaction boundaries. Keep low coupling and high cohesion without creating tiny services.

## Architecture styles

Compare styles against workload and organization. This table is the canonical style list for the reference set.

| Style | Useful when | Main costs / risks |
|---|---|---|
| Modular monolith | One deployable is operationally efficient; modules can enforce ownership | Requires module boundaries and build/test discipline; shared failure/deploy unit |
| Layered / hexagonal | Clear separation of policy, domain, adapters, and infrastructure helps testing/change | Can become ceremony or pass-through layers |
| Microservices | Independent ownership, release, scaling, or isolation are real needs | Distributed calls, data duplication, tracing, deployment, and incident complexity |
| Event-driven | Producers and consumers need temporal decoupling, fan-out, or asynchronous work | Eventual consistency, schema evolution, replay, ordering, poison messages, and debugging |
| Serverless / managed services | Elasticity and lower infrastructure operations outweigh runtime/control constraints | Provider coupling, quotas, cold starts, local testing, observability, and cost variance |
| Batch / streaming data platform | Data volume, freshness, transformations, and analytical access justify distinct pipelines | Data quality, replay, lineage, backfills, storage and compute costs |
| Hybrid / edge / multi-region | Latency, sovereignty, availability, or connectivity requires multiple placement models | Replication, policy consistency, release coordination, and operations multiply |
| Peer-to-peer / decentralized | No single authority owns the state; participants must cooperate directly | Coordination, identity, consistency, abuse handling, and discoverability become protocol work |

Avoid naming a style without explaining its runtime, ownership, and data implications. Pattern-level choices inside a style are listed in the [pattern catalog](pattern-catalog.md).

## Decision process

1. State the decision and context.
2. List requirements and constraints it materially affects.
3. Compare viable options, including doing nothing or a simpler option.
4. Record decision, rationale, accepted consequences, rejected alternatives, confidence, owner, and revisit trigger.
5. Define a test, metric, or milestone that can falsify the assumption.

Prefer reversible decisions early; invest more analysis in expensive or irreversible choices.

## Decision records (canonical ADR format)

This is the single definition of an Architecture Decision Record for this skill. Other references may summarize the parts they need, but they defer to this schema rather than defining a different one.

An ADR contains:

- **Context**: the problem, the forces in play, the constraints, and the state of the system at decision time.
- **Decision**: what was decided, stated as an active choice rather than a discussion.
- **Alternatives**: the options considered and rejected, including the option of doing nothing, with the reason each was not chosen.
- **Consequences**: what becomes easier, harder, costlier, or newly risky, including consequences accepted rather than avoided.
- **Confidence**: how strong the evidence is, and what would change the decision if the assumption fails.
- **Owner**: the person or role accountable for the decision and for revisiting it.
- **Date and revisit trigger**: when it was decided and the event, measurement, or review that should reopen it.

Use ADRs for durable decisions. Revisit when workload, team, security posture, cost, or platform changes. Record operational consequences in [reliability, performance, and production operations](reliability-operations.md) and keep the ADR short enough to be read.

## Decomposition and diagrams

Use C4-like levels when a diagram is useful: system context, containers/deployable units, components only where needed, and code details only for implementation. Label responsibility, trust boundary, protocol, owner, sync/async behavior, and data store. A sequence diagram should show timeouts, retries, and response semantics when they matter. An ERD should show keys, constraints, ownership, and lifecycle, not just table names.

Keep diagrams aligned with prose; mark illustrative architecture as illustrative. Avoid implying network, redundancy, or transactional guarantees that the diagram does not establish.

## Trade-off evaluation

Use a decision table rather than a generic pros/cons list. Weight criteria only when the user or business has supplied priorities; otherwise explain qualitative ranking. Consider total cost of ownership: infrastructure and licenses, engineering time, on-call burden, migration, vendor exit, security assurance, and failure recovery. Distinguish initial build cost from steady-state operation. Prefer measurable hypotheses and prototypes for uncertain bottlenecks.
