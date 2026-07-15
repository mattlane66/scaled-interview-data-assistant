# Computation protocol

Computation supports qualitative judgment; it does not replace it. The assistant proposes
interpretations. The scripts validate structure and calculate reproducible descriptive signals.

## Analysis unit

Use decision episode (`D##`) by default. Interview-level analysis is appropriate only when every
interview contains exactly one bounded decision episode. Otherwise, interview-level co-presence can
create false A↔B associations.

## Incidence matrices

The pipeline builds binary unit × code matrices:

- decision episode × A-code;
- decision episode × B-code;
- decision episode × combined A+B code;
- decision episode × cluster.

`1` means the reviewed evidence for that unit contains the code; `0` means it does not. A zero does
not prove the participant lacked the need—it may reflect interview coverage.

## A↔B association

The primary A↔B artifact is the reviewed `L###` link registry. Each record says that a named
A-code and B-code are explicitly or inferentially linked within one decision episode, cites the
supporting evidence, and records the analyst's rationale.

Computed co-occurrence is secondary. The association output includes the full 2×2 counts (`n11`,
`n10`, `n01`, `n00`), Jaccard, and descriptive phi. Phi is suppressed when there are fewer than ten
units or fewer than the configured number of co-occurring units. Negative-edge flags are disabled
unless the analyst explicitly confirms that zeros represent assessed nonoccurrence rather than
missing interview coverage.

These values describe association, not causation, importance, market size, or prevalence in a wider
population. Semantic cosine between code definitions is only a discovery aid; it is not behavioral
evidence.

## Clustering

The default implementation uses average-linkage hierarchical clustering over Jaccard distance on
binary A+B incidence. This is exploratory grouping, not a discovered ground truth.

- `--clusters auto` evaluates supported candidate counts and records the actual result.
- `--clusters 1` preserves one coherent group; `--clusters none` skips grouping.
- An explicit positive integer requests a candidate count, but identical profiles can still yield
  one actual cluster. The checkpoint records the distinct assignments, never the request.
- The pipeline reports an exploratory silhouette score when defined.
- Previous assignments can be supplied to preserve stable `C##` IDs by membership overlap.
- Every cluster must be reviewed against its evidence, competing links, and edge cases.

Do not force a partition when no useful separation is supported. Run sensitivity checks with nearby
cluster counts when the grouping affects an important decision. If the interpretation changes
materially, report that instability.

## Reporting requirements

Every report must state:

- analysis unit;
- clustering or grouping method;
- computed versus heuristic steps;
- support counts and low-support limitations;
- that code association is not causal;
- analyst review status;
- contradictions and evidence gaps.

Frequency is not importance. A rare episode can still reveal a severe constraint or strategically
important job.
