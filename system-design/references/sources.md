# Research source guide

**Checked:** 2026-10-21. This index favors primary sources and specifications. Recheck changing pages, service capabilities, limits, framework behavior, security versions, and law before relying on them. Company case studies are context-specific, not universal design proofs.

**Next review:** 2027-01-21, or immediately when a cited standard, protocol, or provider page changes.

## Skills format and architecture foundations

Design sources are listed under [Architecture foundations](#architecture-foundations). The skill-format entries are listed under [Packaging metadata](#packaging-metadata-skill-package-format).

### Architecture foundations

- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html — operational excellence, security, reliability, performance, cost, sustainability; AWS-oriented; checked 2026-10-21.
- Google Cloud Well-Architected Framework: https://docs.cloud.google.com/architecture/framework — security, reliability, performance, cost, operations, sustainability; GCP-oriented; checked 2026-10-21.
- Microsoft Azure Architecture Center: https://learn.microsoft.com/en-us/azure/architecture/ — styles, patterns, reference architectures, decision guides; checked 2026-10-21.
- Azure cloud design patterns: https://learn.microsoft.com/en-us/azure/architecture/patterns/ — pattern problem/considerations catalog; technology-agnostic claims still need workload context; checked 2026-10-21.
- Martin Fowler, evolutionary architecture foreword: https://martinfowler.com/articles/evo-arch-forward.html — architecture change and feedback loops; authored commentary; checked 2026-10-21.
- Simon Brown, C4 model: https://c4model.com/ — levels of software architecture diagrams; checked 2026-10-21.

## SRE, reliability, operations

- Google SRE books and workbook: https://sre.google/books/ — SLOs, capacity, incidents, production operation; checked 2026-10-21.
- Google SRE non-abstract large-system design: https://sre.google/workbook/non-abstract-design/ — capacity planning, component isolation, graceful degradation; checked 2026-10-21.
- Google SRE cascading failures: https://sre.google/sre-book/addressing-cascading-failures/ — overload propagation and mitigations; checked 2026-10-21.
- Google SRE launch checklist: https://sre.google/sre-book/launch-checklist/ — launch and operational readiness; checked 2026-10-21.
- Amazon Builders' Library: https://aws.amazon.com/builders-library/ — first-party articles on distributed systems and operations; AWS context; checked 2026-10-21.
- Timeouts/retries/backoff/jitter: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ — transient failures and retry amplification; checked 2026-10-21.
- Idempotent APIs: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-apis/ — safe replay for mutations; checked 2026-10-21.
- AWS recovery objectives: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_objective_defined_recovery.html — RTO/RPO concepts; AWS-specific guidance; checked 2026-10-21.
- AWS queue backlog: https://aws.amazon.com/builders-library/avoiding-insurmountable-queue-backlogs/ — backlog recovery; checked 2026-10-21.
- OpenTelemetry observability primer: https://opentelemetry.io/docs/concepts/observability-primer/ — telemetry, SLIs/SLOs, tracing concepts; checked 2026-10-21.
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/ — traces, metrics, logs, baggage; checked 2026-10-21.
- AWS Well-Architected Reliability Pillar: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html — recovery and fault isolation; AWS-oriented; checked 2026-10-21.
- NIST SP 800-61 Rev. 3 (April 2025): https://csrc.nist.gov/pubs/sp/800/61/r3/final — incident response and recovery; checked 2026-10-21.

## Distributed systems and messaging

- Gilbert and Lynch, Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services: https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf — formal CAP model, not a general database-selection rule; checked 2026-10-21.
- Confluent, Kafka delivery semantics: https://docs.confluent.io/kafka/design/delivery-semantics.html — scoped message-delivery guarantees; product-specific; checked 2026-10-21.
- AWS, SQS standard queues: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html — duplicate and ordering behavior; product-specific; checked 2026-10-21.
- MIT, Little's formula: https://web.mit.edu/urban_or_book/www/book/chapter4/4.4.html — relationship among stable arrival rate, time in system, and average population; checked 2026-10-21.

## Patterns

- Microsoft Azure Architecture Center, cloud design patterns: https://learn.microsoft.com/en-us/azure/architecture/patterns/ — pattern definitions and trade-offs; vendor guidance; checked 2026-10-21.
- Microsoft, transactional outbox: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos — atomic local write and asynchronous publication; product example; checked 2026-10-21.
- AWS, saga pattern: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html — local transactions and compensation; vendor guidance; checked 2026-10-21.
- AWS, fault isolation: https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_fault_isolation_use_bulkhead.html — bulkheads and cells; vendor guidance; checked 2026-10-21.

## Team topology and organisation

- Team Topologies, key concepts: https://teamtopologies.com/key-concepts — team types, interaction modes, cognitive load, and evolving an architecture with the organisation; practitioner framework, not a standard; checked 2026-10-21.
- Google Cloud, architecture and organisation: https://docs.cloud.google.com/architecture/framework — operating model as a design input; vendor-oriented; checked 2026-10-21.

## API and protocol design

- RFC 9110 HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html — method/status/cache semantics; Internet Standard; checked 2026-10-21.
- RFC 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457.html — standardized error representation; checked 2026-10-21.
- OpenAPI Specification: https://spec.openapis.org/oas/ — language-agnostic HTTP interface description; check current released version; checked 2026-10-21.
- gRPC concepts: https://grpc.io/docs/what-is-grpc/introduction/ — RPC and protocol model; checked 2026-10-21.
- GraphQL specification: https://spec.graphql.org/ — schema and execution model; check current edition; checked 2026-10-21.
- Google API Improvement Proposals: https://google.aip.dev/ — resource design, compatibility, pagination, request IDs; Google conventions, not universal standard; checked 2026-10-21.
- OAuth 2.0 Security Best Current Practice RFC 9700: https://www.rfc-editor.org/rfc/rfc9700.html — current OAuth security guidance; checked 2026-10-21.
- OWASP API Security Top 10 (2023 edition): https://owasp.org/API-Security/editions/2023/en/0x11-t10/ — awareness taxonomy, not exhaustive assurance; checked 2026-10-21.
- Microsoft API design: https://learn.microsoft.com/en-us/azure/architecture/microservices/design/api-design — API boundaries, versioning, idempotency; Azure architecture guidance; checked 2026-10-21.
- Pact consumer-driven contract testing: https://docs.pact.io/getting_started/how_pact_works — contract testing workflow, complements other tests; checked 2026-10-21.

## Data, cloud, container, and operations sources

- PostgreSQL 18 transaction isolation: https://www.postgresql.org/docs/current/transaction-iso.html — example DB isolation semantics; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 range constraints: https://www.postgresql.org/docs/current/rangetypes.html — exclusion constraints for non-overlapping ranges; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 `btree_gist` extension: https://www.postgresql.org/docs/current/btree-gist.html — GiST operator classes with B-tree behavior for scalar columns, letting an exclusion constraint mix equality and range operators; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 `CREATE EXTENSION`: https://www.postgresql.org/docs/current/sql-createextension.html — installing a contributed extension such as `btree_gist`; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 replication: https://www.postgresql.org/docs/current/warm-standby.html — example replication behavior; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 partitioning: https://www.postgresql.org/docs/current/ddl-partitioning.html — example partition implementation; PostgreSQL-specific; checked 2026-10-21.
- PostgreSQL 18 indexes: https://www.postgresql.org/docs/current/indexes.html — index behavior and costs; PostgreSQL-specific; checked 2026-10-21.
- MySQL 8.4, affected-rows semantics: https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html — affected-rows values for insert, update, and no-op writes, and the `CLIENT_FOUND_ROWS` flag; MySQL-specific; checked 2026-10-21.
- AWS, DynamoDB read consistency: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html — scoped read guarantees; product-specific; checked 2026-10-21.
- Docker build best practices: https://docs.docker.com/build/building/best-practices/ — build context, images, layer/build guidance; checked 2026-10-21.
- Docker Compose: https://docs.docker.com/compose/ — multi-container application definition; does not by itself establish production HA; checked 2026-10-21.
- CNCF Cloud Native Landscape: https://landscape.cncf.io/ — ecosystem map, not an architecture recommendation; checked 2026-10-21.
- CNCF Cloud Native Reference Architecture: https://architecture.cncf.io/ — cloud-native architecture material; checked 2026-10-21.

## Security and privacy

- OWASP Threat Modeling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html — repeatable threat modeling; checked 2026-10-21.
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/ — testable application security requirements; verify current version/level; checked 2026-10-21.
- OWASP authorization guidance: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html — authorization design/test guidance; checked 2026-10-21.
- OWASP secrets management: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html — secrets lifecycle; checked 2026-10-21.
- OWASP Multi Tenant Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html — application-level tenant isolation; checked 2026-10-21.
- NIST Cybersecurity Framework 2.0: https://csrc.nist.gov/pubs/cswp/29/the-nist-cybersecurity-framework-csf-20/final — risk outcomes, not a legal certification; checked 2026-10-21.
- NIST Privacy Framework 1.0: https://csrc.nist.gov/pubs/cswp/10/nist-privacy-framework-version-10/final — voluntary privacy-risk framework; checked 2026-10-21.
- NIST SP 800-63-4: https://csrc.nist.gov/pubs/sp/800/63/4/final — digital identity guidance; federal-system context; checked 2026-10-21.
- NIST SP 800-218 SSDF: https://csrc.nist.gov/pubs/sp/800/218/final — secure software development practices; checked 2026-10-21.
- NIST SP 800-88 Rev. 2: https://csrc.nist.gov/pubs/sp/800/88/r2/final — media sanitization; not a blanket data-deletion guarantee; checked 2026-10-21.
- AWS SaaS tenant isolation: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/tenant-isolation.html — provider-specific tenancy guidance; checked 2026-10-21.
- Google Cloud security pillar: https://docs.cloud.google.com/architecture/framework/security — provider-specific security/privacy guidance; checked 2026-10-21.
- Azure multitenant models: https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models — Azure-oriented isolation choices; checked 2026-10-21.

## AI and agent systems

- OWASP GenAI Security Project, prompt injection (2025 edition): https://genai.owasp.org/llmrisk/llm01-prompt-injection/ — untrusted content and instruction boundaries; checked 2026-10-21.
- OWASP GenAI Security Project, excessive agency (2025 edition): https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ — excessive tool authority and human oversight; checked 2026-10-21.
- OpenAI, guardrails and human review: https://developers.openai.com/api/docs/guides/agents/guardrails-approvals — vendor-specific approval mechanisms; checked 2026-10-21.
- OpenAI, agent evaluations: https://developers.openai.com/api/docs/guides/agent-evals — vendor-specific evaluation mechanisms; checked 2026-10-21.
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework — voluntary AI risk framework; checked 2026-10-21.

## First-party engineering case studies

These illustrate lessons and constraints; never copy their scale, topology, or internal products blindly. Optional reading: cite a case only when a specific lesson carries the argument.

- AWS static stability: https://aws.amazon.com/builders-library/static-stability-using-availability-zones/ — serving/control-plane resilience; checked 2026-10-21.
- Meta TAO: https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/ — graph workload and caching lessons; checked 2026-10-21.
- Meta link imbalance: https://engineering.fb.com/2014/11/14/production-engineering/solving-the-mystery-of-link-imbalance-a-metastable-failure-state-at-scale/ — coupled component behavior and metastability; checked 2026-10-21.
- Netflix fault tolerance: https://netflixtechblog.com/fault-tolerance-in-a-high-volume-distributed-system-91ab4faae74a — isolation, fallbacks, circuit breakers; older case study; checked 2026-10-21.
- Netflix chaos engineering: https://medium.com/netflix-techblog/chaos-engineering-upgraded-878d341f15fa — controlled resilience experiments; older case study; checked 2026-10-21.
- Stripe API idempotency: https://stripe.com/blog/idempotency — first-party API behavior and retries; checked 2026-10-21.
- Microsoft transient fault handling: https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults — retry and dependency-failure guidance; checked 2026-10-21.

## Interpreting evidence

Prioritize standards/specifications for protocol semantics; official docs for the named platform; first-party blogs for a specific company's case; and carefully selected independent research where primary sources are absent. State author, date/version, platform, scope, and whether a statement is fact, recommendation, or case-specific observation. Do not treat a framework's pillar list, Top 10, or pattern catalog as an exhaustive checklist. Do not reproduce source text at length.

## Packaging metadata (skill package format)

These entries describe the skill package format itself, not design evidence, and no design reference cites them.

- Agent Skills specification: https://agentskills.io/specification — portable skill structure and frontmatter; checked 2026-10-21.
- Vercel `skills` CLI: https://github.com/vercel-labs/skills — installing and targeting agent skills; verify current agent names/flags; checked 2026-10-21.
