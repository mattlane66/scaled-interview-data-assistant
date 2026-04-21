# Mattress worked example

This folder shows how to use the Scaled Interview Data Assistant on a single interview from raw transcript to structured analysis.

## What is included

- `input/mattress-interview.md` — the raw transcript
- `output/evidence-bank.md` — verbatim excerpts with lightweight tags
- `output/interview-card.md` — a worked single-interview A2B card
- `run-example-prompt.md` — a starter prompt for Claude Code, Codex, Gemini Code, GPT, or similar tools

## Why this example is useful

A concrete example lowers the activation energy for new users.

It shows:
- how to go from raw transcript to evidence
- how to separate Point A from Path Y and Path X
- how to preserve UNKNOWNs instead of hallucinating outcomes
- what a good single-interview output should look like before multi-interview synthesis

## Important note

This interview captures the purchase story well, but it does **not** fully capture the after-use experience.

That is useful in itself: a good analysis should mark post-purchase outcome claims as `UNKNOWN` rather than inventing them.
