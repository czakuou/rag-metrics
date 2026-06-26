# Distributed Systems MOC

Map of content for the distributed systems unit (and a few adjacent topics I
keep needing to cross-reference). Mostly just links with a one-liner each so
I can find things fast before the exam.

- [[CAP Theorem]] — why you can't have consistency, availability, and
  partition tolerance all at once
- [[Consistency Models]] — strong vs causal vs eventual consistency
- [[Raft Consensus]] — leader election + log replication for agreement
  across nodes
- [[Replication Strategies]] — single-leader, multi-leader, leaderless, and
  sync vs async
- [[TCP — How it Works]] — the transport layer underneath basically every
  distributed protocol
- [[TCP vs UDP]] — when reliability matters vs when latency matters more
- [[HTTP and DNS]] — application-layer protocols that sit on top of TCP
- [[TLS Overview]] — securing the connection between distributed nodes
- [[Deadlock]] — not distributed-specific but the same circular-wait idea
  shows up in distributed transaction coordination
- [[Processes and Threads]] — the local concurrency building blocks that
  distributed systems are made of, one node at a time

> Putting this together helped me see that half of "distributed systems" is
> really just "what happens when you can't trust the network," and the other
> half is "how do multiple machines agree on anything."
