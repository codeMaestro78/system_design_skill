# System-design behavior evaluations

These cases test decisions the skill should improve. They do not enforce one architecture or guarantee correctness. Run the [package checks](../scripts/check_skill.py) in CI; run behavior cases with an agent that has the local skill loaded. The fixture is intentionally incomplete and must remain read-only during an evaluation.

`python evals/evaluate.py validate` checks the case definitions and the fixture tree. The fixture must contain exactly these files, and nothing else:

```
.env  .github/workflows/ci.yml  .gitignore  Dockerfile  README.md  docker-compose.yml
docs/ARCHITECTURE.md  migrations/001_init.sql  openapi.yaml  package.json
src/orders.js  test/orders.test.js
```

A file that is missing is reported as `Partial repository fixture is missing <path>` and a file that is not in that list is reported as `Partial repository fixture has an unexpected file: <path>`. The fixture is shared by every case, so a change to it changes what the reviewer can see; keep it in step with the cases instead of quietly adding files.

Passing this gate is a **local regression gate**, not a claim of general system-design accuracy. The package checks cannot grade behavior: they verify metadata, links, and structure, while these cases verify what an agent actually does with the skill loaded. Report the two forms of validation separately.

## Run a case

1. `python evals/evaluate.py list` to choose a case.
2. Load `system-design/SKILL.md` through the target agent's normal skill mechanism. In a fresh conversation, submit only the output of `python evals/evaluate.py prompt CASE_ID`. Do not show the agent `cases.json`, this rubric, or earlier responses. The command prints the prompt text itself, with no trailing newline, so the bytes you submit are the bytes the prompt digest covers.
3. Save the agent's full answer to a file outside the repository, for example `/tmp/system-design-answer.md`. You can run `cat > /tmp/system-design-answer.md`, paste the answer, and press Ctrl+D. Check it exists with `test -s /tmp/system-design-answer.md`. The `prompt` command does not create this file. For `interview-coaching`, score only the first assistant reply.
4. Generate a review form: `python evals/evaluate.py template CASE_ID /tmp/system-design-answer.md > /tmp/system-design-review.json`. Add `--route compact` or `--route detailed` when the run uses a reference comparison route. The form is frozen against the exact skill revision, prompt, route, and response bytes you are about to review.
5. Read the response and the case expectations, then fill in the form using the rubric below.
6. Run `python evals/evaluate.py score /tmp/system-design-review.json /tmp/system-design-answer.md`. The digests prevent scoring a different revision, prompt, route, or answer accidentally.

## Pass rule

A scenario passes only when **every critical criterion scores 2** and **no red flag triggers**. The total is reported as a diagnostic (`total/maximum`), not as a pass condition: the old 80% ratio never bound anything on cases where every criterion was critical, and on other cases the criticality rule already enforces the important part. So a run whose total falls below 80% still passes when every critical criterion scored 2 and no flag triggered, and a case with two critical criteria still fails on one missing critical behaviour.

## Score anchors

Every criterion in `cases.json` carries its own anchors for 2, 1, and 0. Use the anchors for that criterion, not a general impression.

- **2 — satisfies the expectation as written, explicitly.** The response states the expectation and names the mechanism or reasoning that delivers it. A correct conclusion without the mechanism is a 1.
- **1 — topic present but incomplete.** The response touches the topic but is generic, is unconnected to this case's constraints, or asserts the outcome without naming the mechanism or reasoning that produces it.
- **0 — absent, contradicted, or answered with a materially different claim.** The response does not address the criterion, or it states something that conflicts with the expectation.

A criterion the response never addresses cannot score 2 by implication. Silence is 0.

## Evidence

Every criterion needs `evidence`: quote at least one sentence from the response, or cite a heading or line where the answer appears. Your own opinion about how the architecture *should* work is not evidence — evidence is text the agent actually wrote. If the response is truncated, cut off mid-answer, or is only a clarifying question, score every unaddressed criterion 0 and record why in `reviewer_notes`.

## Order of work

Score all criteria first, then evaluate the red flags. A triggered flag is a claim about a specific false statement; reading one early biases the criterion scores toward it.

## Red flags

Each red flag in `cases.json` has an `id` and the false claim to detect. Three rules matter:

- **Every flag needs evidence, even when it is not triggered.** Record where you looked. A flag left without evidence is a channel a reviewer can neutralise for free, so the scoring refuses it: `red flag <id>: record where you looked, even if not triggered`.
- **The flag id must match the case.** Flags are bound by id, not by position, so reordering, renaming, or swapping flags is rejected (`red flag id mismatch`).
- **The flag text must match the case.** The `text` in the form is the claim to detect, and the scoring compares it with the case definition: rewriting it is rejected with `red flag <id>: text does not match the case definition`. Leading and trailing whitespace is ignored. A reviewer cannot replace the claim with a softer one and still pass.

A triggered flag fails the review regardless of the criterion scores.

## Run manifest

A review is only reproducible if it names what it was scored against. The `run_manifest` in the template must be filled in:

| field | meaning |
| --- | --- |
| `skill_sha256` | digest of the whole `system-design/` tree the answer was produced with |
| `prompt_sha256` | digest of the exact prompt text sent to the agent |
| `model` | the model or agent that produced the answer |
| `reviewer` | who scored it |
| `date_utc` | date of the run, `YYYY-MM-DD` |

`prompt_sha256` is the SHA-256 of the prompt text with the machine-specific fixture directory folded back to `{{FIXTURE_DIR}}`, so the same prompt has the same digest on every machine. The `prompt` command prints exactly that text, so the bytes you submit are the bytes the digest covers, apart from the fixture path substitution.

`python evals/evaluate.py digest` prints the current skill digest. If `skill_sha256` does not match the skill in the working tree, the score is refused with `assessment was scored against a different version of the skill`: the answer was produced against different guidance, so it cannot be compared with today's. `model`, `reviewer`, and `date_utc` must all be non-empty (`run_manifest: model/reviewer/date_utc are required`); without them nobody can repeat or attribute the run. Each missing field is reported separately, so one empty field does not hide the next.

The response hash covers the route, the prompt, and the response bytes together, so an answer scored under the wrong route or against a different prompt is detected.

## Two reviewers

When two reviewers differ by more than one point on any criterion, both must cite evidence, and a senior reviewer adjudicates. Record all three numbers — both original scores and the adjudicated score — in `reviewer_notes`, together with the sentence that decided it. Adjudication is not a negotiation between the two scores: the adjudicator picks the score the evidence supports.

## History and baselines

Append one row per scored run to `evals/results/<date>-<case>-<route>.json`:

```
python evals/evaluate.py baseline /tmp/system-design-review.json /tmp/system-design-answer.md
```

The stored file keeps the manifest, the assessment, and a copy of the response, so a later run can be diffed against it. The response is stored base64 encoded, so a response that is not valid UTF-8 round-trips byte for byte and `report` can re-verify its hash later. The date, case id, and route come from the assessment, so each one is reduced to a single safe path component before the file name is built, and the file is refused if it would land outside `evals/results/`.

`baseline` exits nonzero when the review did not pass, so it can gate a job like the other commands. Pass `--allow-fail` to record a failing run and still exit 0; the stored verdict is unchanged either way.

To compare two runs of the same case:

```
python evals/evaluate.py diff evals/results/2026-10-21-payment-queue-automatic.json \
                         evals/results/2026-11-04-payment-queue-automatic.json
```

`diff` reports the movement in total/maximum and per criterion, and exits nonzero when the new run is a regression. It says which kind of regression it found: `REGRESSION: the new run scores lower than the old run` for a lower total, and `REGRESSION: the new run does not pass where the old run passed` for a run that stopped passing without losing points, for example because a red flag now triggers. `diff` refuses to compare two different cases (`Cannot diff two different cases`) and exits nonzero: the criteria of two cases are not comparable. **Baseline the first run** of a case, and treat a drop in total/maximum as a regression to investigate, not as noise.

To keep a full copy of one run (prompt, response, assessment, manifest) in a directory:

```
python evals/evaluate.py archive /tmp/system-design-review.json /tmp/system-design-answer.md
```

`archive` exits nonzero when the review did not pass, and `--allow-fail` records the run and exits 0 instead. It refuses a route the case does not define and a `--out` path that exists as a file, with a message rather than a traceback.

To summarise many scored assessments in one table, and to fail a CI job when any of them failed:

```
python evals/evaluate.py report evals/results
```

The report table lists case, route, total/max, pass or fail, and the triggered flags, and exits nonzero when any run failed. A run is re-scored against the skill in the working tree only when that is the revision it was scored against. When the skill has changed since, the report uses the verdict the run was given and notes `N assessment(s) were scored against a different skill revision`, because re-scoring it would report the skill edit rather than the run. A run that did not pass still fails the gate, whenever it was scored. A file that cannot be read as an assessment — truncated, unparsable, or holding something else — is named in a warning and fails the gate too: a truncated baseline must never pass silently.

Keep failed outputs and review notes outside the skill package or in the controlled evaluation archive; inspect privacy and licensing before sharing them.

## Reference comparison routes

For `cached-balance`, run two fresh conversations using `prompt cached-balance --route compact` and `prompt cached-balance --route detailed`. Generate each review template with the matching `--route`. Compare both answers and their critical scores: if they disagree on source of truth or freshness, inspect the two references and fix the conflicting guidance. The default `automatic` run separately tests whether the skill routes well on its own. Other cases may define comparison routes as well, so check `reference_comparison` in `cases.json` before assuming a case has only one.

`launch-readiness` tests whether an agent can make a proportionate public-launch decision when CI passes but recovery, rollback, and incident response are unproven. Score the decision against the supplied evidence and the clinic's risks, not against a universal checklist. A limited rehearsal or internal rollout can be appropriate if it has a safe scope and stop conditions; calling the broad launch ready without closing critical gaps is not.

## Interpret results

Fix the smallest supported guidance gap. Check whether the failure came from activation, reference routing, missing evidence, conflicting advice, or agent behavior despite clear instructions. Add a case only when it captures a distinct consequential failure. Do not rewrite the skill to force one case's preferred technology into all designs. Rerun the changed case and a nearby case after an edit; periodically run the full set across the agents you support. A package-only CI check cannot execute or grade agent behavior, so report these two forms of validation separately.
