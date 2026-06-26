# Indexing and Transactions

## Indexes

An index is an auxiliary data structure (usually a B-tree, sometimes a hash
index) that lets the database find rows matching a condition without
scanning the whole table. Speeds up reads (especially `WHERE`, `JOIN`, and
`ORDER BY` on indexed columns) at the cost of slower writes (every insert/
update/delete must also update the index) and extra storage.

A composite index on `(a, b)` can serve queries that filter on `a` alone, or
on `a` and `b` together, but generally not on `b` alone — the leftmost
column has to be used for the index to help.

## Transactions

A transaction groups multiple statements into one atomic unit — see
[[ACID Properties]] for the full guarantee. Transactions are started with
`BEGIN`, finished with `COMMIT`, or rolled back with `ROLLBACK` if something
goes wrong partway through.

## Isolation levels

From weakest to strongest, each preventing more concurrency anomalies but
costing more locking/overhead:
1. **Read Uncommitted** — can see uncommitted writes from other transactions
   (dirty reads). Rarely used.
2. **Read Committed** — only sees committed data, but a second read in the
   same transaction can see different data (non-repeatable read).
3. **Repeatable Read** — same query re-run in the same transaction returns
   the same rows, but new rows matching the condition can still appear
   (phantom reads).
4. **Serializable** — transactions behave as if run one at a time. Strongest,
   slowest.

> Postgres default is Read Committed. MySQL's InnoDB default is Repeatable
> Read. Got this mixed up on the practice exam.

Related: [[ACID Properties]], [[SQL Normalization]], [[Database Exam Prep]]
