# Machine Learning — Notes

Elective course, not core CS, taking sparser notes than for my required
classes. Will fill in the rest before the exam (narrator: did not).

## Supervised Learning

Learning a mapping from inputs to known outputs (labels) using a labeled
training set. Includes classification (discrete labels, e.g. spam/not spam)
and regression (continuous output, e.g. predicting a price). The model is
evaluated against a held-out test set to estimate generalization.

Examples covered: linear regression, logistic regression, decision trees,
k-nearest neighbors.

## Unsupervised Learning

No labels — the model finds structure in the data on its own. Clustering
(grouping similar points, e.g. k-means) and dimensionality reduction (e.g.
PCA, projecting high-dimensional data into fewer dimensions while
preserving as much variance as possible) are the two big categories we
covered.

> k-means is sensitive to initial centroid placement — bad luck on init can
> get you stuck in a worse local optimum. Run it multiple times with
> different seeds and keep the best result.

## Reinforcement Learning

## TODO

## Related

Not really connected to the rest of my CS notes vault — this is its own
elective track. No links out on purpose.
