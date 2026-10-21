# Sample: public-launch readiness for a clinic booking service (launch-readiness scenario)

> Sample output produced with the `system-design` skill for the `launch-readiness` eval case in `evals/cases.json`. Saved as an illustration of answer shape and reasoning, not as a claim of measured improvement. See `evals/README.md` for how to reproduce and score behavior cases.

**Prompt:** A clinic plans to launch its appointment booking service publicly next week. Unit and integration tests pass. Daily database backups are configured, but nobody has restored one or checked that restored bookings are usable. This release renames a database column used by the previous application version; the team says it can roll back by deploying the old image. Monitoring shows CPU and request count, but there is no alert for failed bookings or named incident responder. Load testing covered average traffic only. Based only on this evidence, should the team launch publicly? Separate verified facts from unproven claims, give the minimum checks and owners needed before a broad launch, and describe a safe rollout and stop conditions. Do not redesign the whole system.

---

## 1. Decision

**No — I would not sign off on the broad public launch next week, on this evidence.** The gaps that block it are not code quality; the code's tests pass. They are about whether the clinic can recover its bookings, get back to a working state after a bad release, and notice and own a broken booking journey. All three are unproven, and two of them (recovery, rollback) are beliefs rather than observations. A green test suite says nothing about either.

**What I would approve instead:** a limited, staged rollout next week — staff-only bookings first, then a capped cohort of patients — with published stop conditions and a pre-authorised containment action. That is a real launch, and it converts the unknown into a bounded risk instead of an unbounded one. **What must be true before the broad public launch** — three items, each closable in days, not weeks: (1) a completed restore drill proving that application-level bookings survive a restore, recording a measured recovery time against an RTO/RPO the clinic has agreed; (2) a rehearsed release path — forward repair, or an expand/contract change — so that "roll back" is an option the team has actually performed rather than believes in; (3) booking-journey alerting with a named responder on a rota. With those closed, the remaining items are ordinary launch hygiene. **Scope:** I am not redesigning the system, and I am not inventing targets. Nothing below introduces microservices, multi-region, or a particular vendor. Where a number appears it is either in the prompt, shown with its arithmetic and its assumption, or marked as a decision the clinic must make.

---

## 2. What the evidence actually shows

| VERIFIED (tested) | CONFIGURED BUT UNPROVEN | UNKNOWN |
| --- | --- | --- |
| Unit and integration tests pass (prompt). This proves the covered paths pass — not that a booking survives a restart, a restore, a release, or a peak. | Daily database backups are configured (prompt). A backup job can run green for months and still restore nothing usable; no restore has been performed. | How long a restore takes and how much booking data it would lose. No drill has produced a number, and the prompt states no RTO and no RPO. |
| Load testing covered average traffic (prompt). This characterises throughput at average load only; it says nothing about the booking-window peak, contention on availability, or behaviour when the database is slow or failing over. | The release process renames a database column (prompt). The change exists; nothing in the evidence shows it is compatible with the previous application version. | Whether the rename has already shipped, whether the old image still runs against the current schema, and whether any forward repair has been rehearsed. |
| CPU and request count are collected and graphed (prompt). These detect load and resource trends; they cannot detect a booking journey that fails while the service looks busy. | A rollback plan exists as a belief — "deploying the old image" (prompt). It is unproven against a renamed column, and an image rollback is not a data rollback. | Whether failed bookings are visible to anyone today, and whether a booking can succeed and then fail to persist. No alert covers either. |
| Nothing is verified about recovery. No restore has been performed (prompt), so there is no measured restore time, no verified data path, and no evidence that a restored database is usable by the running application. | Nothing is verified about rollback. The old image has not been run against the renamed schema, and the change is not shown to be backward-compatible. | The realistic peak booking rate and the clinic's appointment volume and daily distribution. Only average traffic was tested, so no peak can be derived from the evidence. |
| The load-test tooling exists and can be re-run (prompt), which is what makes a peak test cheap to do before the launch. | Backups are daily, so the worst-case data loss is bounded by the backup interval. That is a bound, not a target, and the clinic has not said whether it accepts it. | Who acts on a page, who decides to stop bookings, and how patients are told booking is unavailable. No responder role and no runbook appear in the evidence. |

---

## 3. The recovery proof, before any public launch

**What is missing is a restore, not a backup.** A successful backup job proves bytes were copied. It proves nothing about whether the restored database can be read by the current application, whether the schema in that backup matches the schema the application expects, or how long the restore takes. The rename makes this sharper, not softer: a restore is precisely the moment an older backup meets newer code. **The drill (about an hour, once, before the launch):**

1. Restore the most recent production backup into an **isolated** environment — separate host or account, no production credentials, and either anonymised production data or a synthetic dataset of the same shape and size.
2. **Record the measured recovery time:** wall clock from "restore started" to "the first booking is accepted by the running application" — not to "the database container is up".
3. **Verify application-level booking data, not file existence.** At minimum: (a) bookings in a known window have the expected row count and field values; (b) a booking can be created end-to-end through the running application against the restored database and then read back — the same journey a patient uses; (c) a slot already booked before the backup is still booked, i.e. the double-booking invariant still holds on restored data; (d) the schema version in the restored database is the one the running code expects — this is where the renamed column fails, and it fails late, in the middle of an incident; (e) no orphaned bookings whose patient or provider records are missing.
4. **Record the measured RTO and RPO.** The RPO is bounded by the daily backup interval — up to a day of new bookings could be lost — and the RTO is whatever step 2 measured. Both are measurements, not targets.
5. **Then have the clinic agree them as business requirements.** RTO (the longest outage the clinic will accept for booking) and RPO (the most booking data it will accept losing) are the clinic's decisions, expressed in patient impact: "one business day of new bookings lost" and "N hours to restore" are business statements. The drill supplies the measured numbers; the clinic supplies the acceptable numbers. This document does not invent either, and a drill that misses the agreed numbers is a failed launch gate rather than a failed drill. Repeat the drill on a schedule and after every schema change — a restore path exercised only before a launch is exercised rarely.

---

## 4. Change safety: the old image is not a rollback

**The alternative for this and every future schema change — expand/contract.** Why redeploying the old image is not safe after this rename: the rename is a change to the shape of the data, and redeploying a binary does not undo it. The old image's queries reference the old column name, so once the column is renamed the old code fails on every request that touches it — the "rollback" is a deployment that is known to be broken, applied at the moment the team is already in trouble. It is also a *partial* failure: if the new code wrote the new column while old reads look for the old one, reads and writes can fail independently, giving a partial outage with a misleading error surface. And because the schema change persists, rolling back the code does not roll back the data: the deployable unit (code + schema) is no longer backward-compatible and the previous known-good state has been destroyed. A rollback that cannot be performed is not a rollback; it is false reassurance on the day it is needed.

1. **Expand:** add the new column, nullable, with no behaviour change. The old code still works.
2. **Dual-write:** the new code writes both columns; reads still come from the old column.
3. **Backfill:** copy existing data in batches, with a checkpoint, a rate limit, and a verification count. Idempotent, so it can be re-run.
4. **Switch reads:** the new code reads the new column; the old column is still written, so the old image still runs.
5. **Contract:** drop the old column **in a later release**, only after the old image is no longer deployable and the rollback window has passed.

Under expand/contract the previous version stays a valid rollback target for the whole window, because its column still exists and is still maintained. The cost is one extra column and a period of dual writes — cheap insurance against exactly the situation in the prompt. If the rename has not shipped yet, this is available today and should be taken today. **If the rename has already shipped** (the evidence does not say, and establishing that is the first thing to do), the plan is **forward repair, not rollback**:
1. Freeze further schema changes to that table.
2. Decide the target state. Keeping the new column name is usually right — moving forward is nearly always cheaper than reconstructing a compatible past.
3. Re-establish a fallback: re-add the old column and dual-write both, if that can be done without a long table lock. That makes the old image deployable again and restores rollback as an option. If it cannot be done safely, drop the old image as a rollback target entirely and say so explicitly in the release record.
4. Rehearse the repair in an environment mirroring the production schema and data volume, and **time it**. The rehearsal duration becomes the new RTO for that scenario, and it replaces the rollback the team believed it had.
5. Write the compatibility state into the change record — "schema vN is not backward-compatible with image vN-1; forward-repair path is X, rehearsed on <date>" — so the next release does not rediscover this.

**Minimum before the launch:** establish which of the two states we are in, and have the repair path exercised at least once by someone who did not write the change. If the rename has not shipped, convert it to expand/contract before it ships; that is the cheapest available fix and it is still available.

---

## 5. Detection and ownership

**Journey-level detection.** CPU and request count cannot see a booking failure. The likely way this launch fails is not a traffic spike; it is a release where every booking write fails while the API keeps serving requests and the CPU looks normal. Request count can even rise — clients retrying — and look like success. The signal has to sit at the outcome of the booking, not at the entrance to it.

- `booking_attempt_total{result}` — every attempt, labelled `created`, `slot_conflict`, `validation_error`, `db_error`, `timeout`. A slot conflict is a normal user-facing outcome, not an error; alerting on it drowns the signal.
- `booking_created_total` — incremented **after** the transaction commits and the availability check confirms the slot, not at the HTTP entry point. This is the number the clinic cares about, and the one that exposes silent non-persistence.
- `booking_commit_latency` (p95) — the patient-visible latency of a booking.
- **A scheduled canary booking** — a real booking on a real test slot through the public journey, every few minutes, booking and then cancelling, alerting if it fails. This catches writes that fail silently or bookings that are not persisted, which no error-rate metric on the request path would show.

**Alert thresholds (starting values, to be recalibrated against one measured baseline week):** page the on-call when the canary booking fails twice consecutively; page when the booking success rate falls below 99% over 15 minutes with at least 20 attempts in that window; page when `booking_created_total` is zero for 15 minutes during opening hours — a silent write failure looks exactly like a quiet day; ticket when p95 commit latency exceeds the agreed target, once a target exists, or when the error rate by label rises above its baseline. The 20-attempt floor and the 15-minute window are starting values chosen so a single unlucky request does not page anyone; they are not a service level. Do not invent a target for the clinic — ask for one, record it, and alert against it. **Named ownership:** a single role owns the booking journey end to end — **Booking Service On-Call** (primary) with a named deputy, and the **Clinic Operations Lead** as the business decision-maker for patient impact, opening hours, and when to stop taking bookings. A rota, not a mailing list, and it is written on the runbook. A release nobody owns is how "no named incident responder" becomes an outage.

**Minimal recovery runbook (one page):**
1. **Symptom** — canary failing, or booking success rate below threshold.
2. **Confirm** — check the booking error label and the last release; compare the running image's expected schema version with the database's actual schema version. This is the check that catches the rename.
3. **Contain** — turn off public booking with the feature flag; staff keep booking patients by phone. One action, no meeting, pre-authorised to the on-call.
4. **Fix** — if the cause is the release, execute the rehearsed forward-repair plan; **do not redeploy the old image** unless the compatibility plan says it is valid. If the cause is data loss or corruption, restore into the isolated environment per the drill, verify the bookings, and re-point traffic.
5. **Communicate** — the on-call tells the Clinic Operations Lead within a stated interval; the clinic decides what patients are told; the next update time is stated up front.
6. **Learn** — add the failure to the runbook and re-run the relevant drill.

---

## 6. Capacity and rollout

**Peak, from a stated assumption.** The evidence contains no volume figures, so the peak must be an assumption, and it must be labelled as one. **Assumption A1 (replace with the clinic's real figures before rollout):** one clinic taking up to 200 bookings on a working day, concentrated in a 2-hour morning booking window. Then 200 bookings / 7200 s ≈ 0.028 bookings/s during that window, and at a 5x intra-window rush factor ≈ 0.14 bookings/s. That is a trivial load for one application instance and one database: **throughput is not what will break this launch.** The number that matters is therefore contention and failure behaviour: concurrent readers of the same availability window, contention on the booking constraint, and what happens to a booking when the database is slow, failing over, or mid-restore. So re-run the load test at the assumed peak — 5x the window average, all requests inside one booking window, with the same slot distribution — and in the same run inject database latency and a failover, recording the section 5 journey metrics rather than CPU. If the clinic's real volume is materially above A1, redo the arithmetic; the conclusion changes only if the peak is orders of magnitude beyond what one instance handles.

**Staged rollout, with observable gates:**
- **Stage 0 — internal, for at least 2 working days:** staff-only bookings, feature flag on, staff booking real patients. *Continue* if the canary booking passes every interval, the booking success rate holds at baseline, no page fires, and the restore drill is complete with a measured recovery time inside the agreed RTO. *Stop* on any failed canary, any duplicate booking, any unexplained zero in bookings created, or any open page.
- **Stage 1 — capped public cohort, for at least 2 clinic days:** public booking enabled for a named list of patients, with a hard cap on bookings per day that the clinic sets, so the blast radius of a defect is bounded and the number of affected patients is known. Same criteria as Stage 0, plus a stop if booking-related support contacts exceed the number agreed with the clinic in advance.
- **Stage 2 — general public booking:** only after Stage 1's observation window closes with every criterion met, and the forward-repair or expand/contract path has been exercised at least once by someone other than its author.
- **Stop criteria (any one, observable, no meeting required):** a failed canary booking; booking success rate below threshold for 15 minutes; bookings created dropping to zero during opening hours; any duplicate booking reported — one is enough, because the double-booking invariant is absolute; p95 commit latency above the agreed target; a fired page from the on-call; support contacts above the agreed cap. **Containment action:** flip the feature flag to disable public booking and route patients to the phone — the on-call can do this alone, at any hour, without seeking approval. Patients already booked are unaffected; new bookings stop.

**The honest summary:** Stages 0 and 1 are how the unknowns become bounded, and they are a legitimate launch next week. Stage 2 is the public launch the team asked about, and it is the thing I am not signing off on today.

---

## 7. What is explicitly not required

- **Microservices.** Nothing in the evidence shows a team boundary, a scaling boundary, or an independent deploy cadence. The failure modes here — recovery, compatibility, detection — are solved by a drill, a compatible schema change, and a metric.
- **Multi-region or active-active.** No requirement in the evidence asks for geographic failover, and a restore drill is a different thing from multi-region. The agreed RTO, once the clinic sets it, is what determines whether one region suffices.
- **Any particular vendor.** No specific database, queue, APM tool, or orchestrator is a demonstrated requirement. A managed database with point-in-time recovery is a reasonable default because it shrinks the unproven-restore risk, but the requirement is "a restore you have proven", not a product. Choose what the team can operate and restore at 3am.
- **A rewrite, an event-driven redesign, or a new booking system.** The problems visible here are operational, not architectural. **An availability or latency target stated by me:** the clinic has not given one, so I do not assert one — agree it as a launch gate and alert on the journey, not on a number taken from this document.

---

## 8. Trade-offs accepted

Holding the broad launch costs a week of public visibility and a small amount of engineering time for the drill, the compatibility change, and the alerting. That is cheap against a public launch that loses a day of bookings to an un-restorable backup, rolls back into a broken image, or books nothing while the dashboards stay green. Staging caps bookings, so some patients wait — a deliberate, bounded, visible cost. The compatibility work adds a column and a dual-write window. Forward repair accepts that the old image may be permanently unusable, which is uncomfortable but true, and better than discovering it during an incident.

*Evidence that would change this answer: a completed restore drill showing application-level bookings intact and recording a measured recovery time inside an RTO the clinic has agreed; a rehearsed forward repair, or an expand/contract migration, that restores a real rollback option; booking-journey alerting with a named responder on a rota; a peak-traffic test that passes on journey-level metrics within the agreed targets, plus one deliberately failed release to prove the flag and the stop criteria work. Conversely, if the rename has already shipped and no forward repair can be rehearsed before next week, the answer hardens: do not launch publicly at all, and make the compatibility repair the first milestone. And if the clinic cannot agree an RTO and an RPO, no further evidence can substitute for that decision — the launch is unbounded by definition.*
