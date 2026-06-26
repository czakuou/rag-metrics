# Linear Algebra — Matrix Operations

Notes from my math elective, not CS, but putting it in the same vault
because Obsidian doesn't care and I don't want two separate vaults.

## Matrix multiplication

For matrices A (m x n) and B (n x p), the product AB is an (m x p) matrix
where each entry is the dot product of a row of A and a column of B. Note
the inner dimensions must match (A's columns = B's rows), and matrix
multiplication is **not commutative** in general: AB != BA.

## Determinant

A scalar value computed from a square matrix that tells you, among other
things, whether the matrix is invertible (determinant != 0) and how the
matrix scales area/volume under the linear transformation it represents. For
a 2x2 matrix `[[a, b], [c, d]]`, the determinant is `ad - bc`.

## Eigenvalues and eigenvectors

For a square matrix A, an eigenvector v satisfies `Av = lambda*v` for some
scalar lambda (the eigenvalue) — applying the transformation only scales the
vector, doesn't change its direction. Useful for understanding the
"natural axes" of a transformation, and shows up in PCA (mentioned in my
[[Machine Learning — Notes]] elective, of all places — small world).

## Matrix inverse

A^-1 exists only if A is square and its determinant is non-zero. `A * A^-1
= I` (identity matrix). Used to solve linear systems `Ax = b` as
`x = A^-1 * b`, though in practice numerical methods (Gaussian elimination,
LU decomposition) are used instead of literally computing the inverse, for
stability and performance reasons.

> Professor's pet peeve: never actually compute the inverse to solve a
> linear system in real code, use a solver. Apparently a lot of people lose
> points on this in the engineering programs.
