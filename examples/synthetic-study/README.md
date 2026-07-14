# Synthetic multi-interview study

This original synthetic dataset demonstrates the complete repository workflow without exposing real
participant data.

## Contents

- `transcripts/` — three short source interviews
- `interviews.json`, `episodes.json`, `segments.json` — stable registries
- `evidence_bank.json` — source-located verbatim excerpts
- `codebook.json` — reviewed A/B definitions
- `evidence_mappings.json` — evidence ownership and coding
- `synthesis_report.md` — audited report example

## Run

From the repository root:

```bash
python scripts/run_pipeline.py \
  --interviews examples/synthetic-study/interviews.json \
  --episodes examples/synthetic-study/episodes.json \
  --segments examples/synthetic-study/segments.json \
  --source-root examples/synthetic-study \
  --evidence examples/synthetic-study/evidence_bank.json \
  --codebook examples/synthetic-study/codebook.json \
  --mappings examples/synthetic-study/evidence_mappings.json \
  --report examples/synthetic-study/synthesis_report.md \
  --clusters 2 \
  --output-dir outputs/synthetic-study
```

The transcript-to-evidence and evidence-to-code steps remain interpretive and require human review.
The command validates and computes only after those artifacts exist.
