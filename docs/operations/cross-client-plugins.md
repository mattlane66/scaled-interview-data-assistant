# Install in Codex and Claude Code

The **same six research skills** ship in one portable, skills-only plugin. There is no duplicated methodology or separate fork for each model. This is a private/developer distribution, **not** an approved public directory listing.

## Which files each host reads

| Host | Discovery | Plugin manifest |
| --- | --- | --- |
| Codex / ChatGPT | `.agents/plugins/marketplace.json` in the repository, or a portable ZIP | `plugins/scaled-interview-data-assistant/plugin.json` |
| Claude Code | `.claude-plugin/marketplace.json` in the repository, or a local ZIP | `plugins/scaled-interview-data-assistant/.claude-plugin/plugin.json` |

Both hosts load the **same** `plugins/scaled-interview-data-assistant/skills/*/SKILL.md` files. All six skills are instruction-only by default. A skills-only installation **cannot** run local Python validators or call the MCP research tools by itself.

## Claude Code — install from GitHub

In the Claude Code CLI:

```bash
claude plugin marketplace add mattlane66/scaled-interview-data-assistant
claude plugin install scaled-interview-data-assistant@scaled-interview-research
```

Then start a new Claude Code session and invoke `/scaled-interview-data-assistant:get-started` or `/scaled-interview-data-assistant:research-router`.

For a one-session checkout test rather than installation:

```bash
claude plugin validate --strict ./plugins/scaled-interview-data-assistant
claude --plugin-dir ./plugins/scaled-interview-data-assistant
```

The exact `claude plugin validate` result must be checked on an actual Claude Code installation. Static Python tests do not substitute for that CLI.

## Codex — install from GitHub or use the portable ZIP

From Codex CLI:

```bash
codex plugin marketplace add mattlane66/scaled-interview-data-assistant
```

Open Codex's `/plugins` browser (or Plugins in the desktop app), find **Scaled Interview Research**, install **Scaled Interview Data Assistant**, and start a new session. The repo marketplace entry points to the same portable plugin source. No extra `.codex-plugin/plugin.json` compatibility manifest is necessary because the portable root manifest is the authoritative Codex entry point.

To build a portable ZIP for manual private import in ChatGPT/Codex or local Claude Code:

```bash
python scripts/build_plugin.py
```

It creates `dist/scaled-interview-data-assistant-1.9.0.zip` containing one plugin root: a portable `plugin.json`, a Claude `.claude-plugin/plugin.json`, and the six skills.

## Optional local deterministic MCP tools

For **local desktop/CLI** clients that can start stdio MCP servers, install the research runtime from this repository:

```bash
python -m pip install -e ".[plugin]"
```

Use the **absolute Python executable** from the environment in which the package was installed (for example `/absolute/path/to/repo/.venv/bin/python`). Configure the MCP server *separately* in each client; the skills package intentionally doesn't ship an auto-starting MCP configuration that would fail for users without Python installed.

Claude Code:

```bash
claude mcp add --transport stdio sida-research -- /absolute/path/to/python -m plugin_runtime.server
claude mcp get sida-research
```

Codex CLI:

```bash
codex mcp add sida-research -- /absolute/path/to/python -m plugin_runtime.server
```

Check each client's MCP tool list and call `get_research_capabilities` before claiming any validator is available. A model should never invent executed tool results, approved human reviews, or source evidence. An MCP server connection does **not** grant permission to upload private interview transcripts.

This local stdio option is not a hosted Claude.ai connector or a public ChatGPT plugin. Remote access still requires a deployed HTTPS endpoint, proper authentication and authorization, privacy review, and end-to-end tests. See [plugin readiness](plugin-readiness.md).

## Release checks

From a checkout, run:

```bash
python -m pip install -e ".[dev,plugin]"
python -m ruff check .
python -m pytest -q
python scripts/build_plugin.py
claude plugin validate --strict ./plugins/scaled-interview-data-assistant  # Requires the Claude CLI
```

The Python suite validates package contents, manifest consistency, and marketplace paths; **only native client tests** establish that a real Codex or Claude installation loads and invokes a skill. CI doesn't authenticate to either provider or run end-to-end hosted model sessions.
