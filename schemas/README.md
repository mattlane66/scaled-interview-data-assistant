# JSON schemas

These Draft 2020-12 schemas define the canonical JSON shape for core machine-facing artifacts.
Cross-file ownership, alias, and completeness rules are enforced by `scripts/validate_registry.py`.

- `evidence-bank.schema.json`
- `codebook.schema.json`
- `evidence-mappings.schema.json`
- `sources.schema.json`
- `links.schema.json`
- `checkpoint.schema.json`

Checkpoint export and restore also apply referential-integrity checks in
`scripts/checkpoint_validation.py`; JSON Schema alone cannot express all ownership, completeness,
and alias rules.

CSV, XLSX, JSONL, YAML, and single-table Markdown inputs are normalized into the same logical fields
by the Python tooling.
