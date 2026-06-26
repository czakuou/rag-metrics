# Sorting Algorithms Comparison

Table version of the sorting section from [[Algorithms Cheat Sheet]]. Making
this because I kept mixing up which ones are stable.

| Algorithm      | Best       | Average    | Worst      | Space    | Stable |
|----------------|------------|------------|------------|----------|--------|
| Bubble Sort    | O(n)       | O(n^2)     | O(n^2)     | O(1)     | Yes    |
| Insertion Sort | O(n)       | O(n^2)     | O(n^2)     | O(1)     | Yes    |
| Selection Sort | O(n^2)     | O(n^2)     | O(n^2)     | O(1)     | No     |
| Merge Sort     | O(n log n) | O(n log n) | O(n log n) | O(n)     | Yes    |
| Quicksort      | O(n log n) | O(n log n) | O(n^2)     | O(log n) | No     |
| Heap Sort      | O(n log n) | O(n log n) | O(n log n) | O(1)     | No     |
| Timsort        | O(n)       | O(n log n) | O(n log n) | O(n)     | Yes    |

A few notes on "why":

- Quicksort's worst case (O(n^2)) happens when the pivot choice is bad every
  time, e.g. always picking the first element on an already-sorted array.
  Randomized pivot selection avoids this in practice.
- Merge sort is stable because when merging two halves, you always take from
  the left half first on ties, preserving original relative order.
- Timsort (used by Python's `sorted()` and Java's `Arrays.sort()` for objects)
  is a hybrid of merge sort and insertion sort, optimized for real-world data
  which is often partially sorted already.

> Why does stability even matter? If you're sorting a list of (name, age)
> tuples by age, stable sort guarantees people with the same age stay in
> their original relative order. Matters for multi-key sorts.

Related: [[Algorithms Cheat Sheet]], [[Binary Search Implementation]]
