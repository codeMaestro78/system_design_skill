<!-- Use when a decision is expensive to reverse and outlives the current sprint. Promote from the design doc's decisions table. -->

# ADR-NNNN: <decision in one sentence>

Status: Proposed | Accepted | Superseded by ADR-NNNN
Date: YYYY-MM-DD
Deciders: <roles or names who agreed>
Owner: <role accountable for the decision and for revisiting it>
Reversibility: Reversible | Costly | Irreversible
Revisit trigger: <measurable condition that invalidates this decision, for example "peak sustained write rate exceeds 2,000/s for 7 consecutive days", "two or more teams need independent deploy cadence", "data residency requirement covers a new region">

## Promotion rule

Write an ADR when all three hold:

1. The decision is expensive to reverse: data model, consistency boundary, service split, public API shape, region or vendor commitment, retention or compliance policy.
2. At least two viable options existed at the time of the decision.
3. The decision outlives the current sprint.

Skip the ADR for reversible choices, naming, or libraries with no architectural effect. The default is inline: record the decision in the design doc's decisions table and mark it "promote to ADR if <condition>". Promote when the condition is met, and link the ADR back to the design doc.

## Context

<What forces, constraints, and drivers make this a decision rather than an implementation detail. State the forces with the status label Observed, Given, Assumed, Estimated, or Open. Include what was true at the time of the decision, since that is what makes a later revisit trigger meaningful.>

- Forces: <driver>
- Constraints: <constraint>
- Prior state: <what exists today that this decision replaces or constrains>
- Related material: [design doc](design-doc.md), [ADR-NNNN](adr.md), <issue or doc reference>

## Decision

<The decision itself, in the present tense and active voice. State what will be true after this decision is implemented, not what will be attempted. Include the mechanism by which it is enforced.>

We will <decision>. <Mechanism: the specific constraint, contract, or enforcement point that makes the decision real.>

## Alternatives considered

| Option | Summary | Why rejected | Cost of rejection |
|---|---|---|---|
| A: <option> | <what it means in practice> | <reason, tied to a force or constraint> | <what is given up, stated plainly> |
| B: <option> | | | |
| C: do nothing | <status quo> | | |

Include the simplest viable option. For each rejected option, name the specific force it fails, the cost of choosing it, and the condition under which it would become the right answer.

## Consequences

Accepted benefits:

- <benefit, and for whom>

Accepted costs and risks:

- <cost or risk, and the mitigation or the reason it is acceptable>

Follow-up:

| Action | Owner | Due |
|---|---|---|
| <action that must happen for this decision to hold> | <role> | YYYY-MM-DD |

## Verification

<How the decision will be confirmed or falsified. A metric, a test, or a milestone. If none exists, the decision is a belief, and say so.>

- Metric: <name and unit, and the threshold that counts as success or failure>
- Test or experiment: <what runs, in which environment, and what a pass looks like>
- Milestone: <date or delivery stage at which the evidence will exist>
- Falsified if: <the observation that would prove the decision wrong>

## Before you deliver

- Status matches reality. A decision that has not been agreed is Proposed, not Accepted. A superseding decision names the ADR that replaced it.
- No invented numbers. Every threshold in the revisit trigger and verification sections has units and a source, or it is marked as a proposed value awaiting evidence.
- Every component and consequence maps to a requirement, a constraint, or a named risk reduction.
- Every alternative in the table is one a reasonable engineer would have considered, and each rejection reason is tied to a force rather than to taste.
- Reversal and rollback are drills with an owner and a date, not intentions. A Costly or Irreversible decision states the forward-repair path, since rollback may be impossible.
- The alternatives and the rejected-option costs are recorded so a future reader can tell whether the revisit trigger has been crossed.
