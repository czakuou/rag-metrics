# CPU Scheduling

How the OS decides which ready process gets the CPU next.

## Scheduling algorithms

- **FCFS (First Come First Served)** — simple queue, no preemption. Bad
  average wait time if a long job arrives first (convoy effect).
- **SJF (Shortest Job First)** — minimizes average wait time optimally if you
  know job lengths in advance, which you usually don't.
- **Round Robin** — each process gets a fixed time quantum, then goes back to
  the end of the queue. Fair, good for interactive systems, but throughput
  suffers if the quantum is too small (context switch overhead dominates).
- **Priority Scheduling** — each process has a priority; highest priority
  runs first. Risk of starvation for low-priority processes unless you use
  aging (gradually increase priority of waiting processes).
- **Multilevel Feedback Queue** — multiple queues with different priorities
  and quantum sizes; processes move between queues based on behavior (CPU
  bound vs I/O bound). What most real OS schedulers approximate.

> Linux uses CFS (Completely Fair Scheduler) by default, which doesn't use
> queues at all — it uses a red-black tree keyed on "virtual runtime" to
> always pick the most CPU-starved process next.

Related: [[Processes and Threads]], [[Operating Systems — Memory Management]]
