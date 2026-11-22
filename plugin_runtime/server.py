"""MCP interface for the Scaled Interview Data Assistant.

By default stdio runs locally. Private HTTP mode requires an explicitly set
high-entropy bearer secret and must be deployed behind HTTPS. It is NOT OAuth
and is not itself a public-store-ready authentication solution.
"""

from __future__ import annotations

import os
import re
import secrets
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from plugin_runtime import operations


def private_trusted_host(hostname: str | None) -> TransportSecuritySettings | None:
    """Allow a single, exact, DNS hostname for a private TLS reverse proxy.

    The SDK's safe localhost protection remains active when no host is configured.
    This setting does NOT provide TLS or OAuth, and must not be treated as either.
    """
    if not hostname:
        return None
    if (
        len(hostname) > 253
        or not re.fullmatch(
            r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
            r"[A-Za-z0-9])?\.)+[A-Za-z]{2,63}",
            hostname,
        )
    ):
        raise ValueError("SIDA_MCP_TRUSTED_HOST must be one exact DNS hostname")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[hostname, hostname + ":*"],
        allowed_origins=[],
    )


mcp = FastMCP(
    "Scaled Interview Data Assistant",
    stateless_http=True,
    json_response=True,
    transport_security=private_trusted_host(os.getenv("SIDA_MCP_TRUSTED_HOST")),
)
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, openWorldHint=False
)


@mcp.tool(annotations=READ_ONLY)
def get_research_capabilities() -> dict[str, Any]:
    """Describe what the research service can and cannot establish."""
    return {
        "name": "Scaled Interview Data Assistant",
        "type": "DETERMINISTIC_RESEARCH_TOOLS",
        "supported": [
            "source-linked evidence and registry validation",
            "read-only checkpoint checks",
            "unapproved mechanism study drafting",
            "source episode inventory",
            "human-attested mechanism compilation and PROPOSED planning handoff",
            "review-gated, non-simulated counterfactual decision brief",
            "optional source-bound Lead User research route and return provenance checks",
        ],
        "not_supported": [
            "audio transcription", "automatic human interview review",
            "autonomous LLM calls", "persistent cloud research storage",
            "population causal estimates", "automatic SSR predictions",
            "automatic accepted requirements or selected design",
        ],
        "data_handling": (
            "Stateless in-process computations and temporary files only. "
            "No remote URL fetching, no server-side saved studies. "
            "Inputs and model tool replies still travel through the client and host."
        ),
    }


@mcp.tool(annotations=READ_ONLY)
def check_study(
    study_bundle: dict[str, Any],
    clusters: str = "none",
    include_checkpoint: bool = False,
) -> dict[str, Any]:
    """Validate full source-located registries and compute a bounded checkpoint.

    Requires inline source_files and source/interviews/episodes/segments/
    evidence_bank/codebook/evidence_mappings/links arrays. Does not interpret
    transcripts. By default returns only counts and source validation status.
    """
    return operations.run_study_pipeline(
        study_bundle, clusters=clusters, include_checkpoint=include_checkpoint
    )


@mcp.tool(annotations=READ_ONLY)
def check_checkpoint(checkpoint_json: str) -> dict[str, Any]:
    """Validate the exact checkpoint JSON and return its SHA, counts and limits."""
    return operations.checkpoint_summary(checkpoint_json)


@mcp.tool(annotations=READ_ONLY)
def draft_mechanism_map(
    checkpoint_json: str, scope: dict[str, Any]
) -> dict[str, Any]:
    """Prepare an UNREVIEWED, SHA-bound study; no behavior is invented or approved."""
    return operations.draft_mechanism_study(checkpoint_json, scope)


@mcp.tool(annotations=READ_ONLY)
def preview_mechanism_evidence(
    checkpoint_json: str, study: dict[str, Any]
) -> dict[str, Any]:
    """List actual episode IDs, evidence references and coverage for review."""
    return operations.inspect_mechanism_study(checkpoint_json, study)


@mcp.tool(annotations=READ_ONLY)
def compile_reviewed_mechanism_map(
    checkpoint_json: str,
    study: dict[str, Any],
    include_report: bool = False,
) -> dict[str, Any]:
    """Compile ONLY after genuine human review; produce PROPOSED x/intent/M.

    The backend validates reviewer attestation, not the independent truth of
    that attestation. Never fill or approve review flags on the user's behalf.
    """
    return operations.compile_reviewed_mechanism_study(
        checkpoint_json, study, include_report=include_report
    )


@mcp.tool(annotations=READ_ONLY)
def make_counterfactual_brief(
    checkpoint_json: str, reviewed_scenario: dict[str, Any]
) -> dict[str, Any]:
    """Check a reviewed scenario and produce an UNTESTED product decision brief.

    Does not run an LLM or infer causal/product performance.
    """
    return operations.reviewed_counterfactual_brief(
        checkpoint_json, reviewed_scenario
    )


@mcp.tool(annotations=READ_ONLY)
def triage_context_uncertainty(
    context_question: dict[str, Any],
    checkpoint_json: str = "",
) -> dict[str, Any]:
    """Decide whether to investigate traces, current behavior, or Lead Users.

    The route is a PROPOSAL, never an executed Lead User study. Evidence and
    selected D/E IDs must match the supplied checkpoint, or remain empty when
    no checkpoint exists. Trend and high-benefit signals are *candidates*.
    """
    return operations.propose_context_research_route(
        context_question, checkpoint_json=checkpoint_json
    )


@mcp.tool(annotations=READ_ONLY)
def import_lead_user_context_evidence(
    context_route: dict[str, Any],
    lead_user_handoff: dict[str, Any],
    checkpoint_json: str = "",
) -> dict[str, Any]:
    """Validate an optional upstream x extension without accepting it as fact.

    Uses source-located E/LU refs, LU1 and LU2 support, provenance, transferability
    and the original route hash. It never fetches websites, runs Lead User
    Research, edits interview evidence, or accepts y or a product shape.
    """
    return operations.validate_lead_user_research_return(
        context_route, lead_user_handoff, checkpoint_json=checkpoint_json
    )


class BearerGuard:
    """Fail-closed, single-tenant *private test* ASGI guard.

    Production use needs a validated OAuth identity, per-user authorization and
    identity-scoped data isolation; API keys aren't a public plugin submission
    substitute. The server intentionally stores no state.
    """

    def __init__(self, app: Any, secret: str):
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("SIDA_MCP_BEARER_TOKEN must contain at least 32 bytes")
        self.app = app
        self.expected = ("Bearer " + secret).encode("utf-8")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope["type"] not in {"http", "websocket"}:
            return
        supplied = dict(scope.get("headers", [])).get(b"authorization", b"")
        if not secrets.compare_digest(supplied, self.expected):
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            await send({
                "type": "http.response.start", "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b'Bearer realm="SIDA Private Test"'),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error":"unauthorized"}',
            })
            return
        await self.app(scope, receive, send)


def main() -> None:
    mode = os.getenv("SIDA_MCP_MODE", "stdio").lower()
    if mode == "stdio":
        mcp.run(transport="stdio")
        return
    if mode != "http":
        raise ValueError("SIDA_MCP_MODE must be stdio or http")
    token = os.getenv("SIDA_MCP_BEARER_TOKEN", "")
    if len(token.encode("utf-8")) < 32:
        raise ValueError("Private HTTP mode requires a 32-byte bearer secret")
    import uvicorn

    http_app = BearerGuard(mcp.streamable_http_app(), token)
    uvicorn.run(
        http_app,
        host=os.getenv("SIDA_MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
