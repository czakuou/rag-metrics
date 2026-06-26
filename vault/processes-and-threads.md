# Processes and Threads

A process is an independent execution unit with its own address space, file
descriptors, and OS-level resources. A thread is a unit of execution *within*
a process — threads in the same process share the same address space and
heap, but each has its own stack and registers.

## Why threads exist

Creating a process is expensive (new address space, page tables, copying or
duplicating resources). Threads are cheaper to create and context-switch
between because they share most of the process's resources. This makes
threads good for concurrent work that needs to share data without IPC.

## Process states

A process moves through states during its lifetime:
- New — being created
- Ready — waiting to be scheduled on the CPU
- Running — currently executing on a CPU core
- Waiting/Blocked — waiting on I/O or another event
- Terminated — finished execution

## Context switching

Switching from one process to another requires saving the current process's
CPU state (registers, program counter) into its process control block (PCB),
and loading the next process's saved state. This is pure overhead — no useful
work happens during a context switch, which is why excessive switching hurts
throughput. See [[Operating Systems — Memory Management]] for how TLB flushes add to this cost.

Related: [[CPU Scheduling]], [[Concurrency]]
