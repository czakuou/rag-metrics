# Deadlock

## Definition

A deadlock is a state where two or more processes are each waiting for a
resource held by another process in the set, so none of them can ever
proceed. Nobody is making progress and nobody ever will without outside
intervention (killing a process, forcibly releasing a resource, restarting).

This is different from starvation, where a process *could* eventually run
but keeps getting passed over — deadlock is a permanent stuck state, not
just unlucky scheduling.

## Necessary Conditions (Coffman Conditions)

A deadlock can only occur if all four of these hold simultaneously:

1. **Mutual exclusion** — at least one resource is held in a non-shareable
   mode (only one process can use it at a time).
2. **Hold and wait** — a process holding at least one resource is waiting to
   acquire additional resources currently held by other processes.
3. **No preemption** — resources cannot be forcibly taken away from a
   process; they must be released voluntarily.
4. **Circular wait** — there's a cycle of processes, where each process is
   waiting for a resource held by the next process in the cycle.

Breaking *any one* of these four conditions is enough to prevent deadlock —
this is the basis for most deadlock prevention strategies (e.g. always
acquiring resources in a fixed global order breaks circular wait).

## Example

Classic textbook example: process A holds lock 1 and wants lock 2. Process B
holds lock 2 and wants lock 1. Neither can proceed — A is waiting on B, and B
is waiting on A. Drawing this as a graph (resource allocation graph), you get
a cycle: A -> lock2 -> B -> lock1 -> A. A cycle in the resource allocation
graph is exactly the circular wait condition from above, and (for single-
instance resources) a cycle is both necessary and sufficient for deadlock.

```python
# Thread 1
lock1.acquire()
lock2.acquire()  # blocks if Thread 2 holds lock2

# Thread 2
lock2.acquire()
lock1.acquire()  # blocks if Thread 1 holds lock1
```

> This is exactly the kind of bug [[Concurrency]] notes are warning about
> when they mention locks deadlocking each other — same idea, less formal.

## Detection and recovery

Some systems don't prevent deadlock at all — they let it happen and detect
it afterward (e.g. databases detecting a cycle in the wait-for graph), then
recover by aborting one of the transactions involved and rolling it back.
This trades a rare expensive recovery for not paying the cost of strict
prevention on every single resource acquisition.

Related: [[Processes and Threads]], [[Concurrency]], [[CPU Scheduling]]
