---
name: kafka-topic-and-consumer-tuning
description: Evaluates and tunes Kafka topic partitions, consumer group lag, and serialization schema contracts.
---

# Kafka Topic and Consumer Tuning Procedure

1. Read streaming event throughput specifications.
2. Determine partition count based on target consumer concurrency and key distribution.
3. Define event schema using Protobuf or Avro with strict backward compatibility rules.
4. Configure consumer group parameters: `max.poll.interval.ms`, `session.timeout.ms`, and retry backoff.
5. Implement Dead Letter Queue (DLQ) routing for poison-pill messages.
6. Verify consumer group rebalance behavior and assert zero message loss.
