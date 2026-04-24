# Registry and Checkpoint Protocol

Use this protocol to keep qualitative synthesis work stable, auditable, and resumable across long sessions.

## Persistent registries

Maintain stable IDs across turns. Never renumber.

- Interview Index: `I01`, `I02`, ... with a short descriptor
- Segment Index: `S01`, `S02`, ... per interview, with timestamp or speaker-turn range when available
- Evidence Bank: `E001`, `E002`, ... atomic, verbatim-only excerpts
- Codebook A-codes: `A01`, `A02`, ... for Point A contexts, forces, and struggles
- Codebook B-codes: `B01`, `B02`, ... for Point B progress
- Clusters: `C01`, `C02`, ...
- Alias map: records merges as alias -> canonical

## Evidence bank rows

Each evidence row should include:

| Field | Description |
|---|---|
| E# | Stable evidence ID |
| I# | Interview ID |
| S# | Segment ID |
| Verbatim excerpt | Atomic quote copied exactly from the source |
| Tags | Push, Pull, Anxiety, Inertia, Path X/Y, baseline, desired, constraint, workaround, trigger |
| Note | One-line analyst note |

## Diff Log

Every working turn should include a brief Diff Log with:

- adds
- merges
- renames
- re-codes
- re-clusters
- why the change was made

## Merge handling

When merging IDs, preserve the old identifier in the alias map.

Example:

```text
Alias map:
- A07 -> A03
- C04 -> C02
```

Do not delete the historical ID from prior artifacts. Mark it as an alias so older references remain understandable.

## Checkpoint export

After 4+ interviews, a long transcript batch, or a long chat session, offer a checkpoint that can be pasted back later.

The checkpoint should contain:

- registry
- interview index
- segment index
- evidence bank
- codebook
- E -> code mappings
- clusters
- alias maps
- latest Diff Log

## Resume command

Resume from a checkpoint when the user says:

```text
Resume from checkpoint.
```

On resume:

1. Reconstruct the registries.
2. Preserve all existing IDs.
3. Continue numbering from the highest existing ID.
4. Include a Diff Log confirming what was restored and what changed.
