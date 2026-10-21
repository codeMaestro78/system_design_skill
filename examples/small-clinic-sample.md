# Sample: one-clinic booking system (small-clinic scenario)

> Sample output produced with the `system-design` skill for the `small-clinic` eval case in `evals/cases.json`. Saved as an illustration of answer shape and reasoning, not as a claim of measured improvement. See `evals/README.md` for how to reproduce and score behavior cases.

**Prompt:** Design appointment booking for one clinic with two developers, one location, about 300 appointments per day, and an existing relational database. Receptionists and patients can book or cancel. Avoid double booking. The team can operate one web service and database. Recommend an initial architecture and explain when you would change it.

---

## 1. Facts, assumptions, unknowns

**Facts (from prompt):** one location, ~300 appointments/day, 2 developers, can operate 1 web service + 1 DB, must prevent double booking, book/cancel by receptionists and patients.

**Assumptions (reversible, would confirm):** existing DB is PostgreSQL (adapt below if MySQL); appointments are provider-scoped, fixed-duration slots (e.g., 15–30 min) with possible variable follow-ups; clinic open ~10 h/day; patients book own appointments only; no multi-region or insurance-billing scope in v1.

**Unknowns that would change material decisions:** exact RDBMS version, auth system, reminder/notification needs, no-show/cancellation policy, retention/regulatory jurisdiction for health data. I proceed without inventing traffic or SLO targets; every workload number below is either arithmetic derived from the stated 300/day or an assumption labelled as such.

## 2. Requirements

**Must:** book/cancel without overlapping bookings for the same provider; receptionist can manage any patient, patient only own; durable record; minimal ops.

**Should:** prevent double-click duplicates, show availability quickly, audit who changed what.

**Could:** waitlist, reminders, reporting.

**Out of scope v1:** multi-clinic, online payments, analytics pipeline, active-active HA.

Workload shape, not just average: 300/day over 10 h = 30/h avg. Write rate is 0.0035 writes/s over 24 h (300/86,400) and 0.008 writes/s averaged over the ~10 h the clinic is open (300/36,000). A 10x peak factor (assumed: morning rush plus reminder sends) still lands under 1 write/s; read volume of 5–10x writes is also an assumption, not a measurement. Storage: 300 rows/day × 365 × 5 years ≈ 550k rows, ~190 MB with indexes while `idempotency_key` is null and ~240 MB with the idempotency keys populated (heap 104 MB plus indexes 136 MB, of which 70 MB is the GiST exclusion index), still trivial at this size. `booking_slots` and audit rows recording `created_by`, `cancelled_by`, and status changes are additional and are not counted here. No cache, queue, or second service is justified by load.

## 3. Recommendation: modular monolith

One deployable web service (e.g., Node/Python) + existing relational DB. Modules: scheduling, availability, notifications-stub, admin. No microservices, no Kafka, no Redis in v1 — each would add deployment, monitoring, and failure modes a 2-person team cannot afford at <1 rps.

```mermaid
flowchart LR
  subgraph tb_public["Trust boundary: public internet (patient and receptionist apps)"]
    actor_client["Patient app and receptionist console - books and cancels (client team)"]
  end
  subgraph tb_vpc["Trust boundary: clinic VPC (clinic team)"]
    svc_booking["Booking service - schedules appointments, owns the no-overlap invariant (clinic team)"]
    store_appts[("Appointments DB - source of truth, written only by svc_booking (clinic team)")]
  end
  actor_client -->|"HTTPS 3s deadline"| svc_booking
  svc_booking -->|"SQL 1s deadline, exclusion constraint on insert"| store_appts
```

`svc_booking` is the only writer of `appointments`, so the exclusion constraint, not application logic, is the arbiter of the no-overlap rule.

When to change (measurable triggers): add async reminders/queue only when notification retries block requests or no-show rate justifies it; add read replica/cache only with sustained p95 > target on availability reads; split services only with a second team/ownership boundary or conflicting deploy cadence — not a request-rate threshold alone.

## 4. Data and the double-booking invariant

Owner: `appointments` table owns the invariant “no two booked appointments for the same provider overlap.”

```sql
-- PostgreSQL example; adapt if MySQL (see below)
-- btree_gist supplies the GiST operator class for uuid; it is a trusted extension, so a
-- non-superuser holding CREATE on the database can install it.
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE appointments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL,
  patient_id uuid NOT NULL,
  during tstzrange NOT NULL,
  status text NOT NULL CHECK (status IN ('booked','cancelled','completed')),
  idempotency_key text,
  request_fingerprint text NOT NULL,
  created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT appointments_patient_idempotency_key UNIQUE (patient_id, idempotency_key)
);
ALTER TABLE appointments ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (provider_id WITH =, during WITH &&)
  WHERE (status = 'booked');
```

Why this works, including empty schedules: the exclusion constraint is NOT DEFERRABLE, so PostgreSQL checks it immediately at the `INSERT`, atomically across concurrent transactions. Two concurrent `INSERT`s for overlapping `during` cannot both commit: the loser blocks until the winner commits, then the `INSERT` fails with `23P01` and the app returns `409 Conflict`. That failure aborts the transaction, so `COMMIT` is never reached. With two genuinely simultaneous inserts the GiST exclusion check can raise `40P01` (deadlock_detected) instead of `23P01`, so `40P01` has to be treated as a retryable conflict, not surfaced as a `500`. This holds when no conflicting row existed beforehand, unlike `SELECT → INSERT` in `READ COMMITTED`, where both reads see “free” then both insert. Do not rely on in-process locks: with two processes/containers or a restart they diverge.

Range bounds default to `[)`, so adjacent bookings ([09:00,09:30) and [09:30,10:00)) do not conflict, and the constraint is partial on `status = 'booked'`, so a cancelled row stops blocking the time it freed.

Isolation level: the default READ COMMITTED is sufficient here, because the loser of the race is rejected by the constraint at the `INSERT` (SQLSTATE 23P01) rather than by a stale read, so there is nothing to re-read and retry. Under SERIALIZABLE the same insert-insert conflict still fails with `23P01`; `40001` (serialization_failure) appears instead when the transaction first READS the conflicting range and then writes it, because SSI detects a read-write dependency cycle. Both errors abort the transaction, so both require retrying the whole transaction, not just the statement.

Timezone: the clinic's local timezone is a decision to make explicitly and store with the clinic (for example `America/New_York`). Keep `during` in UTC as `tstzrange` and build local ranges with `start_local AT TIME ZONE 'America/New_York'` rather than by casting a bare `date`/`timestamp`. A DST transition day is 23 or 25 hours long, so “the clinic's day” is not a fixed 24-hour window: define the local business-day boundary (local midnight to local midnight) and derive slots from the local calendar instead of adding 24 hours.

If the existing DB is MySQL/InnoDB (no exclusion constraints): pre-create fixed `slots(provider_id, starts_at UNIQUE)` and book with one atomic write. Preferred: `UPDATE slots SET status='booked' WHERE provider_id=? AND starts_at=? AND status='free'`, where `rows_affected = 1` means this request booked the slot and `0` means the slot is already booked. `INSERT ... ON DUPLICATE KEY UPDATE status='booked'` also works, but there `rows_affected` is 1 when the row was inserted and 2 when an existing row was updated, so 1 and 2 both mean success and 0 means the row was set to its current values, that is the slot is already booked. A 0 is indistinguishable from your own idempotent retry, because replaying a booking you already made returns 0 as well, so use the idempotency-key record to tell "mine" from "someone else's" and treat 0 as a replay to resolve rather than automatically as a conflict; testing `rows_affected == 1` on that path reports a false conflict on a successful booking. With `CLIENT_FOUND_ROWS` the 0 case never occurs, because matched rows are reported rather than changed rows.

Fixed-slot limitation: the `slots(provider_id, starts_at)` scheme only works if every booking snaps to the grid. Variable-length appointments (the follow-up case in §1) need a booking→slot join table, and the unique key in that table is what prevents double booking:

```sql
-- The fixed grid a provider is booked against.
CREATE TABLE slots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_id uuid NOT NULL,
  starts_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'free',
  UNIQUE (provider_id, starts_at)
);

-- Which appointment occupies which slot.
CREATE TABLE booking_slots (
  appointment_id uuid NOT NULL REFERENCES appointments(id),
  slot_id uuid NOT NULL REFERENCES slots(id),
  provider_id uuid NOT NULL,
  PRIMARY KEY (appointment_id, slot_id),
  UNIQUE (provider_id, slot_id)
);
```

The booking transaction inserts all of its slot rows and treats a duplicate-key error on `(provider_id, slot_id)` as 409.

Three locking options, in order of preference for PostgreSQL: (1) the exclusion constraint above, which is atomic, needs no application coordination, and is correct even when the conflicting row does not exist yet; (2) a lock row, `SELECT ... FOR UPDATE` on one row per provider, correct only if that row exists and every booking path takes it; (3) `pg_advisory_xact_lock(hashtext(provider_id::text))`, which needs no schema change but needs a stable key, the same lock ordering in every writer, and protects nothing if some path writes without taking it. Option 1 is the recommendation because it is the only one whose correctness does not depend on every writer cooperating.

Idempotency (double-click/retry ≠ double booking): client sends `Idempotency-Key`; the constraint `UNIQUE (patient_id, idempotency_key)` scopes the key to the patient the booking is for, not to the caller, so a receptionist and that patient share one namespace and a key that must not collide across callers has to carry the acting principal in its value. The lookup uses the AUTHORIZED `patient_id`: the session subject for a patient caller, and the request-body value after the receptionist role check for a receptionist, so a patient's key never returns another patient's row. On key reuse with a DIFFERENT payload (a different `request_fingerprint`, a hash of the booking request) the server returns `409 Conflict` with reason `idempotency_key_payload_mismatch` and never returns the other party's row. On key reuse with the SAME payload it returns the original row. The key column is nullable, so a request that omits the key is accepted but gets no retry protection; the client must send one. Cancellation is `UPDATE ... WHERE id=? AND status='booked'`; freed time becomes bookable; keep cancelled rows for audit.

## 5. Critical flows

Book: `POST /appointments {provider, start, duration, Idempotency-Key}` → authz (the patient id comes from the session for a patient caller, and from the request body after the receptionist role check for a receptionist) → validate window → `INSERT ... ON CONFLICT (patient_id, idempotency_key) DO NOTHING RETURNING *`. A returned row is the booking: 201. No returned row means the key was already used, so `SELECT ... WHERE patient_id = $1 AND idempotency_key = $2` and compare `request_fingerprint` with the hash of this request: equal means a replay, so return the stored row with 200; different means `409 Conflict` with reason `idempotency_key_payload_mismatch`, never the stored row. A raw `23505` (duplicate key violation on `appointments_patient_idempotency_key`) from a concurrent insert is the same replay path, so catch it and re-read. Separately, `23P01` from the exclusion constraint means the slot was taken, so return 409 with next-available suggestions. The request carries a 3s deadline and the database call a 1s budget. Timeout does not mean “not booked”: the client retries with the same key and the same payload and the server returns the existing row; the same key with a different payload is a conflict (409), and the server must not echo the stored row for a different request.

Cancel: `POST /appointments/:id/cancel` → authz (owner or receptionist) → conditional update. Race between two cancels is safe; race between cancel + rebook resolves by transaction order.

## 6. Failure, security, operations (minimal but explicit)

DB is the failure domain. Backups: `pg_basebackup` (or a managed snapshot) plus continuous WAL archiving enables point-in-time recovery; `pg_dump` is a logical, portable fallback only and cannot be replayed to an arbitrary point in time. Quarterly restore drill to a scratch host; document RTO/RPO after one drill. Observability: log booking attempts with provider/time/result; alert on 5xx rate and DB unavailability; track 409 rate (spike = UX or scraping issue), p95 booking latency, backup age. Runbook: “booking 500s” → check DB, queue-free deploy rollback, then run the overlap query below to confirm whether the invariant was breached.

```sql
-- Manual overlap check for one provider and window; lists booked rows that intersect it.
-- Same '&&' overlap operator and '[)' bounds as the exclusion constraint uses.
SELECT a.id, a.patient_id, a.during, a.status
FROM appointments a
WHERE a.provider_id = $1
  AND a.status = 'booked'
  AND a.during && tstzrange($2::timestamptz, $3::timestamptz, '[)');
```

Trust boundaries: patient sees only own bookings; receptionist role checked in server code per request (never trust client tenant/role claim); audit `created_by/cancelled_by`; encrypt in transit, encrypt at rest via managed disk/DB; retention/deletion policy confirmed with clinic before storing health-adjacent notes.

## 7. Trade-offs accepted

Monolith couples deploys but removes network partitions, dual-write, and cache-invalidation failures. Constraint-based correctness costs a Postgres-specific DDL (including the `btree_gist` extension) or slot-table discipline on MySQL and requires clients to handle 409s — cheaper than operating a lock service or queue for 300/day.

*Evidence that would change this answer: different RDBMS, requirement for cross-clinic scheduling, or a hard reminder-delivery SLA that forces async workers.*
