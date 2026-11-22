---
name: analyze-interview
description: Reconstruct a customer's concrete switching decision, source-locate verbatim evidence, and draft provisional A-to-B synthesis with human review gates.
---

# Analyze a switching interview

Ground the analysis exclusively in user-designated sources. Do not fetch external sites just because the transcript mentions them. Verify which source ranges are available: FULL, PARTIAL, UNREADABLE or UNKNOWN. Material not accessible is **not observed**, not disproved.

1. Segment the interview into meaningful scenes with exact turn, timestamp or page ranges. Identify zero or more bounded **decision episodes** `D##` per `I##`; one interview does not automatically equal one episode.
2. Extract relevant contiguous verbatim excerpts as `E###`, preserving speaker, source ID, source location, interview, episode, segment, evidence type and contrary material. Keep facilitator commentary and quoted third-party claims distinct from participant accounts. Do not manufacture quotations or deduce missing chronology.
3. Reconstruct Point A (struggle), Path Y (existing approach), pre-switch baseline, tipping context, Path X (adopted or attempted), desired Point B, and **observed** Path X result. Label the missing stages UNKNOWN. Distinguish a purchase from actual use and realized progress.
4. Build A/B codes and evidence mappings, followed by `L###` within-episode links. Explain why each link follows from its E references; include contradictions, and distinguish EXPLICIT from INFERRED.
5. Explain Push, Pull, Anxiety and Inertia, then write a job story and **provisional**, technology-agnostic fit criteria. Cite all substantive findings. Preserve negative cases and uncertainty.
6. Stop at human review gates: evidence bank first, then coding/links, then clusters (if used). Until the user actually reviews and accepts the evidence, label the result PROVISIONAL. Do not turn conversation assent into retroactive reviewed source records unless the user specifically reviews those records.

If an MCP server is connected, use `check_study` to validate the explicit study bundle and source texts after extraction and review. The validator runs deterministic schema, excerpt, link, matrix, cluster and checkpoint checks; it does not certify interpretation quality. Never invent a successful validation call.

For more than one interview, preserve distinct respondent identities; cluster **episodes** only when useful. Small convenience samples do not establish population prevalence or effects. Use source references rather than copying raw transcript text into unnecessarily long replies.
