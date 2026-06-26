# Raft Consensus

High-level notes only — the professor said a full proof of Raft's safety is
out of scope for this course, thankfully.

## The problem

Consensus means getting a cluster of nodes to agree on a single value (or
sequence of values, like a replicated log) even when some nodes fail or
messages are delayed. This is the core building block for replicated state
machines — see [[Replication Strategies]].

## Roles

Raft splits nodes into three roles:
- **Leader** — handles all client requests, replicates log entries to
  followers
- **Follower** — passive, responds to the leader and to candidates
- **Candidate** — a follower that hasn't heard from a leader recently and is
  trying to become the new leader

## Leader election

Time is divided into terms. If a follower doesn't hear a heartbeat from the
leader within a randomized timeout, it becomes a candidate, increments the
term number, and requests votes from other nodes. A candidate becomes leader
if it gets votes from a majority of nodes. The randomized timeout is
important — it reduces the chance of split votes where multiple candidates
request votes simultaneously.

## Log replication

The leader appends client commands to its log and replicates them to
followers. An entry is considered "committed" once a majority of nodes have
it in their log — this majority requirement is what survives a minority of
node failures.

> Compared to Paxos (which the professor called "famously hard to understand
> correctly"), Raft was explicitly designed for understandability, splitting
> the problem into leader election, log replication, and safety as separate
> sub-problems.

Related: [[Consistency Models]], [[Replication Strategies]], [[Distributed Systems MOC]]
