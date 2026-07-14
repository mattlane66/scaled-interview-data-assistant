# Registry and checkpoint protocol

Stable registries keep long studies auditable and resumable.

## IDs

- Interview: `I01`, `I02`, …
- Decision episode: `D01`, `D02`, …
- Segment: `S01`, `S02`, … per interview
- Evidence: `E001`, `E002`, …
- Point A code: `A01`, `A02`, …
- Point B code: `B01`, `B02`, …
- Cluster: `C01`, `C02`, …

Never renumber an accepted ID. A merge creates an alias to the canonical ID. A split creates new IDs
and records which earlier artifacts require backcoding.

## Evidence provenance

Every evidence row includes its interview, decision episode, segment, source file, source location,
and atomic verbatim excerpt. Stable IDs are not enough if a reviewer cannot locate the original
passage.

## Codebook maintenance

For each batch:

1. reuse an existing code only when its definition fits;
2. add a code when material evidence does not fit;
3. record merges, splits, renames, and reasons;
4. backcode earlier episodes after a material codebook change;
5. periodically review uncoded and contradictory evidence to reduce first-batch anchoring.

## Diff log

Record additions, merges, splits, renames, recodes, reclusters, the reason, and the analyst who
approved the change.

## Checkpoints

Export a checkpoint after each reviewed batch. Version 1 checkpoints include:

- analysis metadata and timestamp;
- interview, episode, and segment indexes;
- evidence bank and codebook;
- evidence-to-code mappings;
- cluster assignments and alias map;
- latest diff log.

On resume, validate the checkpoint-derived tables, preserve every accepted ID, continue numbering
from the highest ID, and record what was restored. A checkpoint is a state transfer, not proof that
the underlying interpretations are correct.

```bash
python scripts/import_checkpoint.py \
  --checkpoint outputs/CHECKPOINT.json \
  --output-dir data/restored
```

Run registry validation on the restored tables before continuing.
