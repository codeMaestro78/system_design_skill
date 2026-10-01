# System Design Agent Skill

An [Agent Skills](https://agentskills.io/specification) package for designing, reviewing, explaining, and practicing software system design. It helps an agent start with the actual requirements and evidence, compare reasonable architectures, and explain how the chosen design behaves in production.

The skill covers small applications as well as distributed systems. It includes guidance for APIs, data ownership, capacity, reliability, security and privacy, cloud platforms, AI agent systems, migrations, and incident analysis. It also has an interactive interview mode that coaches before giving a complete solution.

## Install

You need an agent that supports Agent Skills and a current Node.js installation for the [`skills` CLI](https://github.com/vercel-labs/skills/blob/main/README.md). The CLI commands below were checked with Node.js 24.15.0.

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

To check an installation or update it later:

```bash
npx skills list
npx skills update system-design
```

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
| [`system-design/references/`](system-design/references/) | Detailed and compact topic guides, read as needed |
| [`system-design/agents/openai.yaml`](system-design/agents/openai.yaml) | Agent interface metadata |
| [`evals/`](evals/) | Scenario prompts and a human review rubric |
| [`scripts/check_skill.py`](scripts/check_skill.py) | Frontmatter and local link checks |
| [`.github/workflows/validate-skill.yml`](.github/workflows/validate-skill.yml) | Package checks run in GitHub Actions |

The compact references support a short first pass. The detailed references support consequential decisions. The original reference set is retained; the entry point routes to the relevant guide for each task.

## Validate and improve the skill

Package checks run locally with Python 3 and the development dependency:

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_skill.py
python evals/evaluate.py validate
python -m unittest discover -s tests -v
```

Behavior evaluations test what an agent actually says. Start with:

```bash
python evals/evaluate.py list
python evals/evaluate.py prompt CASE_ID
```

Submit the generated prompt to an agent with the skill loaded, save its full response, and follow the scoring steps in the [evaluation guide](evals/README.md). The cases include simple architecture choices, incomplete repository evidence, messaging and delivery claims, and interview coaching. Reviewers score the response against explicit criteria and red flags; the script does not judge architecture quality on its own.

Passing package checks means the skill can be parsed and its local links resolve. Passing the scenario evaluations offers narrower evidence that the guidance helped on those cases. Neither guarantees a correct design for every system. Verify changing vendor capabilities, prices, security guidance, and regulations against current primary sources before relying on them.

## Contributing

When guidance changes, keep related compact and detailed references consistent. Fix a demonstrated decision error with the smallest useful edit, then rerun the relevant scenario and a nearby case. Add a new scenario when it captures a distinct, consequential failure. See the [evaluation guide](evals/README.md) for the review format and pass criteria.
