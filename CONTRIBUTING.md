# Contributing

This repository holds an Agent Skills package, the scripts that check it, and the behavior evaluations that exercise it.

## Run the checks

Install the development dependencies and run the four checks that CI runs:

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_skill.py
python evals/evaluate.py validate
python -m unittest discover -s tests -v
python scripts/package.py --check
```

The first check validates the skill frontmatter, local links, and reference routing. The second validates the evaluation cases and the fixture. The third runs the unit tests. The fourth proves the distributed archive is reproducible; see the packaging notes below.

CI runs these four checks on Python 3.9 and on Python 3.12, the two ends of the supported range. All four are required: a failure in any one of them fails the build.

`scripts/package.py` builds the distributed archive. It is deterministic: two runs over the same tree produce byte-identical files, and the printed SHA-256 is the build fingerprint.

```bash
python scripts/package.py --check
python scripts/package.py --out dist
```

`--check` builds every variant twice into temporary files and fails when the two SHA-256 values differ. Run it before opening a pull request that touches `system-design/`.

Supported Python versions start at 3.9. Lint with `ruff check .` when ruff is installed, and measure coverage with `coverage run -m unittest discover -s tests` followed by `coverage report --fail-under=70`. Both are advisory in CI and neither is required to run the checks above.

## Change guidance

Fix the smallest supported guidance gap. When a scenario shows a wrong decision, change the smallest piece of guidance that explains it, then rerun that scenario and one nearby scenario. Do not rewrite the skill to force one case's preferred technology into every design, and do not add a new case for a failure the current guidance already covers.

Keep related compact and detailed references consistent. A change to one of them usually needs the matching change in the other.

## Add an evaluation case

1. Add a case to `evals/cases.json` with a unique `id`, a `mode`, a `prompt`, a list of `criteria` (each with an `id`, an `expect` string, a boolean `critical`, and an `anchors` object giving the text for scores `2`, `1`, and `0`), and a list of `red_flags` (each an object with an `id` and a `text`; a bare string is rejected). Use `{{FIXTURE_DIR}}` in the prompt when the case refers to the repository fixture.
2. Add a `reference_comparison` object with `compact` and `detailed` routes when the case compares the two reference styles. Both paths must exist under `system-design/`.
3. Add a fixture file only when the case needs repository evidence that the current fixture does not contain. Keep the fixture incomplete on purpose: unknown facts are part of what the cases test.
4. Run `python evals/evaluate.py validate` and confirm the case is accepted.
5. Run the case with the steps in [the evaluation guide](evals/README.md): print the prompt, collect an agent response, generate a review template, and score it. A case passes only when every critical criterion scores 2 and no red flag triggers. The total is reported as a diagnostic, not as a pass condition.

## Report results separately

Package checks and behavior results are different kinds of evidence and are reported separately.

- Package checks answer whether the skill can be parsed, whether its local links resolve, and whether the archive is reproducible. They say nothing about architecture quality.
- Behavior evaluations answer whether the guidance changed a decision on a specific case, as judged by a reviewer against explicit criteria. They cover the cases that were run, not every system.

Do not describe a behavior result as a general accuracy claim, and do not cite a package check as evidence of design quality. Neither kind of check guarantees a correct design for every system. Verify changing vendor capabilities, prices, security guidance, and regulations against current primary sources before relying on them.
