# Mobile clients and offline synchronization

Use this for: mobile and desktop client behavior, version skew, session lifetime, background work, and offline-first data design. Sources: [RFC 9700 OAuth security practice](sources.md#api-and-protocol-design), [RFC 9110 HTTP semantics](sources.md#api-and-protocol-design), [NIST SP 800-63-4](sources.md#security-and-privacy), [OWASP authorization guidance](sources.md#security-and-privacy).

## The client is a versioned, untrusted, intermittently connected peer

A deployed app is a population of clients you do not control: old versions persist, networks fail, clocks drift, devices are shared, and the app is uninstalled and reinstalled. Design the server to expect it. Keep a stated minimum supported version, enforce it on the endpoints where an old client is unsafe, and return a structured error that names the minimum version and the upgrade route rather than a generic failure. The API must remain compatible with the oldest supported version for a stated window, so a version policy and a compatibility policy are the same decision.

Roll out versions gradually by percentage and cohort, keep a kill switch per version, and measure the version distribution of live traffic before retiring anything. A client that cannot reach the store for an update still runs the code it has, so server behavior must be version-aware for a long tail.

## Sessions, tokens, and long-lived access

Use short-lived access tokens and rotating refresh tokens with reuse detection, so a stolen refresh token is usable at most once before the legitimate client is forced to re-authenticate. Evaluate expiry against server time, never the device clock, and return the server time in a response header so the client can detect skew. Bind the session to a device identifier where the risk justifies it, and give users a way to list and revoke sessions, since a lost device is a permanent session otherwise.

Access token refresh competes with foreground work and with background execution limits. Refresh on foreground, on network reconnection, and on a 401, not on a timer that the operating system may suspend. Treat a revoked or expired session as a normal state that the UI can explain, not a crash.

## Background execution and push

The operating system decides when background code runs, and push delivery is a hint, not a guarantee: tokens rotate, the network may be absent, the user may have disabled notifications, the platform may throttle, and a notification tapped hours later may describe stale state. Use push to tell the client that something may have changed, then have the client fetch with a conditional request; never encode a durable state change only in a push payload. Put background work on a constrained work queue with network and charging conditions, make every unit resumable, and assume a task scheduled now may run much later or never.

## Offline sync is a first-class problem

Offline-first is a data design decision, not a caching tactic. The client holds a replica of a subset of the server's state, and the two replicas can diverge. Decide what the client owns, what the server owns, how changes are detected, and how conflicts are resolved before writing the sync code.

Keep the local store small and purpose-built: only the entities the user reads or edits offline, with a schema version and a migration path. Encrypt the store at rest through platform file protection, and apply column-level encryption to high-sensitivity fields with keys held in the platform keystore. Treat the device as compromised territory: a rooted device, a memory dump, or a backup can read plaintext. Exclude sensitive local files from device backup and from screenshots, and remember that keystore-backed keys are commonly destroyed on uninstall while some keychain data persists.

## Delta sync against full sync

| Mode | Cost | Behavior | Use when |
| --- | --- | --- | --- |
| Full pull | proportional to the whole collection on every sync | simple, no cursor state, expensive as data grows | small collections, first sync, or after a schema change |
| Delta pull | proportional to changes since the cursor | needs an opaque monotonic cursor, tombstones for deletions, and a stable order | normal operation |
| Snapshot plus deltas | one full transfer, then cheap increments | needs a snapshot token that is consistent with the delta stream | large collections with a resumable first sync |

The cursor must be opaque and monotonic, and the client must store it only after the changes are applied durably. A cursor that the client cannot interpret still works, but a cursor that can silently be reused for a different collection cannot.

## Conflict strategies

| Strategy | Guarantee | Cost | Fits | Failure mode |
| --- | --- | --- | --- | --- |
| Last write wins with server or hybrid clock | one value survives | trivial to implement, no merge logic | independent scalar fields, settings, presence | silently discards one user's edit with no signal |
| Vector clocks and CRDTs | concurrent edits are preserved and merged deterministically | per-replica metadata that grows with the writer count, nontrivial type-specific merge rules | collaborative documents, sets, counters, tags | a merge can be semantically wrong, such as a delete combined with a concurrent edit |
| Operational transform | concurrent edits are transformed into a serializable order | transform functions per operation type, central ordering authority, hard with offline reordering | collaborative text editing | incorrect transform functions silently corrupt content |

Pick per field or per entity, not per application. Most business records are not collaborative: they are records that a user submits and the server accepts or rejects, and the right mechanism there is a version check with a conflict response rather than a merge.

## Conflict UX and tombstones

Never silently drop a user's edit. When the server rejects a mutation because the record changed, keep the local edit, show the server value and the local value, and let the user choose, or merge automatically only when the edited fields are disjoint. A merge that is usually right but occasionally wrong is worse than a conflict screen that asks.

Deletions are changes and must propagate, so the server keeps a tombstone with the record version and the client applies it. Tombstones cannot be garbage collected until every live client has acknowledged the deletion, which is not knowable in general. Use a per-device last-seen cursor plus a deletion watermark older than the longest acceptable offline window, and force a full resync when a returning client is older than the watermark. A client that returns after a deletion was collected can otherwise resurrect deleted data.

## Caching, reinstall, and data loss

Cache for read latency and offline availability, and let the server remain the authority for anything the user cannot afford to get wrong: authorization, price, balance, availability, quota, and every irreversible action. A cached price shown in a cart is a display, and the order submission re-validates it. Cache entries carry an as-of timestamp so the client can say how old the data is, and a stale read is shown as stale rather than as current. Never make an authorization decision from local state, and never let the client widen its own permissions by editing a local record.

Uninstalling usually destroys the local store, and any unsynced work is lost with it. Decide what the user is told, keep a server-side draft for work worth preserving, and make the first sync after reinstall a full sync with a fresh cursor. If the local store is encrypted with device-bound keys, reinstalling removes the key and the data is unrecoverable, which is a feature for some data and a data-loss event for others, so classify each field.

## What the API must expose

- Opaque monotonic change cursors per collection, and a documented reset when a cursor expires.
- Stable resource identifiers and per-record version numbers, so the client can detect a stale base version.
- Server-authoritative timestamps, since client clocks are untrusted.
- Idempotency keys on mutations, so a retry after a timeout does not duplicate a write.
- Conflict responses carrying the current server state and the client's base version, so the client can merge or ask.
- Tombstones in delta responses, and a snapshot endpoint that rebuilds a client from scratch.
- Conditional fetches (ETag or equivalent) so a sync that finds no change costs one round trip.

## Reference sync loop

```python
def sync(client, server):
    # pull: ask only for what the client has not applied yet
    page = server.get_changes(collection, cursor=client.cursor, limit=200)
    for change in page.changes:
        apply_locally(client.store, change)  # includes tombstones
    client.cursor = page.next_cursor  # store only after the write is durable

    # push: send local mutations with a stable id so a retry cannot duplicate them
    for mutation in client.pending_mutations():
        result = server.apply(mutation, idempotency_key=mutation.mutation_id, base_version=mutation.base_version)
        if result.status == "conflict":
            client.store.save_conflict(mutation, result.server_state)  # surface, never overwrite
        else:
            client.store.mark_applied(mutation, result.server_version)
    client.ack_applied()  # drop only what the server accepted
```
