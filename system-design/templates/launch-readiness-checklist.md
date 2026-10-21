<!-- Use when a consequential change is about to reach users and needs a go or no-go decision from evidence rather than confidence. -->

# Launch readiness: <change or release>

Change: <what is launching, and the scope of the blast radius>
Target date: YYYY-MM-DD
Owner: <role accountable for the launch decision>
Date of review: YYYY-MM-DD
Decision: GO | NO-GO | GO WITH CONDITIONS
Decision makers: <roles>
Evidence standard: a claim is VERIFIED only if a named test, drill, or query ran and its result is recorded here. Configuration, documentation, dashboards, and green pipelines are CONFIGURED, not VERIFIED.

## 1. Evidence states

| State | Meaning | May it block the launch? |
|---|---|---|
| VERIFIED | Tested or exercised; result recorded below | No |
| CONFIGURED BUT UNPROVEN | Set up correctly as far as anyone knows, but never exercised: a backup that has never been restored, an alert that has never fired, a failover that has never run | Yes, unless the risk is explicitly accepted in section 6 |
| UNKNOWN | Not assessed; no evidence either way | Yes, unless the risk is explicitly accepted in section 6 |

No item may be marked VERIFIED on the basis of configuration, intent, documentation, or a passing build.

## 2. Checklist

Each row states the evidence, not the intention. "Backups configured" is CONFIGURED BUT UNPROVEN until a restore has completed.

### 2.1 Correctness and contract

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 1.1 | <requirement or user journey is covered by a test> | | | | | |
| 1.2 | <API or event contract is backward compatible with the oldest supported client> | | | | | |
| 1.3 | <authorization rules hold for object, property, and cross-tenant paths> | | | | | |
| 1.4 | <data invariants hold under concurrency> | | | | | |

### 2.2 Data and migration

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 2.1 | <migration is idempotent and resumable> | | | | | |
| 2.2 | <backfill completed and reconciliation shows no divergence> | | | | | |
| 2.3 | <old path is retired or scheduled with a condition and a date> | | | | | |
| 2.4 | <deletion propagates to every copy> | | | | | |

### 2.3 Reliability and recovery

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 3.1 | <backup exists for every data class> | | | | | |
| 3.2 | <a restore drill completed and the service came back, not just the files> | | | | | |
| 3.3 | <rollback to the previous version is tested> | | | | | |
| 3.4 | <failover or degraded mode was exercised, including the data loss it causes> | | | | | |
| 3.5 | <runbooks exist for the top failure modes> | | | | | |
| 3.6 | <RTO and RPO are stated per data class> | | | | | |

### 2.4 Observability and detection

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 4.1 | <every user-facing symptom has an alert> | | | | | |
| 4.2 | <the alert fires in a test and reaches the on-call> | | | | | |
| 4.3 | <dashboards cover the critical journey> | | | | | |
| 4.4 | <logs, metrics, and traces carry correlation context> | | | | | |
| 4.5 | <version skew is visible> | | | | | |

### 2.5 Security and privacy

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 5.1 | <dependency and base image scan reviewed> | | | | | |
| 5.2 | <secrets are not in source, images, logs, or client bundles> | | | | | |
| 5.3 | <authorization is enforced in the owning service, not only at the gateway> | | | | | |
| 5.4 | <tenant isolation is tested on the new path> | | | | | |
| 5.5 | <data classification, retention, and residency are confirmed for the new data> | | | | | |

### 2.6 Capacity and cost

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 6.1 | <capacity model exists and the first bottleneck is named> | | | | | |
| 6.2 | <load test at expected peak passed, with abort conditions defined> | | | | | |
| 6.3 | <quotas and rate limits are set for every external dependency> | | | | | |
| 6.4 | <cost delta is known and a budget alert exists> | | | | | |
| 6.5 | <on-call capacity exists for the launch window> | | | | | |

### 2.7 Process and ownership

| # | Item | State | Evidence | Owner | Smallest verification that closes the gap | Blocking? |
|---|---|---|---|---|---|---|
| 7.1 | <on-call rotation covers the launch window> | | | | | |
| 7.2 | <escalation path and incident commander are named> | | | | | |
| 7.3 | <support and customer communication are prepared> | | | | | |
| 7.4 | <feature flags have an owner and an expiry> | | | | | |
| 7.5 | <rollback owner and decision authority are named> | | | | | |

## 3. Staged rollout

| Stage | Traffic or scope | Duration | Health criteria | Stop condition | Rollback action | Owner |
|---|---|---|---|---|---|---|
| 1 | <internal or 1%> | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | 100% | | | | | |

Stop conditions are written before the rollout starts, not during the incident. Use at least one of: error rate over baseline, latency over threshold, a specific alert firing, a customer report, or any new data inconsistency.

## 4. Stop conditions

| Condition | Threshold | Window | Source of the signal | Action on trip | Who may call it |
|---|---|---|---|---|---|
| | | | | | |

A stop condition without a threshold, a window, and a named caller is not a stop condition.

## 5. Known gaps accepted at launch

| Gap | Why acceptable | Blast radius if it occurs | Detection | Mitigation | Accepting role | Expiry |
|---|---|---|---|---|---|---|
| | | | | | | |

An empty table is only credible if every checklist row is VERIFIED.

## 6. Decision

Decision: GO | NO-GO | GO WITH CONDITIONS
Rationale: <what evidence decided it, and which items remain open>
Conditions: <each condition, its owner, and its due date>
Open blockers: <items marked blocking that are not closed>

| Role | Name | Date | Position |
|---|---|---|---|
| | | | |

## Before you deliver

- Every row carries a state of VERIFIED, CONFIGURED BUT UNPROVEN, or UNKNOWN. No third category, and no VERIFIED without recorded evidence.
- No invented numbers. Every threshold, duration, and metric carries units and a source, and each is tied to a measurement that actually ran.
- Every component and every checklist item maps to a requirement, a constraint, or a named risk reduction, and items that do not apply are deleted rather than marked pass.
- The smallest verification that would close each gap is concrete and executable, for example "restore the last production snapshot into a scratch environment and boot the service against it", not "test the backup".
- The staged rollout and the stop conditions are written before launch, each with a threshold, a window, and a named caller.
- Accepted gaps name the accepting role, the blast radius, and an expiry.
- Restore and rollback are drills with an owner and a date, not intentions. An unexercised backup is CONFIGURED BUT UNPROVEN, and that is stated plainly.
