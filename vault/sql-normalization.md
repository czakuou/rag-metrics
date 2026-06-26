# SQL Normalization

Normal forms reduce data redundancy and avoid update anomalies by organizing
tables around functional dependencies.

## 1NF (First Normal Form)

Every column holds atomic values (no lists/arrays packed into one column),
and each row is uniquely identifiable (has a primary key).

## 2NF (Second Normal Form)

Must be in 1NF, plus: no partial dependency on a composite key. Every
non-key column must depend on the *whole* primary key, not just part of it.
Only relevant when the table has a composite (multi-column) primary key.

## 3NF (Third Normal Form)

Must be in 2NF, plus: no transitive dependency — non-key columns must depend
only on the primary key, not on other non-key columns. E.g. if
`student_id -> zip_code -> city`, then `city` depends transitively on
`student_id` through `zip_code`, violating 3NF.

## Why normalize?

Reduces redundancy (don't repeat the same city name in every row) and
prevents anomalies:
- **Update anomaly** — changing one fact requires updating multiple rows
- **Insertion anomaly** — can't add a fact without also having unrelated data
- **Deletion anomaly** — deleting a row accidentally loses unrelated facts

## When to denormalize

Sometimes you deliberately denormalize (add redundancy back) for read
performance, trading write complexity and storage for fewer joins. Common in
analytics/reporting tables and read-heavy systems.

Related: [[ACID Properties]], [[Indexing and Transactions]], [[Database Exam Prep]]
