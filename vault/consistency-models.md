# Consistency Models

Different guarantees a distributed system can offer about what a read will
return relative to writes. Lecture 11, week 12 — related to [[CAP Theorem]].

## Strong consistency

Every read sees the most recent write, no matter which replica handles the
read. Easiest to reason about but requires coordination between replicas
(e.g. via [[Raft Consensus]] or Paxos), which costs latency and availability
during partitions.

## Eventual consistency

If no new writes occur, all replicas will *eventually* converge to the same
value, but there's no bound on how long "eventually" takes, and reads can
return stale data in the meantime. Common in systems that prioritize
availability (the "AP" side of CAP), like DynamoDB or Cassandra in their
default configuration.

## Causal consistency

A middle ground: writes that are causally related (B happened after reading
A) are seen by every node in that order, but writes that are causally
unrelated (concurrent) can be seen in different orders on different nodes.
Stronger than eventual, weaker than strong, and harder to implement than
either because you need to track causality (e.g. with vector clocks).

> Exam hint (TA said this out loud): know the ordering — strong > causal >
> eventual, in terms of how much the system guarantees.

Related: [[CAP Theorem]], [[Replication Strategies]], [[Distributed Systems MOC]]
