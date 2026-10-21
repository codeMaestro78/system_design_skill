<!-- Use when a recurring operational failure needs a written, executable response with containment, recovery, and escalation. -->

# Runbook: <symptom or component>

Owner: <role accountable for this runbook>
Last tested: YYYY-MM-DD
Next review: YYYY-MM-DD
Applies to: <service, component, region, or failure mode>
Severity when triggered: <severity and the paging policy>
Escalation: <who is paged, and after how long>

## 1. Symptom

User-visible or operator-visible symptom, in the words a user would use.

| Symptom | Likely user impact | How it is detected | Alert or dashboard |
|---|---|---|---|
| | | | |

## 2. Diagnosis

Start from the symptom, not from a guess. Each step is a command, a query, or a link to a dashboard, with the reading that confirms or rules it out.

| Step | Command, query, or dashboard | Expected reading | If it matches | If it does not match |
|---|---|---|---|---|
| 1 | <exact command> | | | |
| 2 | | | | |

| Check | Query or dashboard | Healthy | Degraded | Notes |
|---|---|---|---|---|
| | | | | |

Timebox the diagnosis. If the cause is not identified within <duration>, contain first and diagnose after.

## 3. Containment

The action that stops the bleeding. It is safe, reversible where possible, and does not require the root cause.

| Option | Effect | Risk | Reversible | Authority required | Prefer this when |
|---|---|---|---|---|---|
| | <what it stops> | <what it might break> | Yes/No | <role> | |

Order of preference: shed or defer load, disable a feature flag, roll back the last change, isolate a component, then scale. Prefer the action with the smallest blast radius that is known to work.

## 4. Recovery

| Step | Action | Verification | Expected result | Time |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

State the order of recovery for multi-component dependencies, and what must be healthy before the next component is brought back.

## 5. Rollback

| Item | Detail |
|---|---|
| What is rolled back | <code, config, schema, traffic split> |
| Method | <exact command or mechanism> |
| Data implications | <what happens to writes made since the change> |
| Time to safe state | |
| Conditions under which rollback is not safe | <the point of no return> |

## 6. Escalation

| Elapsed time | Condition | Action | Contact | Channel |
|---|---|---|---|---|
| 0 min | | Page primary on-call | | |
| <N> min | | Escalate to secondary | | |
| <N> min | | Escalate to incident commander, open a bridge, start the incident report | | |

## 7. Communication

| Audience | Message | Channel | Cadence |
|---|---|---|---|
| Affected users | | | |
| Support | | | |
| Stakeholders | | | |

## 8. Verification of recovery

The runbook is not complete until recovery is proven.

| Check | Method | Pass condition | Owner | Date last run |
|---|---|---|---|---|
| Symptom cleared | | | | |
| Backlog drained | | | | |
| Data consistent | | | | |
| Capacity normal | | | | |
| Follow-up logged | <incident report or ticket> | | | |

## 9. Known issues and dead ends

| Attempted action | Result | Why it failed |
|---|---|---|

This section saves the next responder from repeating a dead end.

## Before you deliver

- Every step is executable: an exact command, a query, or a named dashboard. No "check the logs".
- No invented numbers. Every threshold and timeout carries units and a source, and the detection query matches the alert that fires it.
- Every action maps to a requirement, a constraint, or a named risk reduction, and every action states its risk and reversibility.
- Containment is listed before diagnosis-dependent repair, and the point of no return is named where rollback is unsafe.
- The runbook has a named owner, a last-tested date, and a next review date. An untested runbook is marked as such in its header.
- Restore and rollback are drills with an owner and a date, not intentions.
- The recovery verification section names the checks that prove the symptom is gone, not just that a process restarted.
