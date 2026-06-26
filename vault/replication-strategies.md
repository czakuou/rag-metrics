# Replication Strategies

Why replicate data across multiple nodes? Fault tolerance (survive node
failure), and scaling read throughput (more replicas to serve reads from).

## Single-leader (primary-replica)

One node is the leader and accepts all writes. Writes are propagated to
follower replicas, which serve read traffic. Simple to reason about, but the
leader is a single point of failure for writes (need leader election on
failure — see [[Raft Consensus]]) and a bottleneck for write throughput.

## Multi-leader

Multiple nodes accept writes independently (e.g. one leader per datacenter),
and leaders replicate to each other. This avoids the single-write-bottleneck
problem but introduces write conflicts when two leaders accept conflicting
writes to the same record concurrently — conflict resolution gets messy fast.

## Leaderless

Any replica can accept a write (Dynamo-style). The client (or a coordinator)
writes to multiple replicas directly and reads from multiple replicas,
using quorums (e.g. write to W replicas, read from R replicas, with
W + R > N to guarantee overlap) to maintain consistency guarantees.

## Sync vs async replication

- Synchronous — the leader waits for the replica to confirm before
  acknowledging the write to the client. Strong durability, but write latency
  is bounded by the slowest replica, and availability drops if a replica is
  unreachable.
- Asynchronous — the leader acknowledges immediately, replicates in the
  background. Fast, but risks data loss if the leader fails before
  replicating.

This sync/async tradeoff is basically [[CAP Theorem]] showing up again at the
replication layer rather than the whole-system layer.

Related: [[Raft Consensus]], [[Consistency Models]], [[Distributed Systems MOC]]
