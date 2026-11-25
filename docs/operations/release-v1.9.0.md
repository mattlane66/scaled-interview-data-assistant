# Scaled Interview Data Assistant v1.9.0

First public release of the complete MIT-licensed research toolkit, not just the agent plugin.

Turn switching interviews into evidence-traceable product research. Reconstruct decision episodes, preserve source-located evidence, build shared A/B codebooks, explore cross-episode patterns, compare rival explanations, and hand provisional findings to product planning.

## Included

- Complete source, methodology, operating prompts, templates, schemas, tests, and real and synthetic worked examples.
- Deterministic validation, incidence and association analysis, exploratory clustering, report audit, and portable checkpoints.
- Behavioral Mechanism Maps, counterfactual decision briefs, optional behavioral simulation and semantic similarity rating.
- Evidence-gated transcript research router and independent Lead User Research handoffs.
- Six shared agent skills for Codex, Claude Code, and private ChatGPT import; optional local MCP runtime.

## Downloads and installation

GitHub's automatically generated source archives contain the complete tracked repository at this release tag. The additional ZIP is a skills-only plugin preview; the Python wheel contains the installable runtime and schemas. SHA256SUMS.txt verifies the additional distributions.

For the full workflow, extract the source archive and follow README.md:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,plugin]"
python -m pytest -q
```

## Evidence and limitations

The repository includes a source-grounded mattress casebook and a provisional two-interview published-source pilot. The pilot preserves non-comparable job scopes and does not claim independent review. Automated checks establish software behavior and structural evidence integrity, not the truth of interpretations, causation, market prevalence, or predictive validity. Human research review is required. Skills-only installation does not execute Python tools. Native client invocation, independently reviewed research and public multi-tenant remote MCP deployment remain separate gates.

The source toolkit is publicly released; agent integrations remain a developer preview, not an approved public plugin directory listing. No hosted MCP service is implied.

License: MIT (see source-specific rights notices for third-party research material).
