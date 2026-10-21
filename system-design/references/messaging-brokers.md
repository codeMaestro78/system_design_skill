# Messaging brokers and delivery semantics

Use this for: choosing between a queue, a log, pub/sub, and a direct call, and specifying delivery, ordering, retention, and consumer behavior. Sources: [Confluent delivery semantics](sources.md#distributed-systems-and-messaging), [SQS standard queues](sources.md#distributed-systems-and-messaging), [AWS queue backlog](sources.md#sre-reliability-operations), [Little's law](sources.md#distributed-systems-and-messaging), [Transactional outbox](sources.md#patterns).

## Choose the primitive before the product

- **Queue (work distribution):** one message reaches one consumer in a group; the consumer owns the work and acknowledges it. Fits task processing, buffering, and load smoothing. History ends at acknowledgement.
- **Log (durable ordered stream):** records are retained in partitions; each consumer group reads the whole log at its own offset. Fits event publication, replay, and several independent consumers.
- **Pub/sub (notification fan-out):** the broker routes to interested subscribers with little durable history. Fits fan-out where a subscriber only needs a hint to fetch.
- **Direct call:** the caller owns timing, retry, and failure. Fits read paths and any work the user is waiting on.

## Ordering scope is a property of the key, not the broker

Kafka orders records within a partition, and the partition is chosen by the record key, so order follows that key and not the topic. SQS FIFO orders within a message group, which means one group per entity whose order matters. SQS standard makes no ordering promise. RabbitMQ preserves order in a single queue only while messages are not requeued or redelivered. NATS orders per subject for a queue group, and JetStream keeps per-subject order inside a stream. Global order exists only by giving up parallelism: a single partition or a single writer.

Ordering also breaks in ways that are not broker defects. A consumer that processes a partition in parallel can finish the second record before the first. A retried record can arrive after later records. A rebalance redelivers in-flight work. A compaction policy can remove records. Name the ordering key, the in-consumer parallelism, and the client-visible tolerance for reordering.

## Delivery semantics, scoped

"Exactly once" is a property of a named boundary, never of the business outcome. Side effects outside the broker (charging a card, sending mail, calling a tax service) are unprotected by any broker guarantee, so the consumer must be idempotent.

| Product | Documented delivery | Ordering scope | Scope limit |
| --- | --- | --- | --- |
| Kafka | at-least-once by default; transactions give exactly-once for a Kafka-to-Kafka read-process-write | per partition | does not cover external side effects; a crash before commit replays records |
| SQS standard | at-least-once; duplicates possible | none | can deliver out of order and can redeliver after a visibility timeout expires |
| SQS FIFO | exactly-once processing inside a bounded deduplication window | per message group | needs a deduplication id and a group per entity; throughput depends on group distribution |
| RabbitMQ | at-least-once with publisher confirms and consumer acknowledgements | per queue | requeue and redelivery break the original order; quorum queues change durability, not ordering |
| NATS Core | at-most-once | per subject | no persistence; a disconnected subscriber loses the message |
| NATS JetStream | at-least-once with explicit acknowledgement, bounded redelivery, deduplication by message id | per subject | acknowledgement and redelivery are per consumer; a slow consumer holds the redelivery window |
| SNS | at-least-once to subscribed endpoints | none | endpoint retries exist, but a subscriber that was down is not replayed later |

Treat every row as product documentation to re-check against current vendor sources, not as a portable guarantee.

## Retention, replay, and state rebuild

A log broker retains records for a configured period or size and can replay them from an offset. A queue broker holds a message only until it is acknowledged or expires, so it is not a history. Replay is safe only when the consumer is idempotent and the handler can rebuild state deterministically; a handler that sends mail or charges a card must suppress duplicates. Replaying a retained window replays old schema versions too, so keep handlers able to read prior shapes or drain the log forward before changing the contract. The retention period is a data-loss horizon: anything that must not be lost belongs in a store of record, not in a topic.

## Consumer groups, offsets, and rebalancing

A consumer group is the unit of parallelism and of progress. Kafka assigns partitions to group members and stores a committed offset per partition; commit after the side effect, not before, or a crash loses work. Auto-commit can both lose and duplicate records. RabbitMQ uses acknowledgements and prefetch to pace a consumer, so an unbounded prefetch lets one slow consumer hold the backlog. SQS hides the offset in the message lifecycle and leaves deletion to the consumer. NATS uses explicit acknowledgement and a durable consumer position.

Rebalancing is the price of membership change: a deploy, a scale event, or an instance loss moves partitions, pauses consumption, and redelivers in-flight work. A large group rebalances slowly, so scale in steps and keep the rebalance window inside the alert budget. Observe lag per group, not per broker.

## Poison messages, retries, and dead letters

Classify every failure: transient (timeout, dependency), permanent-data (malformed payload, missing field, schema violation), and business (valid but rejected). Retry only the transient class, with capped attempts, exponential backoff, and jitter. Send the permanent-data class to a dead-letter destination on the first failure, because a poison record retried inline blocks the partition. Carry the original payload, the error, the attempt count, the producer identity, and a correlation id, and give operators a way to inspect, fix, and replay. A delayed retry topic adds backoff without blocking the partition.

Dead letters are where messages go to be lost. Alert on depth and oldest age, sample and triage, and make replay a deliberate operation with its own dedupe handling.

## Fan-out and backpressure

Fan-out multiplies work by the number of subscribers, so the slowest subscriber sets the required rate. Apply backpressure at the producer: bound in-flight messages, reject with a retry hint at the bound, and let the broker expire or shed the oldest work rather than growing without limit. Track backlog age, not only depth; a stable depth with rising age means the consumer is permanently behind. Use Little's law to size the buffer: a bounded backlog at a stable arrival rate implies an acceptable wait. Queue bounds turn overload into deliberate loss of the oldest work, so decide per message class whether that is acceptable.

## Latency against throughput

Batching, acknowledgements, and compression trade latency for throughput. A producer that waits to fill a batch delays the first message; a producer that flushes synchronously to disk pays another round trip. Long polling reduces empty receives at the cost of a fixed wait. Measure producer to consumer, and separate the percentile the user feels from the one that drives cost.

## Operational burden

Every broker adds a stateful platform: capacity planning, sizing, access control, message contracts, lag and depth monitoring, and a recovery story. Kafka adds partition rebalancing, retention and compaction policy, group state, and a partition ceiling that caps parallelism. RabbitMQ adds memory and disk alarms plus a mirroring decision. SQS standard adds visibility timeout tuning and duplicate handling, with a per-request cost that scales with message count rather than size. Managed brokers remove patching and failover work but add quotas, regional limits, and vendor-specific semantics. Budget the on-call and the migration, not only the per-message cost.

## When a queue is not worth it

A queue accepts work that cannot be done now; it does not create capacity. Do not add one when the caller is waiting and the work fits the request path, when read-your-writes is required, when the ordering and duplicate semantics you need are not offered, when the volume fits a table plus a scheduled worker, when the consistency delay is visible to the user, or when nobody will own the backlog, lag, and dead letters. See [distributed systems](distributed-systems.md) for the failure model and [testing and evolution](testing-evolution.md) for contract, replay, and poison-message tests.

## Reference consumer loop

```python
def consume(records, store, retry_topic, dead_letter):
    for record in records:
        if store.has_effect(record.event_id):  # inbox dedupe, stored with the effect
            record.commit()  # duplicate delivery: skip the side effect
            continue
        try:
            result = handle(record)
        except TransientError:
            retry_topic.publish(record, delay=backoff(record.attempts))  # bounded, jittered
            record.commit()
            continue
        except PermanentError as exc:
            dead_letter.publish(record, error=str(exc), attempts=record.attempts)
            record.commit()
            continue
        store.apply_effect(result, event_id=record.event_id)  # effect and dedupe row in one tx
        record.commit()  # commit the offset only after the effect
```
