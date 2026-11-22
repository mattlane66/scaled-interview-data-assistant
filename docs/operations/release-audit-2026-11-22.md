# Repository release audit — 2026-11-22

**Audited release:** 1.7.1 (pending merge and final CI verification)  
**Repository:** `mattlane66/scaled-interview-data-assistant`  
**Scope:** Whole tracked source tree and documented workflows, including source/registries, decision-episode A→B synthesis, association and clustering code, source/checkpoint schemas, canonical real and synthetic examples, mechanism map, counterfactuals and SSR, skills and packaging, MCP stdio/HTTP, container runtime, privacy boundaries and GitHub Actions.

## Executive finding

The architecture consistently distinguishes reported human evidence, analyst interpretations, simulation hypotheses and product-design authority. Its deterministic pipeline is suitable for evidence-traceable assistance **subject to explicit human review**. The software is not a causal discovery engine, a statistically validated behavioral prediction system, or a remotely deployed multi-tenant product.

Previous green CI runs established that the code worked **from the checkout**. They did not establish that a pip-installed wheel contained the working runtime. The audit added independent distribution and protocol checks and corrected substantive fidelity and security defects. This was not a formal external penetration test or independent human reanalysis of every source claim.

## Material findings and disposition

| Severity | Finding | Correction | Regression proof |
|---|---|---|---|
| **High — evidence integrity** | Association output unconditionally called a supplied link registry `REVIEWED`, although the real mattress's four links were AI-curated and awaiting human adjudication | Renamed metadata `PROVIDED_UNATTESTED` and corrected canonical CSV; kept `INFERRED` link basis separate | Canonical output and review-boundary tests |
| **High — distributable runtime** | `pip wheel` built only metadata, omitting operational modules and JSON schemas; tests were masked by editable checkout imports | Explicitly package `simulation`, `plugin_runtime`, `scripts`, `schemas`, including runtime JSON schemas; remove deprecated license table | CI inspects wheel, installs it separately and loads/validates a checkpoint outside the checkout |
| **High — source isolation** | A transcript named `synthesis_report.md` could be overwritten by an output file of that name before source verification | Reject the reserved source name before starting the validator subprocess | Adversarial source/report collision test |
| **High — dependency hygiene** | `mcp>=1.20` allowed versions affected by session-management resource exhaustion | Require `mcp>=1.30.0,<2` (see [Python SDK advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv)) | CI installs patched dependency on both supported Python versions |
| **Medium — HTTP deployability** | Private HTTP MCP accepted the bearer secret but the SDK's default Host allowlist rejects real proxy hostnames | Added explicit `SIDA_MCP_TRUSTED_HOST` exact DNS allowlist; default remains localhost-only and Origin-restricted | Real authenticated HTTP initialize test, negative auth tests and host allowlist tests |
| **Medium — documentation quality** | Three operational guides accidentally escaped Markdown backticks, and README's layout/review wording was stale | Repaired rendering; updated path tree and explicitly distinguished supplied code links from human review | Automated relative-link, schema and release-version checks |

None of these corrections changes source interview excerpts, accepted human decisions, the historical canonical checkpoint, or original participant identities. The original reference remains explicitly AI-audited, **not independently human-approved**.

## Verification matrix

| Area | Audit evidence | Boundary |
|---|---|---|
| **Core registries & pipeline** | Existing multi- and single-episode end-to-end tests; independent source/checkpoint validation on canonical interview | Checkers validate provenance and structure, not meaning |
| **A↔B, clustering & codebook** | Existing association, sparse support and cluster-ID tests; new unreviewed-link regression | No population inference or causal attribution |
| **Canonical interview & SSR** | Source spans, 28 participant-only excerpts, one-episode checkpoint and saved SSR vectors; existing SSR normalization and provenance tests | Synthetic SSR samples are educational and not holdout-calibrated |
| **Behavioral mechanisms & design handoff** | Human review gates, rival-case and x/intent/y/M schema tests | Reviewer identity is self-attested; no accepted y or shape |
| **Plugin manifest and skills** | ZIP package builder, manifest identity/version, skill source and onboarding checks; a private skills-only plugin exists | Private skill invocation is not equivalent to an executed MCP tool |
| **MCP stdio** | Real MCP session, seven discovered annotated tools and capability-tool response | Local executable smoke only |
| **MCP HTTP** | ASGI initialize with valid bearer, unauthorized request denied; explicit DNS Host allowlist | No live TLS or real ChatGPT remote connection |
| **Distribution** | Built wheel contains executable modules and bundled schemas; independent pip target install and checkpoint validation | Packaging tests do not prove service uptime |
| **Container** | Docker build and non-root runtime import on CI | No real load test, gateway, OAuth, or hosted health monitoring |
| **Security & privacy** | CI privacy guard, source/path limits, negative traversal and no-error-echo tests | Not a DPIA, formal pen test or vendor/participant compliance review |
| **Docs** | All relative Markdown links and JSON schema metaschemas checked | External URLs and source licensing assertions are not exhaustively independently audited |

## Remaining gates (not defects resolved here)

**Research acceptance:** Human adjudication of the canonical mattress interpretation is still open (issue #11). One interview cannot support cross-person job prevalence, causal effects, calibrated purchase likelihood, or validated SSR predictions. The future prediction/holdout study is separate (issue #5).

**Public Plugin Directory:** Issue #14 tracks a verified HTTPS service, OAuth 2.1, per-user authorization, tenant isolation, request rate/body limits at the HTTP/gateway layer, abuse and log controls, retention/deletion policy, data processor and participant-consent review, privacy policy, terms, developer identity, real ChatGPT connection testing and directory submission. The current private plugin is **skills-only**. Do not represent the MCP server as connected remotely.

**Production operational testing:** Docker build and local protocol handshake do not test real load, concurrency exhaustion, outages, reverse proxies, cross-tenant access, secret rotation, or user deletion. The server uses a single-tenant bearer secret only for private integration testing. The automated privacy guard examines repository changes; it is not a security certification.

## Release rule

**Engineering gate:** Ruff, complete pytest on Python 3.10 and 3.12, schema and relative-link checks, source/checkpoint and canonical SSR tests, installed-wheel smoke, Docker non-root smoke and privacy guard must pass at the exact merge commit.

**Scientific gate:** Regardless of automated engineering success, no software release automatically grants human review, empirical behavioral validation or authority to shape a product.

**Publication gate:** Do not submit the remote MCP plugin publicly until issue #14 is complete and the deployed service has been independently exercised.
