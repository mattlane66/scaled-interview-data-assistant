"""Build a private-test Agent Plugins archive from the portable plugin source.

Default is skills-only: a remote server URL MUST NOT be invented. Once a
real HTTPS MCP service and authentication exist, an explicit --mcp-url may
include its connection descriptor for private integration testing.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "scaled-interview-data-assistant"
ALLOWED = {"plugin.json", ".claude-plugin/plugin.json"}
SKILLS = {
    "skills/get-started/SKILL.md",
    "skills/analyze-interview/SKILL.md",
    "skills/compare-mechanisms/SKILL.md",
    "skills/research-to-planning/SKILL.md",
    "skills/extend-context/SKILL.md",
}
PLUGIN_FILES = ALLOWED | SKILLS
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def validated_package() -> tuple[dict, dict[str, bytes]]:
    actual = {
        file.relative_to(PLUGIN_ROOT).as_posix()
        for file in PLUGIN_ROOT.rglob("*") if file.is_file()
    }
    if actual != PLUGIN_FILES:
        raise ValueError(
            f"Unexpected or missing plugin files: "
            f"missing={sorted(PLUGIN_FILES - actual)} "
            f"extra={sorted(actual - PLUGIN_FILES)}"
        )
    for file in PLUGIN_ROOT.rglob("*"):
        if file.is_symlink():
            raise ValueError("Do not package symbolic links")
    manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    for key in ("name", "version", "description"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError(f"Missing plugin manifest field: {key}")
    if manifest["name"] != "scaled-interview-data-assistant":
        raise ValueError("Plugin identity mismatch")
    if manifest.get("$schema") != (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    ):
        raise ValueError("Expected current portable Agent Plugins schema")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", manifest["version"]):
        raise ValueError("Manifest version must be semver")
    claude_manifest = json.loads(
        (PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    for key in ("name", "version", "description", "author", "repository"):
        if claude_manifest.get(key) != manifest.get(key):
            raise ValueError(f"Claude manifest mismatch: {key}")
    if claude_manifest.get("displayName") != "Interview Data Assistant":
        raise ValueError("Claude display name mismatch")
    paths = manifest["extensions"]["com.openai"]
    onboarding = paths["onboardingSkill"]
    if onboarding != "./skills/get-started/SKILL.md":
        raise ValueError("Onboarding skill is missing or unexpected")
    payloads = {}
    for relative in sorted(PLUGIN_FILES):
        body = (PLUGIN_ROOT / relative).read_bytes()
        if not body or len(body) > 100_000:
            raise ValueError(f"Invalid plugin file size: {relative}")
        if relative.endswith("SKILL.md"):
            text = body.decode("utf-8")
            if not text.startswith("---\n") or "\nname:" not in text:
                raise ValueError(f"Missing YAML skill frontmatter: {relative}")
        payloads[relative] = body
    return manifest, payloads


def remote_config(url: str, auth: str) -> bytes:
    parsed = urlparse(url)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path != "/mcp"):
        raise ValueError("MCP URL must be a real HTTPS /mcp endpoint without credentials")
    if (
        parsed.hostname in {"localhost", "example.com", "example.org", "example.net"}
        or parsed.hostname.endswith((".example", ".invalid", ".test", ".localhost"))
    ):
        raise ValueError("Do not ship a placeholder MCP endpoint")
    if auth not in {"api_key", "oauth"}:
        raise ValueError("Explicit auth mode required for a remote MCP endpoint")
    settings = (
        {"type": "api_key", "headerScheme": "bearer"}
        if auth == "api_key" else
        {"type": "oauth", "client": {"mode": "dcr"}}
    )
    return (json.dumps({
        "$schema": MCP_SCHEMA,
        "mcpServers": {"research": {
            "type": "streamable-http",
            "url": url,
            "extensions": {"com.openai": {"auth": settings}},
        }},
    }, indent=2) + "\n").encode("utf-8")


def build_archive(
    output: Path,
    *, mcp_url: str | None = None,
    auth_mode: str | None = None,
) -> dict:
    manifest, files = validated_package()
    if (mcp_url is None) != (auth_mode is None):
        raise ValueError("Pass both --mcp-url and --auth-mode together")
    if mcp_url:
        files["mcp.json"] = remote_config(mcp_url, auth_mode)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, payload in sorted(files.items()):
            zpath = f"{manifest['name']}/{relative}"
            info = zipfile.ZipInfo(zpath, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)
    return {
        "archive": str(output),
        "plugin": manifest["name"],
        "version": manifest["version"],
        "mode": "SKILLS_AND_MCP" if mcp_url else "SKILLS_ONLY",
        "file_count": len(files),
        "public_submission_ready": False,
        "reason": (
            "Developer verification, privacy/terms URLs, and, for MCP, deployed "
            "OAuth and independent security tests are not part of packaging."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mcp-url")
    parser.add_argument("--auth-mode", choices=["api_key", "oauth"])
    args = parser.parse_args()
    version = validated_package()[0]["version"]
    destination = args.output or (
        ROOT / "dist" / f"scaled-interview-data-assistant-{version}.zip"
    )
    print(json.dumps(
        build_archive(destination, mcp_url=args.mcp_url, auth_mode=args.auth_mode),
        indent=2,
    ))


if __name__ == "__main__":
    main()
