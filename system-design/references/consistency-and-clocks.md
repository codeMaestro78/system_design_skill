# Consistency, quorums, and clocks

Use this for: choosing a consistency model, sizing quorums, deciding replication topology, and picking an ordering mechanism. Sources: [Brewer's conjecture and CAP](sources.md#distributed-systems-and-messaging), [PostgreSQL isolation levels](sources.md#data-cloud-container-and-operations-sources), [PostgreSQL replication](sources.md#data-cloud-container-and-operations-sources), [DynamoDB read consistency](sources.md#data-cloud-container-and-operations-sources).

## Keep two axes apart

Database isolation and replication consistency are different questions. Isolation describes what concurrent transactions in one store may observe; consistency describes what a client observes across replicas or regions. A serializable database in one primary region has no replication consistency problem, and a globally replicated store can be linearizable inside a region while inconsistent across regions. Name the axis whenever consistency is used.

## What consensus actually buys

Consensus gives replicas an agreed, totally ordered log: every surviving replica ends with the same sequence, a majority is required to progress, and a minority partition stops rather than splitting. That is the building block for linearizable state, leader election, and distributed locks, not a database: no schema, no query plan, no secondary index, and no transaction spanning other systems.

| Model | Guarantee | Cost | Typical use |
| --- | --- | --- | --- |
| Linearizable (strong) | reads and writes appear as if one copy, ordered by real time | consensus or a leader; reads can fail in a partition | balances, inventory limits, locks |
| Sequential | all replicas see the same order, but not necessarily the order of real time | agreement without real-time ordering | rarely chosen |
| Read-your-writes, monotonic reads | a client sees its own writes and never goes backwards in a session | session tokens, sticky routing, version fences | read after write |
| Causal | only causally related events are ordered | per-request context propagation | messaging and collaboration |
| Eventual | replicas converge once writes stop | conflict detection, read repair, staleness | catalogs, feeds, caches, analytics |

## A lock service is usually the wrong answer

A distributed lock service must itself be linearizable, so it introduces a quorum system, a network hop, lease expiry, and a new failure mode, to protect a resource a single database can protect with a unique constraint, an exclusion constraint, a conditional update, or a row lock. Prefer that. Use a lock service only when the invariant genuinely spans systems that share no store and no transaction, and then require a lease with expiry and a fencing token that the protected resource checks, because a paused holder that resumes later would write with a stale lease.

## Quorum arithmetic

For a replica set of N, a read quorum R, and a write quorum W, any read quorum and any write quorum overlap when R + W > N. The overlap is what makes the read see the write.

| N | W | R | R + W | Stale read possible | Write availability |
| --- | --- | --- | --- | --- | --- |
| 3 | 2 | 2 | 4 > 3 | no | survives one replica failure |
| 3 | 2 | 1 | 3 = 3 | yes | survives one replica failure |
| 3 | 1 | 1 | 2 | no guarantee | survives two replica failures |
| 5 | 3 | 3 | 6 > 5 | no | survives two replica failures |

Worked example. With N = 3, W = 2, R = 2: a write is committed to replicas A and B, and a later read asks B and C. The read set and the write set intersect at B, and B holds the write, so the read returns the committed value. A read that asks only A and C can miss the write, which is why the read quorum must overlap every write quorum. Availability follows from the same arithmetic: with two of three replicas failed, W = 2 cannot be met, so the store refuses writes and trades availability for consistency.

The rule is necessary, not sufficient. It assumes a committed write is durable on the quorum, that sloppy writes, which land on other nodes and are moved later, are not used, and that concurrent writers are ordered by a leader or a version comparison. Without an ordering rule, a quorum system resolves concurrent writes by version, and the version scheme picks the winner.

## Read repair

A read that observes divergent versions repairs it by writing the winning value back to the replicas it read, so the reader needs write permission and a read path can become a writer. Compare versions before writing back, never timestamps alone, or a stale reader overwrites a newer value. A failed repair must not fail the read, and repairs must be idempotent. In leader-follower deployments, let the leader perform the repair instead of every client.

## Replication topologies

| Topology | Write path | Conflict handling | Read staleness | Failover | Typical use |
| --- | --- | --- | --- | --- | --- |
| Leader-follower | one leader, replicated to followers | none while one leader exists | followers lag the leader | election plus fencing | transactional systems with one write order |
| Consensus based (Raft) | leader appends, majority commits | none, the log is totally ordered | reads from the leader or a lease | a new leader is elected | strongly consistent coordination state |
| Multi-leader | each site writes locally, replicates to the others | concurrent edits to one key need version comparison and a merge rule | local reads fresh, remote reads stale | built in per site | multi-region with regional write ownership |
| Leaderless (quorum) | any node accepts a write, versions converge | per-record version comparison, application-defined merge | quorum read with repair | none needed, no single authority | available stores with tolerant conflicts |

Multi-leader is where write conflicts appear: two regions edit the same record, and the merge rule, not the transport, decides the outcome. Leaderless spreads that problem across every node, which is why version comparison and the merge rule belong in the data model.

## Partitions

During a partition the side holding a majority keeps serving, and the minority side must decide. Refuse the writes that would break an invariant, which requires a fence so a recovered minority leader cannot write with a stale lease, or accept the writes and reconcile them later, which needs conflict detection and a merge rule a user can understand. Decide per operation rather than declaring a global mode. Availability and consistency cannot both be held for the affected data, so state which one you chose.

## Ordering and clocks

| Mechanism | Guarantees | Limits | Use for |
| --- | --- | --- | --- |
| Wall clock (NTP) | approximate wall time | can step backwards, not monotonic | display, human deadlines, rate windows |
| Lamport clock | a total order consistent with causality | cannot tell concurrent events apart | ordering events in one logical system |
| Vector clock | per-replica causality, so concurrency is detectable | metadata grows with replica count | conflict detection in leaderless and multi-leader |
| Hybrid logical clock | monotonic per node, close to wall time, carries causality for last-write-wins | assumes bounded clock skew | last-write-wins with a timestamp, audit ordering |
| Broker offset | monotonic and totally ordered within a partition | ordering stops at the partition | ordering events in one stream |
| Time-ordered identifier (UUIDv7) | sortable by creation time | only as accurate as the generating clock, proves no causality | keying and index locality |

Never order events by a client-supplied timestamp. Give the server a monotonic sequence for anything that must be ordered, and detect cross-node causality rather than assume it.

```python
def compare_clocks(a, b):
    """Return 'before', 'after', or 'concurrent' for two vector clocks."""
    a_before_b = all(b.get(k, 0) <= v for k, v in a.items())
    b_before_a = all(a.get(k, 0) <= v for k, v in b.items())
    a_strict = any(b.get(k, 0) < v for k, v in a.items())
    b_strict = any(a.get(k, 0) < v for k, v in b.items())
    if a_before_b and a_strict:
        return "before"
    if b_before_a and b_strict:
        return "after"
    return "concurrent"
```

## The practical conclusion

Most systems need one writer and one database, not a distributed lock. Put the invariant in a single store and enforce it in a single transaction with a constraint rather than in application logic that races. When the invariant spans two stores, give one domain a single writer, publish the change through an outbox, and accept eventual consistency in the other. Reserve consensus for small coordination state with a clear linearizability requirement and an explicit majority-availability budget, and give that state a fencing mechanism. Prefer session-level guarantees such as read-your-writes over global serialization, because they cost less and cover most complaints. See [data architecture](data-architecture.md) and [distributed systems](distributed-systems.md).
