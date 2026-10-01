# Architecture foundations

Use this for greenfield design, architectural reviews, and major feature boundaries. Sources: [AWS Well-Architected](sources.md#skills-format-and-architecture-foundations), [Azure Architecture Center](sources.md#skills-format-and-architecture-foundations), and [C4 model](sources.md#skills-format-and-architecture-foundations).

## Discover before drawing

Capture actors, critical journeys, data owners, external dependencies, failure impact, team ownership, and constraints. Separate business behavior from quality attributes. Prioritize must/should/could/out of scope; write measurable quality targets or mark them open. A design serves a workload and organization, not an abstract scale label.

For an existing system, make a component map from code paths and runtime/deployment evidence. Cite file paths and symbols. Mark behavior inferred from naming as a hypothesis until a call path, test, or operational artifact supports it.

## Boundaries and interfaces

Group behavior by domain ownership and change cadence. Define module/API boundaries around invariants and data ownership; avoid shared writes across independent owners. Specify request/response or event schemas, versioning, authentication, authorization, error behavior, pagination, and compatibility policy. Include accessibility and user impact for product-facing paths.

| Style | Fits | Costs and misuse |
| --- | --- | --- |
| Layered or modular monolith | Small to medium teams, shared transactions, evolving domains | Requires enforced module boundaries; a shared codebase can become tightly coupled. |
| Microservices | Distinct ownership and scaling needs with mature operations | Network failure, data consistency, deployment and observability overhead; splitting before boundaries stabilize can slow changes. |
| Event-driven | Loose time coupling, fan-out, durable asynchronous work | Ordering, replay, duplicate handling, schema evolution, and difficult tracing. |
| Serverless | Bursty/event workloads and managed operations | Runtime/platform limits, cold starts, dependency and cost variability. |
| Peer-to-peer | Decentralized ownership or offline cooperation | Coordination, identity, abuse and consistency are harder. |
| Hybrid | Different workloads with genuinely different needs | Extra interfaces and operational models; justify each boundary. |

## Decisions and evolution

Record consequential choices in a short architecture decision record: context, decision, alternatives, consequences, date, and revisit trigger. Plan an incremental migration with compatibility, data backfill, cutover, rollback, and owner. Review decisions when traffic, team structure, or measured reliability changes. A diagram should show a system boundary and responsibilities before deployment detail.

**Recommendation:** Begin with the simplest architecture that meets known constraints. Move a boundary into a separately deployed service only when independent scaling, ownership, release cadence, or isolation compensates for distributed costs.
