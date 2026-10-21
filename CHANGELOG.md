# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-21

Published by pushing the `v1.0.0` tag; the release workflow builds the archive and attaches it to the GitHub release.

### Added

- Skill package in `system-design/`: `SKILL.md` as the entry point, topic guides in `system-design/references/`, copy-and-fill artifacts in `system-design/templates/`, agent interface metadata in `system-design/agents/openai.yaml`, and artwork in `system-design/assets/`.
- Behavior evaluation harness in `evals/`: scenario prompts and rubrics in `evals/cases.json`, a partially readable repository fixture in `evals/fixtures/`, and `evals/evaluate.py` to list cases, print prompts, build review templates, score an assessment against explicit criteria and red flags, and record, compare, and report runs.
- Package checker `scripts/check_skill.py`: frontmatter validation, local link and heading resolution, reference routing, template reachability, size budgets, agent interface schema, and SVG and PNG asset validation.
- Sample output for the one-clinic booking, payment-queue, partial-repository, and launch-readiness scenarios in `examples/`.
- Reproducible packaging with `scripts/package.py`, which writes a byte-identical archive for the same source tree and can verify that property with `--check`.
- Continuous integration in `.github/workflows/validate-skill.yml` and a tagged release workflow in `.github/workflows/release.yml`.
- Release metadata in `VERSION` and `CHANGELOG.md`, a third-party material notice in `NOTICE`, and the contribution, security, and conduct policies.

### Changed

- Evaluation cases now carry per-criterion anchors for scores 2, 1, and 0, and each red flag carries an id and a text. Reviews are bound to a skill digest, a prompt digest, a route, a model, a reviewer, and a date, so a result can no longer be reproduced against a different version of the skill.
- The entry point gained an operating-mode table, a scope ladder, an ask-or-assume contract, per-mode output contracts, an untrusted-content policy, and a verify-before-presenting step.
- The eight compact reference guides are now short first-pass summaries that link a canonical companion, and the detailed guides are the single source of truth.

### Removed

- The third-party mark formerly in `system-design/assets/icon.svg`, replaced with original artwork derived from this repository's own logo. See `NOTICE`.

### Fixed

- Package checks no longer crash on a non-UTF-8 file, a non-mapping agent interface, or an empty link target, and heading anchors now match GitHub's slug rules.
- The one-clinic sample installs the `btree_gist` extension its exclusion constraint needs, scopes the idempotency key to the caller so one patient's key cannot return another patient's booking, corrects the MySQL affected-rows semantics and the point-in-time recovery pairing, and restates the storage and write-rate figures.
- A first pull request no longer fails on the dependency review step, and a tagged release can no longer be published against an existing tag.

[Unreleased]: https://github.com/codeMaestro78/system_design_skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/codeMaestro78/system_design_skill/releases/tag/v1.0.0
