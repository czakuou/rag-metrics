# Operating Systems — Memory Management

Lecture 8, week 9. This was a dense one, taking my time writing it up properly
because I know it's going to be on the exam.

## Virtual Memory

Virtual memory is the abstraction that gives every process the illusion of
having its own private, contiguous address space, even though physical RAM is
shared, fragmented, and often smaller than the sum of all processes' demands.
The OS and the MMU (memory management unit) work together to translate virtual
addresses used by a program into physical addresses in RAM. This indirection
is what makes isolation between processes possible — process A cannot see or
corrupt process B's memory because A's virtual addresses are mapped to a
completely different region of physical RAM (or disk).

The benefits go beyond isolation. Virtual memory also enables:
- Running programs larger than physical RAM (via paging to disk)
- Sharing physical memory pages between processes (e.g. shared libraries)
- Giving each process a simple, flat address space starting at 0
- Copy-on-write for efficient process forking

> This finally clicked for me when the professor compared it to hotel room
> numbers — the room number (virtual address) stays the same, but which
> physical room you're actually in can change.

## Page Tables

The mapping between virtual and physical addresses is stored in a **page
table**, one per process. Each entry (PTE) maps a virtual page number to a
physical frame number, plus metadata bits: present/absent, dirty, accessed,
protection bits (read/write/execute).

Page tables are themselves stored in memory, which creates a chicken-and-egg
problem: translating an address requires reading the page table, which is
itself at some address. Multi-level page tables solve part of this by paging
the page table itself, so you don't need a giant flat array covering the
entire 64-bit address space for every process.

A typical x86-64 setup uses a 4-level page table:
1. PGD (page global directory)
2. PUD (page upper directory)
3. PMD (page middle directory)
4. PTE (page table entry)

Each level adds a memory access, so naively this means 4 memory accesses just
to resolve one address. That's where the TLB comes in.

## TLB (Translation Lookaside Buffer)

The TLB is a small, fast, hardware cache of recent virtual-to-physical
translations, sitting right next to the CPU core. Instead of walking the page
table on every memory access, the CPU first checks the TLB. A TLB hit means
the translation is basically free (a few cycles). A TLB miss means the CPU
(or OS, depending on architecture) has to walk the page table, which is much
slower, and then cache the result in the TLB for next time.

TLBs are typically small — a few hundred entries — because they need to be
extremely fast (checked on every single memory access). This means TLB misses
are common when a process has poor locality, jumping around a large address
space.

Context switches are expensive partly because of TLB flushes (the TLB entries
belong to a specific process's address space, so on x86 they often get
invalidated when switching to a different process, unless tagged TLBs/ASIDs
are used).

## Page Faults

A page fault occurs when a program accesses a virtual address that doesn't
currently have a valid mapping to physical memory. This is not always an
error! There are a few cases:

- **Minor fault**: the page is in physical memory but not yet mapped into the
  process's page table (e.g. shared memory, copy-on-write pages).
- **Major fault**: the page must be loaded from disk (e.g. it was swapped out,
  or this is the first access to a memory-mapped file). These are much slower
  — disk I/O is orders of magnitude slower than RAM.
- **Invalid/segmentation fault**: the access is illegal (e.g. writing to
  read-only memory, or accessing unmapped memory entirely). This is the one
  that crashes your program with `Segmentation fault (core dumped)`.

On a major fault, the OS must:
1. Find a free physical frame (possibly evicting another page — see below)
2. Read the page contents from disk into that frame
3. Update the page table to point to the new frame
4. Resume the faulting instruction

> Demand paging is the strategy of only loading pages when they're actually
> faulted in, rather than loading the whole program up front. Makes startup
> way faster for large programs.

## Thrashing

Thrashing happens when the system spends more time paging (swapping pages in
and out) than doing actual useful work. It's a vicious cycle: too many
processes (or one process with too large a working set) compete for too
little physical memory, so pages get evicted right before they're needed
again, causing another fault, causing another eviction, and so on.

Symptoms of thrashing:
- CPU utilization drops even though there's "work to do" — the CPU is mostly
  waiting on disk I/O for page faults
- Disk activity light is basically always on
- System feels frozen even though nothing is technically deadlocked

The classic fix is the **working set model** — track each process's working
set (the set of pages it has accessed recently) and only let a process run if
its entire working set can fit in memory. If there isn't enough physical
memory for everyone's working set, the OS should reduce the degree of
multiprogramming (suspend a process) rather than let everyone starve equally.

Page replacement algorithms matter a lot here:
- **LRU (Least Recently Used)** — evict the page that hasn't been used in the
  longest time. Good approximation of "will be needed again soon" but
  expensive to implement exactly.
- **Clock / Second-chance** — approximates LRU cheaply using a reference bit
  and a circular buffer of pages.
- **Optimal (Belady's algorithm)** — evict the page that won't be used for the
  longest time in the future. Not implementable in practice (requires future
  knowledge) but used as a theoretical baseline.

> Belady's anomaly: increasing the number of physical frames can sometimes
> *increase* the page fault rate under FIFO replacement. Counter-intuitive
> and was a fun "wait, what?" moment in lecture.

## Segmentation vs Paging

Before paging became the dominant approach, some systems used segmentation:
dividing the address space into variable-sized logical segments (code, heap,
stack, etc.) rather than fixed-size pages. Segmentation maps more naturally
onto how programs are structured, but variable-sized segments cause external
fragmentation — over time, free physical memory ends up scattered into small
holes that are individually too small to satisfy a new allocation, even
though the total free space would be enough.

Paging avoids external fragmentation by using fixed-size pages and frames —
any free frame can hold any page, no matter where it sits physically. The
tradeoff is internal fragmentation: if a process's last page isn't fully
used, the unused remainder is wasted (bounded by the page size, typically
4KB on x86, so much less wasteful than segmentation's worst case). Most
modern systems use paging, sometimes combined with segmentation at a coarse
level (segmented paging) for protection boundaries.

> The professor made a point of saying that "segmentation fault" is a
> historical name — modern systems are almost always using paging
> underneath, but the error message stuck around from the segmentation era.

## Memory Allocation Strategies

Within a process's own heap, the allocator (e.g. `malloc`/`free` in C, or the
runtime's allocator in managed languages) needs its own strategy for handing
out chunks of the process's virtual address space:

- **First-fit** — scan from the start, use the first free block big enough.
  Fast, but tends to fragment the front of the heap over time.
- **Best-fit** — scan everything, use the smallest block that still fits.
  Less wasted space per allocation, but slower (full scan) and tends to leave
  behind lots of tiny, useless fragments.
- **Worst-fit** — use the largest available block, leaving the biggest
  possible leftover free chunk. Rarely used in practice; the idea is to keep
  leftover fragments large enough to be useful later, but it doesn't actually
  work well empirically.
- **Buddy allocation** — round allocation sizes up to the next power of two
  and recursively split/merge blocks ("buddies") of that size. Makes
  coalescing freed memory back together cheap and predictable, at the cost
  of up to ~50% internal fragmentation in the worst case. Used in the Linux
  kernel's physical page allocator.
- **Slab allocation** — pre-allocate fixed-size pools ("slabs") for objects
  of a known, frequently-allocated size (e.g. kernel data structures like
  `task_struct`). Avoids fragmentation entirely for that object type and
  skips the general-purpose allocator's overhead, at the cost of being
  specialized rather than general.

Fragmentation, in general, is the recurring villain across all of these
topics — segmentation has it externally, fixed-size paging has it
internally, and heap allocators have to actively manage it with strategies
like the ones above plus periodic compaction (relocating live objects to
squeeze out the gaps, common in garbage-collected runtimes).

## Swap Space and the Disk Tradeoff

When physical memory is full and a new page needs to be brought in, the OS
picks a victim page (using one of the replacement algorithms above) and, if
that page has been modified (the dirty bit is set), writes it out to **swap
space** on disk before reusing its frame. Clean pages (unmodified since being
loaded, e.g. code pages backed by the executable file) can just be dropped
and re-read from their original file later — no write-back needed, which is
part of why code pages are cheaper to evict than dirty heap/stack pages.

This is also why systems with very little physical RAM relative to their
workload feel painfully slow under load even without literally crashing:
every eviction risks becoming a disk write, and every subsequent re-access
risks becoming a disk read, and disk latency (even on an SSD) is orders of
magnitude higher than RAM latency. SSDs made swapping less catastrophic than
it was on spinning disks, but it's still far slower than just having enough
RAM in the first place — swap is a safety net, not a substitute for memory.

## Related

See also [[Processes and Threads]] and [[CPU Scheduling]] for how memory
management interacts with the rest of process management. [[Distributed Systems MOC]]
is unrelated but linking it here because the professor kept comparing TLB
caching to distributed cache invalidation, which is a stretch but whatever.
