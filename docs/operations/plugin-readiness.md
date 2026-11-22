# Plugin development and publication readiness (v1.7.0)

This project has **two distinct deliverables**:

1. A portable ChatGPT/Codex **skills-only plugin** suitable for a private preview without claiming execution of Python analysis tools.
2. An optional **stateless MCP service** wrapping the existing Python validators, checkpoint validation, mechanism map and reviewed counterfactual brief. It can run on localhost (stdio) or in a fail-closed **single-tenant private test** HTTP mode. It is **not** yet a production OAuth multi-user app.

Do not publish a public MCP plugin or claim a successful ChatGPT MCP connection until the real service is deployed, domain/auth are verified, and end-to-end tool calls have been observed.

## Source of truth

- Plugin root: `plugins/scaled-interview-data-assistant/plugin.json`
- Four skills: `skills/get-started`, `analyze-interview`, `compare-mechanisms`, `research-to-planning`
- Optional runtime: `plugin_runtime/operations.py` and `server.py`
- Package builder: `scripts/build_plugin.py`
- Canonical real-world test: `examples/canonical-mattress/` (includes the licensed full published transcript, not independent outcome validation)
- Tests: `tests/test_plugin_distribution.py`

The older imported GPT instructions may remain separately available in users' ChatGPT accounts. Updating this repository does **not** silently update that legacy GPT or make a new public listing.

## Private skills preview

From repository root:

~~~bash
python -m pip install -e ".[dev,plugin]"
python -m ruff check .
python -m pytest -q
python scripts/build_plugin.py
~~~

This creates `dist/scaled-interview-data-assistant-1.7.0.zip`, containing exactly **one** portable plugin root with `plugin.json` and four `SKILL.md` files. The archive does **not** bundle source transcripts, checkpoints, live user data, secrets or an `mcp.json` with a nonexistent server.

For private testing, import the ZIP as a private plugin in ChatGPT/Codex through a supported creator or plugin-import surface. Try:
- "I have a recorded switch interview. Reconstruct the decision episode and flag missing evidence."
- "Review my source-located evidence bank and stop before unapproved A→B coding."
- "Using two reviewed interviews, explain rival mechanisms and contrasting cases."
- "Propose research-to-planning x, reported intent and M, but don't select y or a product yet."

Check that it clearly says **it did not execute Python validators** when only skills are installed. A skill does not execute local repository code on its own.

## Local MCP smoke test

~~~bash
python -m pip install -e ".[plugin]"
python -m plugin_runtime.server
~~~

Default `SIDA_MCP_MODE=stdio` is a local standard-input MCP server for development, not a ChatGPT-web hosted connection. Connect an MCP Inspector or a capable local MCP client and test these read-only tools:

| Tool | Behavior |
|---|---|
| `get_research_capabilities` | Accurate limits and data flow, with no private data |
| `check_study` | Validate source-located registries, verify supplied transcript excerpts, run the original deterministic CLI and return summary/counts; optionally return checkpoint JSON |
| `check_checkpoint` | Validate exact supplied checkpoint JSON, return digest and counts |
| `draft_mechanism_map` | Create unreviewed, SHA-bound study (no approval) |
| `preview_mechanism_evidence` | Inspect episode coverage and original E/L IDs |
| `compile_reviewed_mechanism_map` | Compile a genuinely human-reviewed study and PROPOSED planning handoff |
| `make_counterfactual_brief` | Require source- and review-matched scenario; no synthetic run needed |

Never feed the server a model-generated "reviewer" name or invented approved flags. Source and review states must come from the research process. A reviewer *attestation* is validated structurally, not independently verified.

### Input and safety contract

- Requests are at most 2 MB, with at most 20 inline source text files and at most 350 KB per text file. Names must be safe `.txt`/`.md` basenames; URLs and filesystem traversal are rejected. No server-side file fetching.
- The `check_study` tool requires explicit JSON arrays: `sources`, `interviews`, `episodes`, `segments`, `evidence_bank`, `codebook`, `evidence_mappings`, `links`, plus `source_files: {"file.md": "complete source text"}`. The source entries must name these files. `report` is optional. `clusters` defaults to `none` to avoid pretending a one-interview cluster has meaning.
- The server uses `TemporaryDirectory` and deletes input/output at the end of each call. No uploaded research data is persisted by the service. This does **not** control retention in ChatGPT/client layers, cloud request logging, proxies, or future hosting.
- On source validation failure, the server returns a generic error **without emitting raw subprocess logs or transcript excerpts**. Local engineers can run the CLI directly to see full diagnostics.
- The MCP process never makes model API requests, never scores SSR on its own, does not imply population estimates, and does not authorize product goals or product shapes.

## Private HTTP mode — single-tenant test only

HTTP access is **disabled by default**. It requires a bearer secret of at least 32 bytes, and the service should sit behind a TLS endpoint. Do not place a token in source control, ZIP, URL, or plugin manifest.

~~~bash
export SIDA_MCP_MODE=http
export SIDA_MCP_HOST=127.0.0.1
export SIDA_MCP_BEARER_TOKEN="<independently generated high-entropy secret>"
python -m plugin_runtime.server
~~~

The guard responds `401` without a valid bearer header. Do **not** publish this private-test variant as a public multi-user MCP plugin. Fixed tokens neither identify users nor enforce tenant permissions. A public deployment needs verified OAuth 2.1, access-token audience/scopes, per-request authorization, user isolation, rate limits, abuse prevention, HTTPS, reliable operations, safe error and proxy logging, and incident/deletion procedures.

Only once a **real HTTPS /mcp** endpoint exists and is independently validated, a private combined package can be generated with:

~~~bash
python scripts/build_plugin.py \
  --mcp-url https://YOUR-VERIFIED-SERVER/mcp \
  --auth-mode api_key
~~~

`api_key` above is **for private testing**. The package contains an authentication *descriptor*, not a token. The `--auth-mode oauth` generator option only declares OAuth metadata; it **does not implement OAuth**. Never use that flag to claim the current server accepts OAuth.

OpenAI's directory submission tooling currently requires real remote HTTPS MCP endpoints and compatible authentication. Static API-key configuration is not supported by the public portal's connection flow.

## Public Plugin Directory gates — NOT COMPLETE

Before a public submission:

1. Choose an accountable publisher identity and verify it in OpenAI Platform with the required submission permissions.
2. Implement and independently test OAuth for each user, with actual identity and tenant isolation; deploy the service at a stable verified HTTPS domain; run MCP Inspector + ChatGPT connected tests with realistic and malicious inputs.
3. Review permitted transcript processing, sensitive data minimization, confidentiality, processor contracts, server and proxy logs, retention, residency, deletion, auth security, rate limits and incident response. Publish an actual, accurate privacy policy and terms of service.
4. Provide public support and website URLs, production icon/listing copy, an authenticated demo account if needed, and **five positive plus three negative** reviewer-ready test cases.
5. Demonstrate that all tools advertise truthful read-only / open-world / destructive annotations, return no unnecessary personal data, and never promote hypothetical SSR predictions or unreviewed evidence to facts.
6. Submit to the directory through the OpenAI developer portal; approval and publication are separate actions. Never claim approval until received.

The initial skills-only private preview is a working *packaging test*, not proof of production readiness or successful MCP integration.

References: [OpenAI plugin architecture](https://developers.openai.com/plugins/concepts/plugins), [portable packaging](https://developers.openai.com/plugins/build/plugins), [MCP server development](https://developers.openai.com/plugins/build/mcp-server), and [public submission](https://developers.openai.com/plugins/deploy/submission).
