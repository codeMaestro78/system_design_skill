# Architecture foundations

Use this for: a fast first pass on a greenfield design, an architectural review, or a major feature boundary.

Sources: [AWS Well-Architected](sources.md#architecture-foundations), [Azure Architecture Center](sources.md#architecture-foundations), [C4 model](sources.md#architecture-foundations).

**Canonical guide:** [Architecture method and decision records](architecture-method.md). That file is the source of truth for style selection and the ADR format; this page is only a first pass.

## Decision rules

- Discover before drawing: actors, critical journeys, data owners, external dependencies, failure impact, team ownership, constraints. Separate known fact from assumption. Write a measurable target or mark it open.
- Group behavior by domain ownership and change cadence. One owner per dataset. No shared writes across owners without a stated reason.
- Name a style only when a requirement forces it. Default to a modular monolith; move a boundary into a service only when independent scaling, ownership, release cadence, or isolation pays for the distributed cost.
- Record consequential choices with context, decision, alternatives, consequences, confidence, owner, and revisit trigger. Use the ADR schema in [architecture method](architecture-method.md); do not improvise a second one.
- For an existing system, build the component map from code paths and runtime evidence, cite file paths and symbols, and mark naming-based inferences as hypotheses until a call path, test, or operational artifact supports them.
- Show the system boundary and responsibilities before deployment detail. Keep the diagram consistent with the prose.

## Where to go next

- Workload sizing and targets: [requirements and capacity](requirements-and-capacity.md).
- Persistence, ownership, and invariants: [data architecture](data-architecture.md).
- Pattern choice and its costs: [pattern catalog](pattern-catalog.md).
- Objectives, failure behavior, and operations: [reliability and operations](reliability-operations.md).
- Trust boundaries, tenancy, and privacy: [security and privacy](security-privacy.md).
