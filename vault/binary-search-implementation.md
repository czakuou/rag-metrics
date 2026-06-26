# Binary Search Implementation

Lab 4 wanted us to implement this from scratch instead of using `bisect`.
Writing up the clean version here plus the bugs I hit along the way.

## The algorithm

Binary search works on a sorted array by repeatedly halving the search space:
compare the target to the middle element, and discard the half that can't
contain the target.

```python
def binary_search(arr: list[int], target: int) -> int:
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1  # not found
```

## Recursive version

```python
def binary_search_recursive(arr: list[int], target: int, low: int = 0, high: int | None = None) -> int:
    if high is None:
        high = len(arr) - 1
    if low > high:
        return -1
    mid = (low + high) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, high)
    else:
        return binary_search_recursive(arr, target, low, mid - 1)
```

## Complexity analysis

Each step halves the search space, so the number of steps to reduce n
elements down to 1 is log2(n). This gives O(log n) time complexity.

- Time: O(log n)
- Space: O(1) iterative, O(log n) recursive (call stack — see [[Recursion]])

## Common mistakes

```
# Off-by-one in the loop condition
while low < high:   # WRONG, should be low <= high
    ...
```

This was literally my bug in lab 4 — using `<` instead of `<=` means you skip
checking the case where `low == high`, which is a valid single-element range
you still need to check.

Another classic mistake: computing `mid = (low + high) // 2` can overflow in
languages with fixed-size integers (not really a problem in Python, but it's
a classic interview gotcha in Java/C++). The fix is
`mid = low + (high - low) // 2`.

> TA docked a point on lab 4 for forgetting to handle empty arrays. `len(arr)
> == 0` means `high = -1` immediately, loop never runs, returns -1. Actually
> fine? I think I just panicked.

See [[Algorithms Cheat Sheet]] for where this fits among other search/sort
algorithms, and [[Sorting Algorithms Comparison]] for sorting since binary
search requires a sorted array to begin with.
