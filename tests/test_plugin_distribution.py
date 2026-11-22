"""Plugin distribution safety and MCP adapters, with no live transcript upload."""

from __future__ import annotations

import asyncio
import json
import zipfile
from pathlib import Path

import pytest

from plugin_runtime.operations import (
    checkpoint_summary,
    draft_mechanism_study,
    run_study_pipeline,
)
from scripts.build_plugin import build_archive, remote_config, validated_package

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "canonical-mattress"


def _checkpoint() -> str:
    return (CASE / "results" / "CHECKPOINT.json").read_text(encoding="utf-8")


def _registries() -> dict:
    names = (
        "sources", "interviews", "episodes", "segments", "evidence_bank",
        "codebook", "evidence_mappings", "links",
    )
    bundle = {
        name: json.loads((CASE / f"{name}.json").read_text(encoding="utf-8"))
        for name in names
    }
    bundle["source_files"] = {
        "full-transcript.md": (CASE / "full-transcript.md").read_text(
            encoding="utf-8"
        ),
    }
    return bundle


def test_build_private_plugin_has_only_public_methods_and_no_mcp_endpoint(tmp_path):
    manifest, payloads = validated_package()
    assert manifest["name"] == "scaled-interview-data-assistant"
    assert len(payloads) == 5
    assert all("SECRET" not in body.decode() for body in payloads.values())
    dest = tmp_path / "private.zip"
    result = build_archive(dest)
    assert result["mode"] == "SKILLS_ONLY"
    assert result["public_submission_ready"] is False
    with zipfile.ZipFile(dest) as z:
        files = z.namelist()
        assert len(files) == 5
        assert all(x.startswith("scaled-interview-data-assistant/") for x in files)
        assert not any("mcp.json" in x for x in files)
        assert not any("full-transcript" in x for x in files)
        assert any(path.endswith("skills/get-started/SKILL.md") for path in files)


def test_remote_mcp_configuration_requires_real_https_and_auth(tmp_path):
    for address in (
        "http://example.com/mcp",
        "https://example.com/mcp",
        "https://example.invalid/mcp",
        "https://host.example/mcp",
        "https://u:p@example.org/mcp",
        "https://research.org/mcp?secret=1",
        "https://research.org/other",
    ):
        with pytest.raises(ValueError):
            remote_config(address, "oauth")
    with pytest.raises(ValueError, match="Explicit auth"):
        remote_config("https://research.example.org/mcp", "none")
    desc = json.loads(remote_config("https://research.example.org/mcp", "oauth"))
    assert desc["mcpServers"]["research"]["extensions"]["com.openai"][
        "auth"
    ]["client"]["mode"] == "dcr"
    built = build_archive(
        tmp_path / "mcp.zip", mcp_url="https://research.example.org/mcp",
        auth_mode="api_key",
    )
    assert built["mode"] == "SKILLS_AND_MCP"
    with zipfile.ZipFile(tmp_path / "mcp.zip") as archive:
        assert any(path.endswith("/mcp.json") for path in archive.namelist())


def test_checkpoint_summary_does_not_echo_transcript_content():
    summary = checkpoint_summary(_checkpoint())
    assert summary["valid"] is True
    assert summary["interviews"] == 1
    assert summary["decision_episodes"] == 1
    assert summary["evidence_rows"] == 28
    assert summary["checkpoint_sha256"].startswith("sha256:")
    assert "verbatim_excerpt" not in json.dumps(summary)


def test_draft_refuses_to_invent_a_second_interview_for_single_case():
    with pytest.raises(ValueError, match="not valid|too short|oneOf|valid"):
        draft_mechanism_study(_checkpoint(), {
            "kind": "EPISODES", "episode_ids": ["D01"],
        })
    with pytest.raises(ValueError, match="unknown|scope"):
        draft_mechanism_study(_checkpoint(), {
            "kind": "EPISODES", "episode_ids": ["D01", "D02"],
        })


def test_pipeline_runs_real_canonical_source_without_persisting_it():
    result = run_study_pipeline(_registries(), clusters="none")
    assert result["valid"] is True
    assert result["evidence_rows"] == 28
    assert result["decision_episodes"] == 1
    assert result["clusters"] == 0
    assert "checkpoint_json" not in result
    assert result["source_verification"] == (
        "EXCERPTS_CHECKED_AGAINST_SUPPLIED_SOURCE_TEXT"
    )
    assert result["interpretation_review"] == (
        "HUMAN_REVIEW_NOT_VERIFIED_BY_THIS_TOOL"
    )


def test_malicious_source_paths_and_oversized_inputs_are_rejected():
    bundle = _registries()
    for path in ("../escape.txt", "/root/raw.txt", "https://evil.com/a.txt",
                 ".secret.md", "note.py", "a/b.md"):
        changed = dict(bundle)
        changed["source_files"] = {path: "source"}
        with pytest.raises(ValueError, match="safe"):
            run_study_pipeline(changed)
    with pytest.raises(ValueError, match="maximum|limit"):
        run_study_pipeline({
            **bundle, "source_files": {"interview.md": "x" * 2_000_001}
        })
    # A safe uploaded filename is not enough: the registry itself can try to
    # cause the legacy validator to open a path outside the scratch directory.
    changed = _registries()
    changed["sources"][0]["source"] = "../../etc/passwd"
    with pytest.raises(ValueError, match="registered|safe filenames"):
        run_study_pipeline(changed)

    changed = _registries()
    changed["evidence_bank"][0]["source"] = "../../etc/passwd"
    with pytest.raises(ValueError, match="registered sources"):
        run_study_pipeline(changed)


def test_invalid_study_never_issues_fake_success_or_leaks_content():
    bundle = _registries()
    bundle["evidence_bank"][0]["verbatim_excerpt"] = (
        "SECRET_CANARY_SAMPLE_NOT_FOUND_IN_SOURCE"
    )
    result = run_study_pipeline(bundle, clusters="none")
    assert result["valid"] is False
    assert result["error_code"] == "STUDY_VALIDATION_FAILED"
    assert "SECRET_CANARY" not in json.dumps(result)


def test_http_mode_auth_guard_rejects_missing_or_wrong_token():
    pytest.importorskip("mcp")
    from plugin_runtime.server import BearerGuard

    received = []

    async def application(scope, receive, send):
        received.append(scope)
        await send({
            "type": "http.response.start", "status": 200,
            "headers": [],
        })
        await send({"type": "http.response.body", "body": b"OK"})

    async def run_request(header=None):
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(msg):
            messages.append(msg)

        guard = BearerGuard(application, "x" * 40)
        await guard({
            "type": "http",
            "path": "/mcp",
            "headers": [(b"authorization", header)] if header else [],
        }, receive, send)
        return messages

    assert asyncio.run(run_request())[0]["status"] == 401
    assert asyncio.run(run_request(b"Bearer wrong"))[0]["status"] == 401
    assert asyncio.run(run_request(b"Bearer " + b"x" * 40))[0]["status"] == 200
    assert len(received) == 1
