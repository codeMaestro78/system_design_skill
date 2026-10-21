# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-21

### Added

- Skill package in `system-design/`: `SKILL.md` as the entry point, topic guides in `system-design/references/`, agent interface metadata in `system-design/agents/openai.yaml`, and artwork in `system-design/assets/`.
- Behavior evaluation harness in `evals/`: scenario prompts and rubrics in `evals/cases.json`, a partially readable repository fixture in `evals/fixtures/`, and `evals/evaluate.py` to list cases, print prompts, build review templates, and score an assessment against explicit criteria and red flags.
- Package checker `scripts/check_skill.py`: frontmatter validation, local link resolution, heading checks, and reference routing checks.
- Sample output for the one-clinic booking scenario in `examples/small-clinic-sample.md`.
- Reproducible packaging with `scripts/package.py`, which writes a byte-identical archive for the same source tree and can verify that property with `--check`.
- Continuous integration in `.github/workflows/validate-skill.yml` and a tagged release workflow in `.github/workflows/release.yml`.

[Unreleased]: https://github.com/codeMaestro78/system_design_skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/codeMaestro78/system_design_skill/releases/tag/v1.0.0
