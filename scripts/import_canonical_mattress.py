"""Import the full publicly published mattress-interview transcript as a reproducible snapshot.

Use only with permission to republish the source. Preserves dialogue, editorial
interludes, and facilitator game-off commentary as distinct types of material.
This importer does not classify an interviewer's claims as customer evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, Tag

SOURCE_URL = "https://jobstobedone.org/radio/the-mattress-interview-part-one/"
ROLES = {"Chris": "FACILITATOR", "Bob": "FACILITATOR",
         "Jason": "FACILITATOR", "Ryan": "AUDIENCE",
         "Interviewee": "PARTICIPANT", "Audience Member": "AUDIENCE",
         "Audience": "AUDIENCE"}
SPEAKER = re.compile(
    r"^(Audience Member|Interviewee|Chris|Bob|Jason|Ryan|Audience):\s*", re.I
)
INLINE_SPEAKER = re.compile(
    r"(?=(?<![A-Za-z])(?:Audience Member|Interviewee|Chris|Bob|Jason|Ryan|Audience):\s*)",
    re.I,
)
START_HEADING = "Why we are sharing a live JTBD interview"
STOP_HEADING = "Listen to the interview debrief and Q&A"


def text(value: Tag) -> str:
    return re.sub(r"[ \t]+", " ", value.get_text(" ", strip=True)).strip()


def extract(html: str) -> tuple[list[dict], list[dict], int]:
    soup = BeautifulSoup(html, "html.parser")
    section = next(
        (h for h in soup.find_all(["h2", "h3"])
         if START_HEADING.lower() in text(h).lower()), None
    )
    if section is None:
        raise ValueError("Cannot identify complete interview section; source markup changed")

    blocks = []
    for tag in section.find_all_next(["h2", "h3", "p", "blockquote"]):
        if tag.name in {"h2", "h3"} and STOP_HEADING.lower() in text(tag).lower():
            break
        if tag.name == "blockquote":
            continue
        if tag.find_parent("blockquote"):
            continue
        if tag.name == "p" and tag.find_parent(["header", "footer", "nav"]):
            continue
        txt = text(tag)
        if not txt:
            continue
        blocks.append({"kind": "HEADING" if tag.name.startswith("h") else "PARAGRAPH",
                       "text": txt})

    turns: list[dict] = []
    mixed: list[dict] = []
    current_heading = START_HEADING
    previous_role = None
    for block in blocks:
        value = block["text"]
        if block["kind"] == "HEADING":
            current_heading = value
            mixed.append({"kind": "SECTION", "heading": value})
            previous_role = None
            continue

        # A few paragraph elements contain multiple labeled turns separated by
        # HTML line-breaks. Split only at a new *speaker* label, not at punctuation.
        parts = [p.strip() for p in INLINE_SPEAKER.split(value) if p.strip()]
        # BeautifulSoup may flatten <br> tags into whitespace. As a conservative
        # fallback, preserve a whole paragraph instead of inventing speaker turns.
        if len(parts) == 0:
            parts = [value]

        for part in parts:
            match = SPEAKER.match(part)
            if match:
                key = next(k for k in ROLES if k.lower() == match.group(1).lower())
                utterance = part[match.end():].strip()
                if not utterance:
                    continue
                turn_id = f"T{len(turns) + 1:04d}"
                turns.append({
                    "turn_id": turn_id, "speaker": key, "role": ROLES[key],
                    "section": current_heading, "text": utterance,
                })
                mixed.append({
                    "kind": "DIALOGUE", "turn_id": turn_id, "speaker": key,
                    "role": ROLES[key], "text": utterance,
                })
                previous_role = key
            elif previous_role and not (
                part.startswith(("Concept ·", "Go deeper", "See how",
                                 "Read on", "A struggle", "The “impulse",
                                 "From first thought", "Two forces",
                                 "Why the milk", "This is the famous"))
                or "→" in part
            ):
                # Web text formatting places some continuous spoken paragraphs
                # in standalone <p> nodes, without repeating "Interviewee:".
                turns[-1]["text"] += "\n" + part
                mixed[-1]["text"] += "\n" + part
            else:
                mixed.append({"kind": "EDITORIAL_OR_UNASSIGNED", "text": part,
                              "section": current_heading})
                previous_role = None

    # The published page contains nested/duplicated dialogue fragments in
    # some HTML blocks. Collapse *repeated multi-turn sequences*, keeping
    # the later, correctly positioned segment. Do not dedupe individual
    # "yes"/"no" utterances: the customer may genuinely repeat them.
    normalized = [
        row["speaker"] + " " + re.sub(r"\\s+", " ", row["text"]).strip()
        for row in turns
    ]
    duplicates: set[int] = set()
    i = 0
    while i < len(turns):
        if len(normalized[i]) >= 40:
            length = 0
            for j in range(i + 1, len(turns)):
                if normalized[i] != normalized[j]:
                    continue
                count = 0
                while (
                    i + count < j and j + count < len(turns)
                    and normalized[i + count] == normalized[j + count]
                ):
                    count += 1
                length = max(length, count)
            if length >= 4:
                duplicates.update(range(i, i + length))
                i += length
                continue
        i += 1
    # Preserve the last copy when an exact, substantial utterance appears twice.
    # Short replies like "No" and "Yeah" must remain distinct.
    latest_occurrence = {}
    for i, key in enumerate(normalized):
        if len(key) >= 80:
            if key in latest_occurrence:
                duplicates.add(latest_occurrence[key])
            latest_occurrence[key] = i
    # A few parent paragraphs duplicate a long later utterance but collapse
    # whitespace or include editorial spillover. Preserve the final version.
    for i, row in enumerate(turns):
        if i in duplicates or len(row["text"]) < 800:
            continue
        opening = normalized[i][:120]
        for j in range(i + 1, len(turns)):
            if row["speaker"] == turns[j]["speaker"] and normalized[j].startswith(opening):
                duplicates.add(i)
                break

    removed_ids = {turns[i]["turn_id"] for i in duplicates}
    clean = [turn for i, turn in enumerate(turns) if i not in duplicates]
    id_map = {
        row["turn_id"]: f"T{i:04d}" for i, row in enumerate(clean, start=1)
    }
    for row in clean:
        row["turn_id"] = id_map[row["turn_id"]]
    clean_mixed = [
        row for row in mixed
        if row.get("kind") != "DIALOGUE" or row["turn_id"] not in removed_ids
    ]
    for row in clean_mixed:
        if row.get("kind") == "DIALOGUE":
            row["turn_id"] = id_map[row["turn_id"]]
    turns, mixed = clean, clean_mixed

    if len(turns) < 75:
        raise ValueError(f"Too few speaker turns ({len(turns)}): extraction may be partial")
    participant_text = " ".join(t["text"] for t in turns if t["role"] == "PARTICIPANT")
    for marker in ("Costco", "Groupon", "Macy", "mattress", "wife"):
        if marker.lower() not in participant_text.lower():
            raise ValueError(f"Missing expected source topic {marker!r}")
    if sum(t["role"] == "PARTICIPANT" for t in turns) < 30:
        raise ValueError("Participant transcript appears incomplete")
    return turns, mixed, len(removed_ids)


def render(mixed: list[dict], sha: str) -> str:
    lines = [
        "# The Mattress Interview — full dialogue and teaching context",
        "",
        f"Original page: {SOURCE_URL}",
        f"Source HTML SHA-256: {sha}",
        "",
        "This is a source snapshot, not an analyst reconstruction.",
        "Facilitator and audience commentary is preserved but is not participant evidence.",
        "Editorial notes remain visible and are marked separately.",
        "",
    ]
    for row in mixed:
        if row["kind"] == "SECTION":
            lines.extend(["", "## " + row["heading"], ""])
        elif row["kind"] == "DIALOGUE":
            lines.append(f"**{row['speaker']} [{row['turn_id']}, {row['role']}]:** "
                         + row["text"].replace("\n", "\n\n"))
            lines.append("")
        else:
            lines.append("**[EDITORIAL/UNASSIGNED — not participant evidence]:** "
                         + row["text"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="Use pinned local HTML instead of fetching")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.html:
        raw = args.html.read_bytes()
    else:
        request = urllib.request.Request(
            SOURCE_URL,
            headers={"User-Agent": "CanonicalInterviewResearch/1.0 (source attribution)"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    content = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    turns, mixed, removed_count = extract(content)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "full-transcript.md").write_text(render(mixed, digest), encoding="utf-8")
    (out / "source-turns.json").write_text(
        json.dumps(turns, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "source-manifest.json").write_text(
        json.dumps({
            "source_url": SOURCE_URL,
            "source_html_sha256": digest,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "speaker_turns": len(turns),
            "duplicate_html_speaker_turns_removed": removed_count,
            "participant_turns": sum(x["role"] == "PARTICIPANT" for x in turns),
            "facilitator_turns": sum(x["role"] == "FACILITATOR" for x in turns),
            "audience_turns": sum(x["role"] == "AUDIENCE" for x in turns),
            "editorial_blocks": sum(x["kind"] == "EDITORIAL_OR_UNASSIGNED" for x in mixed),
            "coverage": "FULL_PUBLISHED_PAGE_NOT_ORIGINAL_AUDIO",
            "limitations": [
                "The website is an edited published transcript with editorial material.",
                "The audio has not been independently re-transcribed.",
            "Repeated runs of website dialogue caused by HTML nesting were collapsed "
            "using repeat-sequence matching; compare source for edge cases.",
                "Do not treat game-off explanations, audience commentary, or site editorial "
                "as first-person customer evidence.",
            ],
        }, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Imported {len(turns)} speaker turns, "
        f"{sum(x['role'] == 'PARTICIPANT' for x in turns)} participant turns; "
        f"SHA-256={digest}"
    )


if __name__ == "__main__":
    main()
