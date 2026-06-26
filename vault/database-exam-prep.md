# Database Exam Prep

Made this as flashcards the night before the midterm. Worked pretty well,
keeping the format for the final too.

**Q: What does ACID stand for?**
A: Atomicity, Consistency, Isolation, Durability. See [[ACID Properties]]
for the full breakdown of each.

**Q: What's the difference between a primary key and a unique key?**
A: Both enforce uniqueness, but a table can have only one primary key (which
also implies NOT NULL) and multiple unique keys. Unique keys can allow NULL
values (depending on the database).

**Q: What is 3NF and why does it matter?**
A: Third Normal Form requires the table to be in 2NF with no transitive
dependencies — non-key columns must depend only on the primary key, not on
other non-key columns. It matters because it eliminates redundancy and the
update/insertion/deletion anomalies that come with it. See
[[SQL Normalization]].

**Q: What is a transaction?**
A: A group of one or more SQL statements executed as a single atomic unit —
either all of them succeed and commit, or none of them take effect (and the
transaction rolls back).

**Q: Name the four SQL transaction isolation levels, from weakest to
strongest.**
A: Read Uncommitted, Read Committed, Repeatable Read, Serializable. See
[[Indexing and Transactions]] for what anomaly each one prevents.

**Q: What's a dirty read?**
A: When a transaction reads data written by another transaction that hasn't
committed yet — and might be rolled back, making the read invalid.

**Q: Why use an index, and what's the tradeoff?**
A: Indexes speed up reads (lookups, joins, sorts on indexed columns) by
avoiding a full table scan, but slow down writes (every insert/update/delete
also has to update the index structure) and use extra storage.

**Q: What's the difference between a clustered and non-clustered index?**
A: A clustered index determines the physical storage order of rows in the
table — there can be only one per table (often the primary key). A
non-clustered index is a separate structure pointing back to the row's
location; a table can have many.

**Q: What's a foreign key and what does it enforce?**
A: A column (or set of columns) that references the primary key of another
table, enforcing referential integrity — you can't insert a row referencing
a non-existent parent row, and (depending on the constraint) you can't
delete a parent row that's still referenced by children without explicitly
handling the cascade.

**Q: Why would you denormalize a database?**
A: To improve read performance for read-heavy workloads by reducing the
number of joins needed, accepting more redundancy and more complex/careful
writes as the tradeoff. See the "When to denormalize" section in
[[SQL Normalization]].

Related: [[ACID Properties]], [[SQL Normalization]], [[Indexing and Transactions]]
