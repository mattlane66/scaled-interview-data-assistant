# Scaled Interview Data Assistant

Analyze transcripts into A2B/JTBD synthesis and explain the method and LLM workflow clearly.

This repo packages a qualitative synthesis assistant around A2B, JTBD, and framing. It is meant to turn transcripts, notes, and observations into evidence-traceable analysis: per-interview cards, shared codebooks, cross-interview A↔B clusters, forces analysis, fit criteria, and report-ready synthesis.

## What is in this repo

- `prompt/custom-gpt.md` — the core assistant instructions
- `docs/methodology/` — concise notes on A2B and framing
- `docs/output/example-report-structure.md` — the target report shape
- `templates/` — interview card and synthesis report templates
- `knowledge/` — source PDFs used to ground the method
- `examples/` — worked examples from raw transcript to processed artifact

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

## Where framing starts

Before using the six interview questions, start with a demand-side learning goal.

A strong learning goal should not start with what you think people should want. It should start with what people are already doing now, why they are doing it that way, what workarounds or compensating behaviors they use, and what causes them to switch paths.

Good starting questions look like:

- How are people currently doing [x]?
- How are they currently doing [y]?
- How are they currently doing [z]?
- What caused them to recently buy, adopt, or switch to something?

This keeps the work anchored in real past behavior inside a bounded context rather than using interviews to validate an imagined solution.

## The physics of the opportunity

Before imagining solutions, identify where the real energy exists in the system:

- the struggle
- the moment
- the motion

That means observing when and why people shift paths. The goal is to uncover the causal structure of demand, not just collect opinions.

## Broad line of inquiry

Use these six questions to uncover Point A, Path Y, Path X, and Point B:

1. **When did you first start using or buying Path X?**
   - Anchors the moment of adoption.
2. **When was the first time you thought, “Maybe I need something like Path X”?**
   - Reveals the earlier trigger and separates the first thought from the eventual action.
3. **What were you doing in the period before you adopted Path X?**
   - Surfaces the prior behavior, workaround, or substitute path.
4. **Why didn’t you just continue doing that? What finally tipped you to adopt Path X?**
   - Exposes the forces pushing them away from the old way and pulling them toward the new one.
5. **What was bad or frustrating about that?**
   - Helps identify the core struggle worth resolving.
6. **Before using Path X, what were you hoping would be different afterward?**
   - Clarifies the desired progress or job to be done.

Useful follow-up prompts often help anchor the story in real context: where they were, what had just happened, what the emotional tone was, what the workaround looked like, and what changed on the day they finally acted.

If someone brings up a feature request in the middle of an interview, redirect back to the situation:

- Tell me about the last time you needed that.
- What were you trying to do?
- What did you end up doing instead?
- What made that frustrating or difficult?

## Worked example

See `examples/mattress/` for a concrete single-interview example that starts with a raw transcript and turns it into a processed A2B artifact.

That folder includes:

- `transcript.md` — the raw mattress interview
- `interview-card.md` — a worked single-interview A2B analysis
- `walkthrough.md` — a short explanation of how Point A, Path Y, tipping moment, Path X, and Point B were interpreted

It is meant to help humans and LLMs calibrate what a strong single-interview output looks like before moving into multi-interview synthesis.

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
├── examples/
│   └── mattress/
│       ├── transcript.md
│       ├── interview-card.md
│       └── walkthrough.md
└── knowledge/
    ├── A2B.pdf
    ├── Example Report.pdf
    └── The Art & Science of Framing.pdf
```

## Using this with Claude Code, Codex, Gemini Code, GPT, or other LLM tools

The repo is intentionally tool-agnostic.

### Minimal setup

1. Give the model `prompt/custom-gpt.md` as the main operating instruction.
2. Add the files in `docs/`, `templates/`, `knowledge/`, and `examples/` as reference context.
3. Add your transcripts or notes in a `data/` folder.
4. Ask the model to work in one of four modes:
   - `GUIDE`
   - `INGEST`
   - `SINGLE`
   - `SYNTHESIZE`

### Practical mapping by tool

- **ChatGPT / custom GPT / project instructions**: use `prompt/custom-gpt.md` as the main behavior spec and attach the docs, templates, and examples as knowledge.
- **Claude Code**: keep the prompt file in-repo and point Claude to it as the synthesis operating guide; use the templates and examples as output targets and calibration artifacts.
- **Codex / GPT in repo workflows**: include the prompt file in the working tree and explicitly tell the model to follow it while reading files from `data/` and writing outputs into `outputs/`.
- **Gemini Code / Gemini app workflows**: paste or attach `prompt/custom-gpt.md`, then attach the method docs, examples, and templates so the model has the frame definitions and output structure.
- **Any other agentic coding tool**: treat this repo as the source of truth for method, prompt, worked example, and output shape.

### Suggested working pattern

For 1–3 interviews:

- run `SINGLE` on each interview first
- produce one interview card per interview
- compare one result to the mattress example if you want a calibration pass
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
