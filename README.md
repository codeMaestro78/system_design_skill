# System Design Agent Skill

An [Agent Skills](https://agentskills.io/specification) package for designing, reviewing, explaining, and practicing software system design. It helps an agent start with the actual requirements and evidence, compare reasonable architectures, and explain how the chosen design behaves in production.

The skill covers small applications as well as distributed systems. It includes guidance for APIs, data ownership, capacity, reliability, security and privacy, cloud platforms, AI agent systems, migrations, and incident and capacity analysis at a basic level. It also has an interactive interview mode that coaches before giving a complete solution.

## Sample: one-clinic booking (300 appointments/day)

> Sample output from the `small-clinic` scenario in [`evals/cases.json`](evals/cases.json). Full text in [`examples/small-clinic-sample.md`](examples/small-clinic-sample.md).

300 appointments a day, two developers, one location. The skill recommends a modular monolith on the existing relational database, not microservices or a queue:

- One web service + one database handles ~0.008 writes/s averaged over the ~10 h the clinic is open (0.0035/s over 24 h; <1/s at peak); ≈550k rows over 5 years, ~190 MB with indexes (~200 MB once idempotency keys are populated).
- Double bookings are prevented by a database constraint (`EXCLUDE USING gist` in PostgreSQL, which needs the `btree_gist` extension for a `uuid` provider column, or a unique slot write in MySQL), which works atomically even when no conflicting row exists yet, unlike read-then-insert or in-memory locks. Conflicts return `409 Conflict`.
- Retries use a stable `Idempotency-Key` scoped to the caller, so a timeout or double-click does not create a second booking, and one patient's key cannot return another patient's row.
- Backups with point-in-time recovery (`pg_basebackup` plus WAL archiving), a restore drill, and booking success/409/latency monitoring cover the booking journey.
- Queue, cache, or service split only on measured triggers or an ownership boundary (e.g., notification retries blocking requests, a sustained p95 breach, a second team).

## Operating modes

| Mode | Use it when | What you get |
| --- | --- | --- |
| Engineering design/review | A feature or service needs a design, or an existing design needs review | Requirements and evidence first, then components, data ownership, critical flows, failure and security model, trade-offs, and the evidence that would change the answer |
| Production readiness | A launch or a consequential change is close and recovery, rollback, and detection are unproven | A scoped go/hold decision - launch, limited launch, or hold - from observed evidence, the smallest verification for critical journeys, a staged rollout with stop conditions, rollback safety, and an explicit list of what is still unproven |
| Learning | You want to understand a topic, a pattern, or a decision | Progressive explanation with a concrete example, trade-offs, and failure cases, with terms defined as they appear |
| Interview | You want to practise system design | One useful question at a time; your attempt comes before any complete design is revealed |
| Incident | A system is degraded right now | The user-visible symptom, current evidence, safe containment, causal hypotheses, and measurable follow-up, without jumping to a redesign |
| Capacity | A limit is approaching, or a target volume is planned | The load model and its assumptions, projected load against capacity, headroom, the scaling trigger and who owns it, and cost at the target volume |

## How it decides

1. **Scope.** The skill first decides whether it applies at all: the full skill when the request changes or reviews architecture, a targeted slice when it is about one concern such as a queue, a cache, authorisation, or a data model, and not this skill for an isolated implementation task, a bug fix, a syntax question, or a rewrite of existing code.
2. **Mode.** The request selects one operating mode, and the mode sets the deliverable: a design recommendation, a launch decision, an explanation, an interview turn, or a containment plan. A design or review request uses engineering design/review, a launch question uses production readiness, "teach me" uses learning, "interview me" uses interview, "it is down" or "latency is up" uses incident, and "will this keep up" or "what will this cost at volume" uses capacity. When the signals conflict, incident wins over capacity, which wins over production readiness, interview, learning, and the default engineering design/review.
3. **Workflow.** Engineering design/review runs the thirteen-step workflow: frame the problem, discover constraints, specify requirements, model the domain and data, estimate capacity, compare designs, describe the architecture, trace critical flows, threat-model, design production operation, plan evolution, communicate decisions, verify before presenting. Production readiness runs steps 1, 2, 9, 10, and 13 and then answers with its own contract; it does not generate designs or compare alternatives. The other modes follow their output contract instead.
4. **Reference routing.** The mode and the topic decide which reference files are opened: start with the one first-pass guide for the topic, then add the canonical guide whenever the decision is irreversible, cross-team, regulated, or money-moving. Aim for three to five guides and the templates you will actually fill in. `SKILL.md` lists the mapping, and the package check fails if a reference file is not reachable from it.
5. **Reasoning checks.** The answer is verified against a fixed list before it is returned: every component maps to a requirement, the enforcement mechanism for a concurrent invariant is named, a timeout is not treated as proof that the operation failed, retries are bounded and idempotent, idempotency keys are scoped to the caller, restore and rollback are drills rather than configured controls, and facts, assumptions, estimates, recommendations, and open questions stay separated.

## When not to use this skill

- Routine coding work with no architectural decision: an isolated implementation task, a bug fix, a syntax question, or a rewrite of existing code.
- Refactoring that stays inside one module or one service and adds no new data ownership, contract, or failure mode.
- Vendor or API usage questions that need the product's current documentation rather than a design discussion.
- Performance work without a hypothesis: the skill needs the target percentile and the workload before it can size anything.
- Incident response where someone has to act now: contain the outage first, then use the skill for the follow-up analysis.
- Any request where you cannot share the constraints. The skill works from requirements and evidence; with none supplied it returns labelled assumptions rather than answers.

## Install

You need an agent that supports Agent Skills and Node.js 22.20 or newer for the [`skills` CLI](https://github.com/vercel-labs/skills/blob/main/README.md). The CLI commands below were verified on Node.js 24.15.0 on 2026-10-21.

From a local checkout, list the discovered skill before installing it:

```bash
npx skills add . --list
```

Install it for one agent in the current project (replace `codex` with `claude-code` or `opencode` as needed):

```bash
npx skills add . --skill system-design -a codex
```

To make it available across projects, add `-g`:

```bash
npx skills add . --skill system-design -a codex -g
```

Install directly from the [GitHub repository](https://github.com/codeMaestro78/system_design_skill):

```bash
npx skills add codeMaestro78/system_design_skill --skill system-design -a codex
```

The CLI can target multiple agents by repeating `-a`, for example `-a codex -a claude-code -a opencode`. For agents with their own skill installer, point it at the [`system-design/`](system-design/) directory, which contains the required [`SKILL.md`](system-design/SKILL.md). Follow that agent's installation instructions for project or user scope.

To check a project installation:

```bash
npx skills list
```

`npx skills update` applies to skills installed from the GitHub source. For an installation made from a local path, re-run the install command against the checkout:

```bash
npx skills add . --skill system-design -a codex
```

For an installation made with `-g`, use `npx skills list -g`; the default list shows project skills only.

## Use it

Ask your agent to use **system-design** and give it the problem, constraints, and desired output. In agents that support explicit skill invocation, you can use `$system-design`. The skill may also be selected automatically when a request calls for architecture work.

For example:

> Use system-design to review this repository's order flow. Inspect the code and deployment configuration first. Cite the evidence for each finding, identify unknowns, and recommend the smallest useful changes.

> Use system-design to design an appointment booking system for a small team. Start with a simple architecture, explain how it prevents double bookings, and show what would change if traffic grows.

> Use system-design to evaluate whether our notification service needs a queue. Compare a direct call with a queue, including retry behavior, duplicate delivery, operations, and cost.

> Use system-design in interview mode for a URL shortener. Ask me one useful question at a time and wait for my attempt before revealing a complete design.

Useful input includes expected users and workload, latency and availability needs, data sensitivity, budget, team size, deployment environment, and existing system constraints. You can leave unknowns open; the skill instructs the agent to label assumptions and ask only questions that could change a material decision.

The agent should produce a recommendation tied to requirements, key data and request flows, trade-offs, failure and recovery behavior, and unresolved decisions. The level of detail should match the task. A small design does not need a large distributed architecture or every section of a design brief.

## What's in this repository

| Path | Purpose |
| --- | --- |
| [`system-design/SKILL.md`](system-design/SKILL.md) | Entry point, workflow, reference routing, and reasoning checks |
| [`system-design/references/`](system-design/references/) | 30 topic guides: compact first-pass guides and detailed deep-dive guides |
| [`system-design/templates/`](system-design/templates/) | 11 copy-and-fill templates: design doc, ADR, threat model, SLO sheet, capacity model, data model, API contract, migration plan, runbook, incident report, launch readiness checklist |
| [`system-design/agents/openai.yaml`](system-design/agents/openai.yaml) | Agent interface metadata |
| [`system-design/assets/`](system-design/assets/) | Skill icons and logos |
| [`evals/`](evals/) | Scenario prompts and a human review rubric |
| [`evals/fixtures/`](evals/fixtures/) | Deliberately incomplete repository used by the evaluation cases |
| [`examples/small-clinic-sample.md`](examples/small-clinic-sample.md) | Sample answer for the one-clinic booking scenario |
| [`tests/`](tests/) | Unit tests for the package checks and the evaluation harness |
| [`scripts/check_skill.py`](scripts/check_skill.py) | Package validation: frontmatter, local links, reference reachability, agent interface icons |
| [`requirements-dev.txt`](requirements-dev.txt) | Python dependency needed to run the checks |
| [`.github/workflows/validate-skill.yml`](.github/workflows/validate-skill.yml) | Package checks run in GitHub Actions |
| [`system-design/templates/index.md`](system-design/templates/index.md) | Template routing table and the shared delivery checklist |
| [`system-design/assets/README.md`](system-design/assets/README.md) | Artwork sources, palette, and PNG regeneration steps |
| [`evals/README.md`](evals/README.md) | Evaluation guide: pass rule, anchors, evidence, manifest, adjudication |
| [`evals/cases.json`](evals/cases.json) | Scenario prompts, anchored criteria, and red flags |
| [`evals/evaluate.py`](evals/evaluate.py) | Prompt, template, score, baseline, archive, diff, and report commands |
| [`examples/payment-queue-sample.md`](examples/payment-queue-sample.md) | Sample answer for the payment-queue scenario |
| [`examples/repository-review-sample.md`](examples/repository-review-sample.md) | Sample answer for the partial-repository scenario |
| [`examples/launch-readiness-sample.md`](examples/launch-readiness-sample.md) | Sample answer for the launch-readiness scenario |
| [`scripts/package.py`](scripts/package.py) | Deterministic archive build and the `--check` reproducibility test |
| [`tests/`](tests/) | Unit tests for the package checks and the evaluation harness |
| [`.github/`](.github/) | CI workflows, CODEOWNERS, Dependabot, issue and pull-request templates |
| [`VERSION`](VERSION) | Released version, read by the release workflow |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history |
| [`NOTICE`](NOTICE) | Third-party material notice and artwork attribution |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to run the checks and add an evaluation case |
| [`SECURITY.md`](SECURITY.md) | Security scope and private reporting route |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Code of conduct |
| [`LICENSE`](LICENSE) | MIT license |

### Reference map

The compact references support a short first pass; the entry point calls them the first-pass column. The detailed references are the canonical guides and support consequential decisions. The entry point routes to the relevant guide for each task, and the package check fails when a reference file is not linked from `SKILL.md`.

| Topic | Compact reference | Detailed reference |
| --- | --- | --- |
| Architecture, boundaries, decision records | [`architecture-fundamentals.md`](system-design/references/architecture-fundamentals.md) | [`architecture-method.md`](system-design/references/architecture-method.md) |
| Requirements, workload, capacity | [`scalability-and-capacity.md`](system-design/references/scalability-and-capacity.md) | [`requirements-and-capacity.md`](system-design/references/requirements-and-capacity.md) |
| Data ownership, lifecycle, storage choice | [`data-and-storage.md`](system-design/references/data-and-storage.md) | [`data-architecture.md`](system-design/references/data-architecture.md) |
| Patterns and anti-patterns | [`architecture-patterns.md`](system-design/references/architecture-patterns.md) | [`pattern-catalog.md`](system-design/references/pattern-catalog.md) |
| Reliability, SLOs, operations | [`reliability-and-operations.md`](system-design/references/reliability-and-operations.md) | [`reliability-operations.md`](system-design/references/reliability-operations.md) |
| Security, privacy, tenancy | [`security-and-threat-modeling.md`](system-design/references/security-and-threat-modeling.md) | [`security-privacy.md`](system-design/references/security-privacy.md) |
| AI and agent systems | [`ai-agent-systems.md`](system-design/references/ai-agent-systems.md) | [`ai-systems.md`](system-design/references/ai-systems.md) |
| Teaching and interview practice | [`learning-and-interview.md`](system-design/references/learning-and-interview.md) | [`interview-learning.md`](system-design/references/interview-learning.md) |

Detailed-only references, reached directly from the entry point: `api-design.md`, `distributed-systems.md`, `cloud-platform.md`, `testing-evolution.md`, `design-brief.md`, and `sources.md`, plus the newer specialist guides `messaging-brokers.md`, `networking-and-edge.md`, `mobile-and-offline.md`, `model-serving.md`, `consistency-and-clocks.md`, `team-topology.md`, `diagram-style.md`, and `parallel-review.md`.

## Validate and improve the skill

Package checks run locally with Python 3 and the development dependency:

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_skill.py
python evals/evaluate.py validate
python -m unittest discover -s tests -v
```

`scripts/check_skill.py` validates that the `SKILL.md` frontmatter carries a valid `name` and `description`, resolves every local link including `#heading` anchors, requires every file in `references/` to be reachable directly from `SKILL.md`, and verifies that the agent interface icons declared in `agents/openai.yaml` exist. It also enforces size budgets on `SKILL.md` and on each reference file, requires every template to be reachable from `SKILL.md`, requires each compact guide to link its canonical companion with a `**Canonical guide:**` marker, and validates the shipped SVG and PNG assets.

Behavior evaluations test what an agent actually says. Start with:

```bash
python evals/evaluate.py list
python evals/evaluate.py prompt CASE_ID
```

Submit the generated prompt to an agent with the skill loaded, then save the agent's full response to a file before running `template` or `score`. The prompt command only prints the question; it does not run an agent or create a response file. Follow the scoring steps in the [evaluation guide](evals/README.md). The 13 cases cover simple architecture choices, incomplete repository evidence, messaging and delivery claims, production launch readiness, unknown-scale handling, AI-agent security, reference consistency, interview coaching, prompt injection in repository content, incident response, secrets in the tree, API contract evolution, and cost modelling. Reviewers score the response against explicit criteria and red flags; the script does not judge architecture quality on its own.

Incident and capacity analysis are supported through the incident and capacity modes. One behavior evaluation case covers incident response (`production-incident`); no case covers capacity analysis yet.

Passing package checks means the skill can be parsed and its local links resolve. Passing the scenario evaluations offers narrower evidence that the guidance helped on those cases. Neither guarantees a correct design for every system. Verify changing vendor capabilities, prices, security guidance, and regulations against current primary sources before relying on them.

## Contributing

When guidance changes, keep related compact and detailed references consistent. Fix a demonstrated decision error with the smallest useful edit, then rerun the relevant scenario and a nearby case. Add a new scenario when it captures a distinct, consequential failure. See the [evaluation guide](evals/README.md) for the review format and pass criteria.

## License

MIT. See [LICENSE](LICENSE). You may reuse and modify the skill under those terms.
