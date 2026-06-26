# Data Structures

Overview note, mostly so I have somewhere to link from the algorithms notes.

## Linked Lists

A linked list is a sequence of nodes where each node holds a value and a
pointer to the next node (and, for doubly linked lists, the previous node
too). Insertion/deletion at the head is O(1), but random access is O(n)
since you have to walk the list.

## Trees

A tree is a hierarchical structure with a root node and child nodes, no
cycles. A binary search tree (BST) keeps left children smaller and right
children larger than the parent, giving O(log n) average lookup — but O(n)
worst case if it degenerates into a linked list (unbalanced). Self-balancing
variants like AVL trees and red-black trees fix this by rebalancing on
insert/delete.

## Hash Maps

A hash map stores key-value pairs using a hash function to compute an index
into a backing array (the "bucket"). Average case O(1) lookup/insert/delete,
but collisions degrade this. Common collision strategies: chaining (each
bucket is a linked list) or open addressing (probe for the next free slot).

## Heaps

A heap is a tree-based structure satisfying the heap property: in a min-heap,
every parent is smaller than its children (max-heap is the reverse). Used to
implement priority queues. Insert and extract-min are both O(log n).

Related: [[Algorithms Cheat Sheet]], [[Binary Search Implementation]]
