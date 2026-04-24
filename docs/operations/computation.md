# Computation Protocol

Use this protocol to separate qualitative interpretation from deterministic computation.

## Principle

The assistant can propose interpretations, but numerical claims should be computed or clearly labeled as heuristic.

## Good generative interpretation tasks

LLMs are useful for:

- segmenting transcripts into scenes
- extracting verbatim evidence
- proposing Point A and Point B codes
- summarizing per-interview timelines
- drafting job stories
- naming clusters
- identifying possible contradictions and edge cases

These outputs still need evidence references and analyst review.

## Structured computation tasks

Validate these with tools whenever available:

- counts
- interview x code incidence matrices
- interview x cluster heatmaps
- Jaccard co-occurrence
- phi coefficients
- cosine similarity of code text
- hierarchical clustering

Do not do this math mentally when tools are available.

## Incidence matrices

Represent whether an interview contains a code or cluster.

Use binary values:

- `1` = present
- `0` = absent

Recommended matrices:

- interview x A-code
- interview x B-code
- interview x combined A+B code
- interview x cluster

## A<->B linking

Primary link strength:

- Jaccard co-occurrence across interviews

Secondary link checks:

- Phi coefficient when `N >= 5`
- Flag negative edges such as `phi < -0.20`
- Optional cosine similarity of code definitions or code text

## Clustering

Preferred method when tools exist:

- Ward hierarchical clustering on combined A+B incidence

If tools are unavailable:

- label clustering as `HEURISTIC`
- merge by highest Jaccard overlap
- stop at 3-5 clusters or when the best merge is below `0.30`

## Reporting computation status

Every synthesis report should state:

- clustering method used
- whether tools were used
- which calculations were computed vs. heuristic
- confidence limits
- what would raise confidence

Example:

```text
Method: Ward hierarchical clustering on combined A+B incidence.
Computation status: VERIFIED with tool-generated matrices.
Phi used: No; N=4, below the N>=5 threshold.
Confidence: Medium. Would rise with 3-5 additional interviews from the same segment.
```

## Heuristic label

Use `HEURISTIC` when the result is analyst/model judgment rather than tool-validated calculation.

Example:

```text
HEURISTIC: C02 groups A03, A06, and B04 because the evidence repeatedly links time pressure, workaround fatigue, and desire for lower-friction coordination. This should be validated with incidence counts when more interviews are available.
```
