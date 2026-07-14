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

The primary descriptive signal is Jaccard co-occurrence across decision episodes. The output also
includes support counts and phi where mathematically defined. Low-support results are flagged.

These values describe association, not causation, importance, market size, or prevalence in a wider
population. Semantic cosine between code definitions is only a discovery aid; it is not behavioral
evidence.

## Clustering

The default implementation uses average-linkage hierarchical clustering over Jaccard distance on
binary A+B incidence. This is exploratory grouping, not a discovered ground truth.

- The analyst chooses and records the target cluster count.
- The pipeline reports an exploratory silhouette score when defined.
- Previous assignments can be supplied to preserve stable `C##` IDs by membership overlap.
- Every cluster must be reviewed against its evidence, competing links, and edge cases.

Run sensitivity checks with nearby cluster counts when the grouping affects an important decision.
If the interpretation changes materially, report that instability.

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
