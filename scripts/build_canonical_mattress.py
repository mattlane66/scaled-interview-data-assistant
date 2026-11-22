"""Build an explicitly provisional, runnable study from the published mattress interview.

All source excerpts must be exact contiguous spans of a PARTICIPANT speaker turn.
This script never performs or claims independent human review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SECTIONS = {
    "Building the timeline: the day at Costco": "S01",
    "The struggling moment: a year of bad sleep": "S02",
    "Why he waited so long to switch": "S03",
    "Passive looking, active looking, and the decision": "S04",
    "Espoused behavior vs. real behavior": "S05",
    "The four forces: anxiety, habit, and the moment of truth": "S06",
    "Inside the method: lowering anxiety and finding the job": "S07",
}

# Literal snippets are source selectors. Both start and end are included.
# A and B codes are interpretive, provisional, not source assertions.
EVIDENCE = [
    ("bought an overpriced Sterns & Foster",
     "and we got the cushy pillow top.", "current_state", "A02", "",
     "Old mattress: significant prior investment and expectation."),
    ("I would say for about a year I kept waking up every morning",
     "I need to find something different.’", "current_state", "A01", "",
     "Year of waking pain; reported, not independently diagnosed."),
    ("Year three kind of ‘eh,’ year four, couldn’t stand it.",
     "Had total buyer’s remorse.", "current_state", "A01", "",
     "Reported degradation over years; no objective clinical data."),
    ("I tried sleeping without pillows, I tried adjusting my position",
     "all this stuff.", "concrete_event_or_behavior", "A01", "",
     "Concrete prior attempts before replacement."),
    ("I did not. Last year was the first year of my business",
     "but I didn’t have those problems.", "current_state", "A01", "",
     "Reported contrast with hotel sleep; not proof of mattress causality."),
    ("Yeah, I flipped it, I rotated it, I turned it upside down",
     "took it off the box springs.", "concrete_event_or_behavior", "A01", "",
     "Repeated attempts to preserve old bed."),
    ("she started, I would say the last six months, to realize too",
     "‘I’m starting to have problems too. It’s uncomfortable,’",
     "current_state", "A01", "", "Wife's reported struggle is secondhand testimony."),
    ("I think life gets in the way, between building a company",
     "then move to a different place.", "current_state", "A03", "",
     "Business, children, and moving competed for attention."),
    ("Buying a new mattress was not top of priority list.",
     "Buying a new mattress was not top of priority list.", "current_state",
     "A03", "", "Explicit priority constraint."),
    ("I went back to Macy’s Home Store and asked some questions",
     "lay a yard stick across the sink of the mattress.’",
     "concrete_event_or_behavior", "A02", "", "Unsuccessful warranty-help pathway."),
    ("I did not do that, because they said it had to be at least an inch and a half.",
     "I did not do that, because they said it had to be at least an inch and a half.",
     "concrete_event_or_behavior", "A02", "", "Reported eligibility threshold blocked claim."),
    ("And measure it to make sure you’ve hit that magic number",
     "nothing about the warranty mattered.", "interpretation", "A02", "",
     "Participant's interpretation of an unsatisfactory return process."),
    ("Within that three month window, I started doing research",
     "just gave me the skeeves.", "concrete_event_or_behavior", "A04", "",
     "Active research and aversion to conventional mattress retail."),
    ("I did a lot of online research, came this close to pulling the trigger on a Groupon",
     "then what am I going to do?", "concrete_event_or_behavior", "A02", "",
     "Near purchase abandoned because recovery path felt uncertain."),
    ("To me, it was about a good night’s sleep.",
     "as a business guy and a dad and a husband the next day.", "aspiration", "",
     "B01", "Desired progress explicitly independent of mattress features."),
    ("Yeah, the mattress was not on the list.",
     "Yeah, the mattress was not on the list.", "concrete_event_or_behavior",
     "", "", "No planned mattress purchase on shopping trip."),
    ("I actually go down an aisle unexpectedly",
     "and there’s the mattress.", "concrete_event_or_behavior", "", "B03",
     "Unplanned discovery at trusted existing shopping location."),
    ("There was some, ‘Are you sure you want it?’",
     "‘Here touch it, feel it.’", "concrete_event_or_behavior",
     "A02", "B03", "Partner's hesitation; participant offers physical foam sample."),
    ("‘Oh, that’s actually not bad. If you want it, get it.",
     "That’s when I went out and got the flatbed.", "concrete_event_or_behavior",
     "", "B03", "Participant-reported spouse endorsement and purchase action."),
    ("Yeah, it was $699.",
     "the Costco that’s five minutes from my house?", "concrete_event_or_behavior",
     "A02", "B02", "Paid more than Groupon option; local return mattered."),
    ("That really didn’t get me. What got me was the ability",
     "To me going with foam was radically different.", "interpretation",
     "A04", "B04", "Participant attributes choice to touch and novel material."),
    ("There was two that we were specifically looking at",
     "That was the one that we went with.", "concrete_event_or_behavior", "",
     "B04", "Selected one of the foam options, not merely hypothetical intent."),
    ("I actually slept on the old mattress last night.",
     "I actually slept on the old mattress last night.", "concrete_event_or_behavior",
     "A05", "", "Old product still in use after new purchase."),
    ("I have not thrown it out yet.",
     "I have not thrown it out yet.", "current_state", "A05", "",
     "Retention of old mattress; reasons are not fully established."),
    ("First of all, I’m a germaphobe.",
     "I see all these beds lined up everywhere and it’s creepy.",
     "current_state", "A04", "", "Reported discomfort in showroom setting."),
    ("this mattress issue still hasn’t actually been resolved",
     "I was like, ‘I can’t go in.’", "current_state", "A04", "",
     "Post-purchase situation remained unresolved; mechanism unknown."),
    ("Oh yeah. Not a lot, but a couple things.",
     "Oh yeah. Not a lot, but a couple things.", "concrete_event_or_behavior",
     "", "B02", "Reports prior successful Costco returns."),
    ("I will tell you this. Walgreens specifically I wouldn’t purchase it there.",
     "I will tell you this. Walgreens specifically I wouldn’t purchase it there.",
     "hypothetical", "", "", "Hypothetical response: expressly excluded from observed choice."),
]

CODEBOOK = [
    ("A01", "Prior mattress causes reported morning discomfort and impaired functioning."),
    ("A02", "Replacement feels hard to reverse or recover from when a product disappoints."),
    ("A03", "Competing family, business, and move demands delay the replacement."),
    ("A04", "Conventional mattress sales channels feel uncomfortable or untrustworthy."),
    ("A05", "Old mattress remains in use or retained after the new purchase."),
    ("B01", "Wake rested enough to function well in work and family roles."),
    ("B02", "Try a replacement with a credible, recoverable purchase path."),
    ("B03", "Make a joint buying decision during an existing shopping occasion."),
    ("B04", "Choose a materially different mattress through a manageable evaluation."),
]

LINKS = [
    ("L001", "A01", "B01", ["E002", "E004", "E015"],
     "Reported waking impairment motivates desire for rested functioning."),
    ("L002", "A02", "B02", ["E010", "E014", "E020", "E027"],
     "Failed recovery and Groupon anxiety make known-store return experience salient."),
    ("L003", "A03", "B03", ["E008", "E009", "E017", "E019"],
     "Competing obligations make convenient joint purchase a plausible path."),
    ("L004", "A04", "B04", ["E013", "E021", "E025"],
     "Retail aversion and foam sample shape a different product evaluation path."),
]


def write_json(directory: Path, name: str, value: object) -> None:
    (directory / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build(folder: Path) -> dict:
    turns = json.loads((folder / "source-turns.json").read_text(encoding="utf-8"))
    present = {row["section"] for row in turns if row["role"] == "PARTICIPANT"}
    unrecognized = present - SECTIONS.keys()
    if unrecognized:
        raise ValueError(f"Unrecognized source sections: {sorted(unrecognized)}")
    bank = []
    mappings = []
    selected_turns = set()
    for idx, (start, end, kind, a_codes, b_codes, note) in enumerate(EVIDENCE, 1):
        matches = [
            row for row in turns if row["role"] == "PARTICIPANT"
            and start in row["text"] and end in row["text"]
            and row["text"].index(start) <= row["text"].index(end)
        ]
        if not matches:
            raise ValueError(f"Could not locate exact participant excerpt E{idx:03}: {start}")
        # Last match avoids hidden duplicate HTML blocks present on the source page.
        row = matches[-1]
        payload = row["text"]
        begin = payload.index(start)
        stop = payload.index(end, begin) + len(end)
        excerpt = payload[begin:stop]
        if "\n" in excerpt:
            raise ValueError(f"Excerpt E{idx:03} crosses a source paragraph boundary")
        if not excerpt.strip():
            raise ValueError(f"Empty source excerpt E{idx:03}")
        selected_turns.add(row["turn_id"])
        evidence_id = f"E{idx:03d}"
        bank.append({
            "evidence": evidence_id, "source_id": "SRC01",
            "interview": "I01", "episode": "D01",
            "segment": SECTIONS[row["section"]],
            "source": "full-transcript.md",
            "source_location": f"{row['turn_id']} | {row['section']}",
            "speaker": "PARTICIPANT", "evidence_type": kind,
            "verbatim_excerpt": excerpt,
            "tags": "Participant testimony; preliminary A/B inference",
            "note": note,
        })
        mappings.append({
            "evidence": evidence_id, "interview": "I01", "episode": "D01",
            "a_codes": a_codes, "b_codes": b_codes,
        })
    if not all(row["speaker"] == "PARTICIPANT" for row in bank):
        raise ValueError("Facilitator or audience content is in the participant evidence bank")
    transcript = (folder / "full-transcript.md").read_text(encoding="utf-8")
    for row in bank:
        if row["verbatim_excerpt"] not in transcript:
            raise ValueError(
                f"Excerpt {row['evidence']} is not verbatim in published transcript snapshot"
            )
    meta = json.loads((folder / "source-manifest.json").read_text())
    sources = [{
        "source_id": "SRC01", "source": "full-transcript.md",
        "coverage": "FULL",
        "accessible_range": f"T0001–T{meta['speaker_turns']:04d}",
        "notes": "Full published web transcript only; NOT verified against audio. "
                 + meta["source_url"],
    }]
    interviews = [{
        "interview": "I01", "descriptor": "Public workshop mattress-switch interview, "
        "one anonymous attendee, one replacement decision",
    }]
    episodes = [{
        "episode": "D01", "interview": "I01",
        "descriptor": "Replace disappointing, deteriorating mattress via an "
        "unexpected Costco foam-mattress purchase",
    }]
    segments = [{
        "interview": "I01", "segment": sid, "location": section,
    } for section, sid in SECTIONS.items()]
    links = [{
        "link": ident, "episode": "D01", "a_code": a,
        "b_code": b, "basis": "INFERRED",
        "evidence": refs, "rationale": explanation,
        "contradictions": (
            "New purchase did not establish problem resolution; old mattress retained."
            if ident == "L002" else ""
        ),
    } for ident, a, b, refs, explanation in LINKS]

    names = {
        "sources.json": sources,
        "interviews.json": interviews,
        "episodes.json": episodes,
        "segments.json": segments,
        "evidence_bank.json": bank,
        "codebook.json": [{"code": code, "definition": definition}
                          for code, definition in CODEBOOK],
        "evidence_mappings.json": mappings,
        "links.json": links,
    }
    for name, rows in names.items():
        write_json(folder, name, rows)
    result = {
        "observed_participant_source_turns": meta["participant_turns"],
        "excerpt_count": len(bank), "selected_source_turns": len(selected_turns),
        "decision_episodes": 1, "distinct_people": 1,
        "review_status": "AI_CURATED_NOT_HUMAN_APPROVED",
        "no_cluster_justification": "One participant cannot establish cross-person job clusters",
        "model_generation": "NOT_YET_RUN",
    }
    write_json(folder, "curation-manifest.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.folder), indent=2))


if __name__ == "__main__":
    main()
