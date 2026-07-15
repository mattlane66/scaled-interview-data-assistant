# Registry and checkpoint protocol

Stable registries keep long studies auditable and resumable.

## IDs

- Source: `SRC01`, `SRC02`, …
- Interview: `I01`, `I02`, …
- Decision episode: `D01`, `D02`, …
- Segment: `S01`, `S02`, … per interview
- Evidence: `E001`, `E002`, …
- Point A code: `A01`, `A02`, …
- Point B code: `B01`, `B02`, …
- A↔B link: `L001`, `L002`, …
- Cluster: `C01`, `C02`, …

Never renumber an accepted ID. A merge creates an alias to the canonical ID. A split creates new IDs
and records which earlier artifacts require backcoding.

## Evidence provenance

Register every source and whether it was read in full, partially read, or unreadable. Every evidence
row includes its source ID, interview, decision episode, segment, source file, source location,
speaker, evidence type, and atomic verbatim excerpt. Stable IDs are not enough if a reviewer cannot
locate the original passage or determine what the study actually covered.

## A↔B link maintenance

Create an `L###` record only after reviewing the relationship within a decision episode. Each link
names one A-code and one B-code, labels the basis `EXPLICIT` or `INFERRED`, cites episode-owned
evidence, and states the rationale. Cross-episode co-occurrence can prioritize review; it does not
create a link record.

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

Export a checkpoint after each reviewed batch. Version 1.1 checkpoints include:

- analysis metadata and timestamp;
- source, interview, episode, and segment indexes;
- evidence bank and codebook;
- evidence-to-code mappings;
- reviewed A↔B links;
- cluster assignments and alias map;
- decision log;
- latest diff log.

Export and restore apply the checkpoint JSON Schema and cross-registry checks for unique IDs,
ownership, references, link evidence, aliases, and complete cluster assignments. Version 1.0
checkpoints are migrated additively; missing coverage or evidence-type facts remain unknown. On
resume, preserve every accepted ID, continue numbering from the highest ID, and record what was
restored. A checkpoint is a state transfer, not proof that the underlying interpretations are
correct.

```bash
python scripts/import_checkpoint.py \
  --checkpoint outputs/CHECKPOINT.json \
  --output-dir data/restored
```

The importer rejects invalid checkpoints before writing any restored table. Run registry validation
again after adding or changing artifacts.
