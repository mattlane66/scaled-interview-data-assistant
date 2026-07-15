# Data contracts

The deterministic scripts accept CSV, XLSX, JSON, JSONL, YAML, or a Markdown file containing one
table. Use JSON or CSV for machine-facing artifacts. Multi-table Markdown reports are human-facing
and should not be used as pipeline input.

Draft 2020-12 JSON schemas for the core artifacts live in [`schemas/`](../../schemas/). The registry
validator adds cross-file rules that JSON Schema alone cannot express.

## Source coverage registry

Required fields: `source_id`, `source`, `coverage`. Coverage is `FULL`, `PARTIAL`, `UNREADABLE`, or
`UNKNOWN` for migrated legacy data. Evidence rows must reference the matching source ID and path.

## Interview registry

Required fields: `interview`, `descriptor`.

## Decision-episode registry

Required fields: `episode`, `interview`, `descriptor`.

One interview may contain several episodes. Each episode belongs to one interview.

## Segment registry

Required fields: `interview`, `segment`, `location`.

Segment IDs may repeat in different interviews; the pair `(interview, segment)` is unique.

## Evidence bank

Required fields:

| Field | Meaning |
|---|---|
| `evidence` | Stable `E###` ID |
| `source_id` | Owning `SRC##` |
| `interview` | Owning `I##` |
| `episode` | Owning `D##` |
| `segment` | Source `S##` |
| `source` | Source filename or immutable source identifier |
| `source_location` | Timestamp, line, page, or speaker-turn range |
| `speaker` | Participant, interviewer, or observer label |
| `evidence_type` | Event/behavior, state, observation, interpretation, aspiration, generalization, hypothetical, interviewer statement, or unknown |
| `verbatim_excerpt` | Atomic passage copied without substantive rewriting |
| `tags` | Optional descriptive tags |
| `note` | Optional analyst interpretation |

Typographic normalization must not change meaning. If an excerpt is noncontiguous, store separate
evidence rows.

Pass `--source-root` to validation when local source files are available. The validator collapses
whitespace and confirms that each excerpt occurs in its named file; it rejects paths that escape the
declared root.

## Codebook

Required fields: `code`, `definition`. Optional field: `family`, which must match the `A` or `B`
prefix.

## Evidence-to-code mapping

Required fields: `evidence`, `interview`, `episode`, `a_codes`, `b_codes`.

Use comma-separated code IDs in table cells. The validator rejects malformed codes, wrong-family
codes, duplicate evidence rows, missing codes, and ownership mismatches.

## Reviewed A↔B link registry

Required fields: `link`, `episode`, `a_code`, `b_code`, `basis`, `evidence`, and `rationale`.
`basis` is `EXPLICIT` or `INFERRED`. Supporting evidence must belong to the same episode. One row
represents one reviewed episode/A/B relationship; computed co-presence does not create this record.

## Cluster assignments

Required fields: `episode` and `cluster` when decision episode is the analysis unit. Cluster IDs are
registry identifiers, not ordinal rankings. Every included unit must appear once; unknown and
duplicate units fail validation.

## Alias map

Required fields: `alias`, `canonical`. Aliases must stay within the same ID family and may not form
cycles.
