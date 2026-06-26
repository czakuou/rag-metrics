# Concurrency

messy notes, typing fast during lecture, fix later (never did)

so the basic idea is multiple things happening at once but on a single core
it's actually interleaved not truly parallel, that's concurrency vs
parallelism, profesor kept going back to this. it uses a lock to prevent
this, but they can deadlock if they grab them in different order, see
[[Deadlock]] for that.

race condition is when two of them touch the same thing at the same time and
it depends on timing which one wins, that's the bug. happens a lot with
shared counters, this is why you need atomic ops or a lock around it.

mutex vs semaphore — he said these are different but honestly still not 100%
clear on it. a mutex is basically a lock that one of them holds at a time,
ownership matters. a semaphore is a counter, lets N of them in, doesn't
really have "ownership" the same way, any of them can release it not just
the one that acquired it. that part's important apparently.

> this whole section is a mess but I'm scared to delete it because some of it
> might actually be on the exam

producer-consumer problem: one or more produce items, one or more consume
them, they share a buffer, this is where it gets tricky because if it's
full the producer has to wait and if it's empty the consumer has to wait,
that's what a condition variable is for, it lets you sleep until someone
else signals you instead of busy-waiting which wastes cpu.

also there's the readers-writers problem, multiple readers can go at once
since they're not changing anything, but a writer needs exclusive access,
so it blocks everyone else including other writers. starvation can happen
here if writers never get a turn because readers keep coming in, depends on
the policy (fair vs reader-preferring vs writer-preferring).

spinlocks vs regular locks — a spinlock just busy-loops checking the flag
instead of sleeping, faster if you expect to wait a very short time (avoids
context switch cost) but wastes cpu cycles if you guessed wrong and end up
waiting a while. regular locks (mutexes) put the thread to sleep instead,
better for longer waits.

threading in python is its own can of worms because of the GIL (global
interpreter lock) — only one of them can execute python bytecode at a time
even with multiple threads, so threads don't actually help cpu-bound work
in python, only IO-bound stuff where it's waiting on something external
anyway. multiprocessing sidesteps it by using separate processes instead,
each with their own GIL, but then you don't share memory directly anymore.

see [[Processes and Threads]] for the more organized version of some of
this, this note is more "what actually got said out loud in lecture" than a
clean reference.
