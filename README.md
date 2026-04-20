# Scaled Interview Data Assistant

Analyze transcripts into A2B/JTBD synthesis and explain the method and LLM workflow clearly.

This repo packages a qualitative synthesis assistant around A2B, JTBD, and framing. It is meant to turn transcripts, notes, and observations into evidence-traceable analysis: per-interview cards, shared codebooks, cross-interview A↔B clusters, forces analysis, fit criteria, and report-ready synthesis.

## What is in this repo

- `prompt/custom-gpt.md` — the core assistant instructions
- `docs/methodology/` — concise notes on A2B and framing
- `docs/output/example-report-structure.md` — the target report shape
- `templates/` — interview card and synthesis report templates
- `knowledge/` — source PDFs used to ground the method

## What the assistant does

The workflow is designed to stay anchored in real past behavior, bounded context, causal reasoning, and desired progress rather than jumping to solution ideas.

Typical outputs:

- per-interview A2B cards
- evidence banks with stable IDs
- Point A and Point B codebooks
- interview × code matrices
- A↔B link analysis
- adjusted job story clusters
- forces and fit criteria
- decision-useful synthesis

## Core method in one pass

1. Identify the specific struggling moment.
2. Separate Point A from Path Y and Path X.
3. Clarify the current baseline result.
4. Surface Point B as desired progress, not a feature.
5. Capture Push, Pull, Anxiety, and Inertia.
6. Synthesize across interviews without losing evidence traceability.

## Repo layout

```text
.
├── README.md
├── .gitignore
├── prompt/
│   └── custom-gpt.md
├── docs/
│   ├── methodology/
│   │   ├── a2b.md
│   │   └── framing.md
│   └── output/
│       └── example-report-structure.md
├── templates/
│   ├── interview-card.md
│   └── synthesis-report.md
└── knowledge/
    ├── A2B.pdf
    ├── Example Report.pdf
    └── The Art & Science of Framing.pdf
```

## Using this with Claude Code, Codex, Gemini Code, GPT, or other LLM tools

The repo is intentionally tool-agnostic.

### Minimal setup

1. Give the model `prompt/custom-gpt.md` as the main operating instruction.
2. Add the files in `docs/`, `templates/`, and `knowledge/` as reference context.
3. Add your transcripts or notes in a `data/` folder.
4. Ask the model to work in one of four modes:
   - `GUIDE`
   - `INGEST`
   - `SINGLE`
   - `SYNTHESIZE`

### Practical mapping by tool

- **ChatGPT / custom GPT / project instructions**: use `prompt/custom-gpt.md` as the main behavior spec and attach the docs/templates as knowledge.
- **Claude Code**: keep the prompt file in-repo and point Claude to it as the synthesis operating guide; use the templates as output targets.
- **Codex / GPT in repo workflows**: include the prompt file in the working tree and explicitly tell the model to follow it while reading files from `data/` and writing outputs into `outputs/`.
- **Gemini Code / Gemini app workflows**: paste or attach `prompt/custom-gpt.md`, then attach the method docs and templates so the model has the frame definitions and output structure.
- **Any other agentic coding tool**: treat this repo as the source of truth for method, prompt, and output shape.

### Suggested working pattern

For 1–3 interviews:

- run `SINGLE` on each interview first
- produce one interview card per interview
- then run a synthesis pass

For larger studies:

- ingest interviews incrementally
- maintain stable IDs for interviews, segments, evidence, codes, and clusters
- synthesize from cards rather than from raw transcripts every turn

## Suggested folders to add

```text
data/
outputs/
scripts/
```

Examples:

- `data/transcripts/`
- `data/notes/`
- `outputs/interview-cards/`
- `outputs/synthesis/`
- `scripts/cluster-analysis.ipynb`

## Suggested first prompt

```text
Use the files in this repo as the operating method.
Work in INGEST mode.
Build the registry structure first.
Then process the transcript in data/transcripts/interview-01.md into an interview card.
Do not invent quotes, numbers, or findings.
Label important claims as VERIFIED, INFERRED, or SPECULATIVE.
```

## Notes

- This repo includes the user-authored behavior spec and supporting method files.
- It does not include hidden platform system instructions.
- No license is included yet.
