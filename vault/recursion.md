# Recursion

Notes from the lecture where we were *supposed* to cover recursive
algorithms but the professor spent basically the whole hour on the call
stack instead because half the class was confused about why recursion blows
up memory. Writing down what actually got covered.

## The call stack

Every function call pushes a new **stack frame** onto the call stack. A
stack frame holds the function's local variables, its parameters, and the
return address (where execution should resume once this call returns). When
the function returns, its frame is popped off.

A recursive function calls itself, so each recursive call adds another stack
frame on top of the previous one — they don't get reused or merged, each
call gets its own frame with its own copy of the local variables.

```python
def countdown(n):
    if n == 0:
        return
    print(n)
    countdown(n - 1)
```

Calling `countdown(3)` pushes a frame for `countdown(3)`, which calls
`countdown(2)` (pushing another frame on top), which calls `countdown(1)`
(another frame), which calls `countdown(0)` (another frame), which returns —
popping frames one at a time back down to the original call.

## Stack overflow

Each stack frame takes up real memory, and the call stack has a fixed size
limit (set by the OS/runtime). If recursion goes too deep — usually because
there's no base case, or the base case is never reached — you run out of
stack space and get a **stack overflow**. This crashes the program (or
raises `RecursionError` in Python, which actually checks recursion depth
explicitly at ~1000 calls by default rather than waiting for a real
hardware stack overflow).

```python
def infinite():
    return infinite()  # no base case — guaranteed stack overflow
```

> This is exactly why an unbounded recursive function is way more dangerous
> than an unbounded loop — a loop just runs forever using the same constant
> stack space, but unbounded recursion eats memory linearly with depth until
> it crashes.

## Tail calls (and why Python doesn't help you here)

Some languages optimize "tail calls" — when the recursive call is the very
last thing the function does — by reusing the current stack frame instead of
pushing a new one, making deep tail recursion run in constant stack space.
Python deliberately does **not** do this (Guido has said so explicitly), so
even tail-recursive Python functions will still blow the stack at depth.
Languages like Scheme guarantee tail call optimization.

## Why this matters for actual recursive algorithms

When you do write recursive algorithms (covered briefly — see
[[Algorithms Cheat Sheet]] for the actual algorithm list), the call stack
depth is bounded by how deep the recursion goes, which for something like
[[Binary Search Implementation|recursive binary search]] is O(log n) — safe.
But naive recursive Fibonacci or unguarded tree recursion can blow up fast
in both time and stack depth.

Related: [[Binary Search Implementation]], [[Algorithms Cheat Sheet]]
