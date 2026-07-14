from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def test_validator_rejects_wrong_family_code(tmp_path: Path) -> None:
    mappings = json.loads((FIXTURES / "evidence_mappings.json").read_text())
    mappings[0]["a_codes"] = "B01"
    bad_mappings = tmp_path / "bad-mappings.json"
    write_json(bad_mappings, mappings)

    result = run_script(
        "validate_registry.py",
        "--evidence",
        str(FIXTURES / "evidence_bank.json"),
        "--codebook",
        str(FIXTURES / "codebook.json"),
        "--mappings",
        str(bad_mappings),
    )
    assert result.returncode == 1
    assert "wrong A-code column" in result.stdout


def test_validator_rejects_mapping_owner_mismatch(tmp_path: Path) -> None:
    mappings = json.loads((FIXTURES / "evidence_mappings.json").read_text())
    mappings[0]["interview"] = "I02"
    bad_mappings = tmp_path / "bad-owner.json"
    write_json(bad_mappings, mappings)

    result = run_script(
        "validate_registry.py",
        "--evidence",
        str(FIXTURES / "evidence_bank.json"),
        "--codebook",
        str(FIXTURES / "codebook.json"),
        "--mappings",
        str(bad_mappings),
    )
    assert result.returncode == 1
    assert "Mapping owner mismatch for E001" in result.stdout


def test_validator_checks_excerpt_against_local_source(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("The participant said the manual process lost context.\n")
    evidence = tmp_path / "evidence.json"
    codebook = tmp_path / "codebook.json"
    mappings = tmp_path / "mappings.json"
    write_json(
        evidence,
        [
            {
                "evidence": "E001",
                "interview": "I01",
                "episode": "D01",
                "segment": "S01",
                "source": "source.md",
                "source_location": "line 1",
                "verbatim_excerpt": "The participant said automation solved everything.",
            }
        ],
    )
    write_json(codebook, [{"code": "A01", "definition": "Manual process loses context."}])
    write_json(
        mappings,
        [
            {
                "evidence": "E001",
                "interview": "I01",
                "episode": "D01",
                "a_codes": "A01",
                "b_codes": "",
            }
        ],
    )

    result = run_script(
        "validate_registry.py",
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--mappings",
        str(mappings),
        "--source-root",
        str(tmp_path),
    )
    assert result.returncode == 1
    assert "excerpt was not found" in result.stdout


def test_matrices_keep_units_with_no_codes(tmp_path: Path) -> None:
    mappings = [
        {
            "evidence": "E001",
            "interview": "I01",
            "episode": "D01",
            "a_codes": "A01",
            "b_codes": "",
        },
        {
            "evidence": "E002",
            "interview": "I02",
            "episode": "D02",
            "a_codes": "",
            "b_codes": "",
        },
    ]
    path = tmp_path / "mappings.json"
    write_json(path, mappings)
    output = tmp_path / "matrices"

    result = run_script("build_matrices.py", "--mappings", str(path), "--output-dir", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = pd.read_csv(output / "episode_x_combined_code.csv")
    assert set(matrix["episode"]) == {"D01", "D02"}
    assert matrix.loc[matrix["episode"] == "D02", "A01"].item() == 0


def test_links_use_decision_episode_instead_of_whole_interview(tmp_path: Path) -> None:
    mappings = [
        {
            "evidence": "E001",
            "interview": "I01",
            "episode": "D01",
            "a_codes": "A01",
            "b_codes": "",
        },
        {
            "evidence": "E002",
            "interview": "I01",
            "episode": "D02",
            "a_codes": "",
            "b_codes": "B01",
        },
    ]
    path = tmp_path / "mappings.json"
    write_json(path, mappings)
    episode_output = tmp_path / "episode-links.csv"
    interview_output = tmp_path / "interview-links.csv"

    episode_result = run_script(
        "analyze_links.py", "--mappings", str(path), "--output", str(episode_output)
    )
    interview_result = run_script(
        "analyze_links.py",
        "--mappings",
        str(path),
        "--output",
        str(interview_output),
        "--unit-column",
        "interview",
    )
    assert episode_result.returncode == 0, episode_result.stdout + episode_result.stderr
    assert interview_result.returncode == 0, interview_result.stdout + interview_result.stderr
    assert pd.read_csv(episode_output)["jaccard"].item() == 0
    assert pd.read_csv(interview_output)["jaccard"].item() == 1


def test_cluster_ids_are_preserved_from_previous_assignments(tmp_path: Path) -> None:
    matrix = pd.DataFrame(
        [
            {"episode": "D01", "A01": 1, "B01": 1, "A02": 0, "B02": 0},
            {"episode": "D02", "A01": 1, "B01": 1, "A02": 0, "B02": 0},
            {"episode": "D03", "A01": 0, "B01": 0, "A02": 1, "B02": 1},
            {"episode": "D04", "A01": 0, "B01": 0, "A02": 1, "B02": 1},
        ]
    )
    previous = pd.DataFrame(
        [
            {"episode": "D01", "cluster": "C07"},
            {"episode": "D02", "cluster": "C07"},
            {"episode": "D03", "cluster": "C09"},
            {"episode": "D04", "cluster": "C09"},
        ]
    )
    matrix_path = tmp_path / "matrix.csv"
    previous_path = tmp_path / "previous.csv"
    output = tmp_path / "assignments.csv"
    matrix.to_csv(matrix_path, index=False)
    previous.to_csv(previous_path, index=False)

    result = run_script(
        "cluster_interviews.py",
        "--matrix",
        str(matrix_path),
        "--clusters",
        "2",
        "--previous-assignments",
        str(previous_path),
        "--assignments-output",
        str(output),
        "--heatmap-output",
        str(tmp_path / "heatmap.csv"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assignments = pd.read_csv(output)
    assert set(assignments["cluster"]) == {"C07", "C09"}


def test_report_audit_rejects_unsupported_verified_claim(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text(
        """# Report

## Method
- Analysis unit: Decision episode.
- Clustering method: Analyst-reviewed grouping.
- Computed vs. heuristic: HEURISTIC.

## Findings
### VERIFIED
- This claim has no evidence reference.
"""
    )
    result = run_script(
        "audit_report.py",
        "--report",
        str(report),
        "--evidence",
        str(FIXTURES / "evidence_bank.json"),
    )
    assert result.returncode == 1
    assert "VERIFIED claim lacks evidence ID" in result.stdout
