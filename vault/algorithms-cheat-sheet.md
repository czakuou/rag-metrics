# Algorithms Cheat Sheet

Quick reference before the exam. Not pretty, just need this memorized.

## Time complexities (common)

- O(1) — constant: array index, hash map lookup (avg)
- O(log n) — binary search, balanced BST ops
- O(n) — linear scan, single loop
- O(n log n) — merge sort, heap sort, quicksort (avg)
- O(n^2) — bubble sort, insertion sort, nested loops
- O(2^n) — naive recursive Fibonacci, subset generation
- O(n!) — permutations, brute-force TSP

## Sorting algorithms

- Bubble sort — O(n^2), stable, in-place, basically never used in practice
- Insertion sort — O(n^2) worst, O(n) best (nearly sorted), good for small n
- Merge sort — O(n log n) always, stable, needs O(n) extra space
- Quicksort — O(n log n) avg, O(n^2) worst (bad pivot choice), in-place
- Heap sort — O(n log n) always, in-place, not stable
- See [[Sorting Algorithms Comparison]] for the full table

## Searching

- Linear search — O(n), no precondition on data
- Binary search — O(log n), requires sorted array
- See [[Binary Search Implementation]] for code

## Graph algorithms

- BFS — shortest path in unweighted graph, O(V + E), uses a queue
- DFS — explore as deep as possible first, O(V + E), uses a stack/recursion
- Dijkstra — shortest path with non-negative weights, O((V + E) log V) with
  a priority queue
- Bellman-Ford — shortest path, handles negative weights, O(V * E)
- A* — Dijkstra + heuristic, used in pathfinding/games
- Topological sort — ordering of DAG nodes, O(V + E)
- Union-Find — for cycle detection and connectivity, near O(1) amortized
  with path compression + union by rank

## Tree traversals

1. Pre-order — root, left, right
2. In-order — left, root, right (gives sorted order for BST)
3. Post-order — left, right, root
4. Level-order — BFS on a tree

## Dynamic programming patterns

- 0/1 Knapsack — O(n * W)
- Longest common subsequence — O(n * m)
- Longest increasing subsequence — O(n log n) with binary search trick
- Edit distance — O(n * m)
- Coin change — O(n * amount)

## Big-O cheat reminders

- Always drop constants: O(3n) = O(n)
- Always drop lower-order terms: O(n^2 + n) = O(n^2)
- Nested loops over same input usually multiply: O(n) * O(n) = O(n^2)
- Recursive calls: use the recurrence relation, e.g. T(n) = 2T(n/2) + O(n)
  gives O(n log n) by the master theorem

See [[Data Structures]] for the structures these algorithms operate on.
