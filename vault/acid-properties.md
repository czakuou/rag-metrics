# ACID Properties

The four guarantees a database transaction is supposed to provide.

- **Atomicity** — a transaction either fully completes or has no effect at
  all. No partial writes left behind if something fails halfway through.
- **Consistency** — a transaction can only bring the database from one valid
  state to another valid state, respecting all constraints (foreign keys,
  unique constraints, etc.). Note: this is a different "consistency" than the
  one in [[CAP Theorem]] / [[Consistency Models]] — easy to conflate on exams.
- **Isolation** — concurrent transactions shouldn't interfere with each
  other, as if they ran one at a time. In practice this is relaxed by
  isolation levels (read uncommitted, read committed, repeatable read,
  serializable) for performance.
- **Durability** — once a transaction commits, it stays committed even if the
  system crashes immediately after (usually via write-ahead logging).

Related: [[SQL Normalization]], [[Indexing and Transactions]], [[Database Exam Prep]]
