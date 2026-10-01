# System-design behavior evaluations

These cases test decisions the skill should improve. They do not enforce one architecture or guarantee correctness. Run the [package checks](../scripts/check_skill.py) in CI; run behavior cases with an agent that has the local skill loaded. The fixture is intentionally incomplete and must remain read-only during an evaluation.

## Run a case

1. `python evals/evaluate.py list` to choose a case.
2. Load `system-design/SKILL.md` through the target agent's normal skill mechanism. In a fresh conversation, submit only the output of `python evals/evaluate.py prompt CASE_ID`. Do not show the agent `cases.json`, this rubric, or earlier responses.
3. Save the agent's full answer to a file outside the repository, for example `/tmp/system-design-answer.md`. For `interview-coaching`, score only the first assistant reply.
4. Generate a review form: `python evals/evaluate.py template CASE_ID /tmp/system-design-answer.md > /tmp/system-design-review.json`.
5. Read the response and case expectations. For every criterion, assign **2** when clearly supported by the response, **1** when partial or ambiguous, or **0** when absent or contradicted. Record a short quotation or precise location and explanation in `evidence`. Mark each red flag `true` or `false`; explain triggered flags. A second reviewer is useful for disputed scores.
6. Run `python evals/evaluate.py score /tmp/system-design-review.json /tmp/system-design-answer.md`. The response hash prevents scoring a different revision accidentally.

A scenario passes only if every critical criterion scores 2, at least 80% of all points are earned, and no red flag triggers. This threshold is a local regression gate, not a claim of general system-design accuracy. Keep failed outputs and review notes outside the skill package or in a separately controlled evaluation archive; inspect privacy and licensing before sharing them.

For `cached-balance`, run two fresh conversations using `prompt cached-balance --route compact` and `prompt cached-balance --route detailed`. Generate each review template with the matching `--route`. Compare both answers and their critical scores: if they disagree on source of truth or freshness, inspect the two references and fix the conflicting guidance. The default `automatic` run separately tests whether the skill routes well on its own.

## Interpret results

Fix the smallest supported guidance gap. Check whether the failure came from activation, reference routing, missing evidence, conflicting advice, or agent behavior despite clear instructions. Add a case only when it captures a distinct consequential failure. Do not rewrite the skill to force one case's preferred technology into all designs. Rerun the changed case and a nearby case after an edit; periodically run the full set across the agents you support. A package-only CI check cannot execute or grade agent behavior, so report these two forms of validation separately.
