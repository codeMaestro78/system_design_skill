# Team topology as a design constraint

Use this for: deciding service boundaries, assigning ownership and on-call, and sizing a platform capability. The architecture method that this file supports is in [architecture method and decision records](architecture-method.md). Sources: [AWS Well-Architected Framework](sources.md#skills-format-and-architecture-foundations), [Google SRE books](sources.md#sre-reliability-operations), [C4 model](sources.md#skills-format-and-architecture-foundations), [Team Topologies key concepts](sources.md#team-topology-and-organisation).

## Team types that carry the architecture

The four team types from Team Topologies map onto architecture roles, and a design that ignores them produces a structure nobody can operate.

| Team type | Exists to | Typical interaction | Fails when |
| --- | --- | --- | --- |
| Stream-aligned | own a customer-facing or business stream end to end | collaboration with other streams | the stream is a layer, such as only a frontend team or only a backend team |
| Platform | provide a self-service internal product, such as deployment, observability, and identity | X-as-a-Service for product teams | it becomes a ticket queue, or teams bypass it because the road is slower than the alternative |
| Enabling | help teams adopt a practice or capability, then step back | facilitating | it becomes a permanent shadow owner of another team's code |
| Complicated | own a genuinely hard domain, such as a numerical engine, a contract model, or a compliance interpretation | collaboration | the domain is not actually hard, or the charter is vague and the team becomes a dumping ground |

## Cognitive load is a hard limit

A team can only hold so many things. The limit shows up as on-call pages for systems nobody understands, long onboarding, reviews that become bottlenecks, and changes to one component breaking an unrelated one. Measure it: services owned, distinct runtimes, domains covered, pages per rotation, dependency fan-out, and the time to onboard a new engineer. When the load is exceeded, the options are to split the team, to merge services back together, to move a capability to the platform, or to narrow the scope. A design that assumes a team can absorb another service without changing anything else is a design that will fail on its worst day.

## Conway's law, used deliberately

Communication structure produces architecture. The practical move is inverse Conway: change the team structure deliberately to produce the architecture you want, by placing a team on the platform so it builds what it needs, by splitting a team along a business stream before splitting the code, and by moving people when a boundary turns out to be wrong. A service with three owning teams is a signal that the boundary or the ownership is wrong, and it should be treated as a design defect rather than a staffing fact.

## Every deployable has one owning team

Each deployable, datastore, topic, dashboard, runbook, alert route, and pipeline needs exactly one owning team, recorded in a service catalog and enforced in code review through ownership files. Orphaned assets are the most common cause of an unowned incident, and a service nobody can fix at night is an outage waiting for a schedule. On-call ownership is separate from code ownership but must exist for every production component, with a staffed primary rotation, a defined escalation path, and a handover that transfers runbooks, dashboards, and open risks along with the code. When a team is restructured, assets transfer explicitly; they are never left behind.

```yaml
service: svc_orders
owner_team: orders-core
on_call_rotation: orders-primary
alert_route: orders-primary
repo: git.example.com/orders/core
runbook: runbooks/svc_orders.md
deploy_target: orders-production
data_owned:
  - store_orders
contracts:
  - api/orders-v1
dependencies:
  - svc_payments
escalation: platform-oncall
```

## What a service split actually costs

| Dimension | Module in one deployable | Separate service |
| --- | --- | --- |
| Deployment | one pipeline, one artifact, one rollback | separate pipeline, artifact, environment, and rollback |
| On-call | one rotation, one runbook set | a rotation per service, including the one nobody wants |
| Debugging | one process, one stack trace, one log stream | distributed traces, correlation ids, and reasoning across network hops |
| Version skew | not applicable inside one artifact | two services deployed independently can run incompatible contract versions for a window |
| Data | a shared transaction in one database | duplicated data, a saga, or a distributed transaction to preserve a join |
| Latency | a function call | a network call, plus retries, timeouts, and a possible partial failure |
| Security | one trust boundary to reason about | a new boundary, a new authorization surface, and a network policy |
| Change | any change can touch any module | a change that crosses the boundary becomes a coordinated release |
| Cost | shared runtime and connections | duplicated runtime, memory, connections, and a per-service overhead |

The costs are permanent. Budget them against the benefit, which is usually independent deployment, independent scaling, failure isolation, or a security boundary, and require evidence for at least one of them.

## Choosing between a modular monolith and services

Use the team shape, not the traffic. If one team owns the domain end to end, a modular monolith is the better answer: shared transactions, one deployment, one on-call rotation, and one debugging story. If two or more teams own adjacent domains that change on different cadences, hold different data, or need different scaling, and the domain boundary is understood, then a split is justified. Traffic volume alone is not a reason: a high-traffic module with one owner is still a module, and a low-traffic domain with a separate team and a regulatory boundary may be a service.

## Where a module becomes a service

| Signal | Keep it a module | Extract a service |
| --- | --- | --- |
| Change cadence | changes together | changes independently and often |
| Data | joined in one transaction | owned by a different domain, and the join can be eventual |
| Scaling | one profile | a clearly different profile, such as a slow, memory-bound job next to a latency-sensitive API |
| Isolation | no requirement | containment, compliance, or tenant boundary is required |
| Team | one team | a different team can own it |
| Runtime | one language and one toolchain | a different runtime has a demonstrated benefit |
| Failure | shared fate is acceptable | a failure of one must not affect the other |

Extract in stages: enforce module boundaries in one codebase first, give the module its own data, add a contract with consumer-driven tests, then deploy it separately. Extracting code before the boundary is understood moves the coupling into the network, where it is harder to see and harder to change. See [testing and evolution](testing-evolution.md) for the migration mechanics and [distributed systems](distributed-systems.md) for the failure cost of the call.

## What the platform team provides

A platform team is responsible for the paved road: templates and golden paths for building and deploying, artifact supply chain and provenance, workload identity and secrets, observability defaults with logs, metrics, and traces wired to the service catalog, progressive delivery and rollback, environment parity, cost visibility, and runtime patching. Product teams deploy to production without filing a ticket, because a ticket queue makes the platform a support function and pushes teams back to their own bespoke pipelines.

Measure adoption of the paved road and publish it. If teams bypass it, fix the road rather than the teams, and record the reason. The platform owns its own reliability objectives and its own on-call, and a platform outage is a fleet-wide outage, so its blast-radius controls matter more than any single product's.

## Working with the architecture method

The method in [architecture method and decision records](architecture-method.md) prefers a modular monolith when one team and shared transaction boundaries dominate, and this file supplies the test for that judgement: does the team shape support the boundary. Record the owning team in the decision record for any proposed service, alongside the independent-deployment, scaling, or isolation benefit that pays for the split.
