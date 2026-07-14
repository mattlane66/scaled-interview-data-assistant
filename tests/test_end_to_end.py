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
        check=True,
    )


def test_end_to_end_fixture_workflow(tmp_path: Path) -> None:
    evidence = FIXTURES / "evidence_bank.json"
    codebook = FIXTURES / "codebook.json"
    mappings = FIXTURES / "evidence_mappings.json"
    interviews = FIXTURES / "interviews.json"
    episodes = FIXTURES / "episodes.json"
    segments = FIXTURES / "segments.json"
    clusters = FIXTURES / "clusters.json"
    report = FIXTURES / "synthesis_report.md"
    matrices_dir = tmp_path / "matrices"

    run_script(
        "validate_registry.py",
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--mappings",
        str(mappings),
        "--interviews",
        str(interviews),
        "--episodes",
        str(episodes),
        "--segments",
        str(segments),
    )

    run_script(
        "build_matrices.py",
        "--mappings",
        str(mappings),
        "--output-dir",
        str(matrices_dir),
    )
    combined = pd.read_csv(matrices_dir / "episode_x_combined_code.csv")
    assert set(combined["episode"]) == {"D01", "D02", "D03"}
    assert {"A01", "A02", "A03", "B01", "B02", "B03"}.issubset(combined.columns)

    links_path = matrices_dir / "a_to_b_link_strengths.csv"
    run_script(
        "analyze_links.py",
        "--mappings",
        str(mappings),
        "--codebook",
        str(codebook),
        "--output",
        str(links_path),
    )
    links = pd.read_csv(links_path)
    assert {
        "a_code",
        "b_code",
        "jaccard",
        "phi",
        "definition_cosine",
        "cooccurring_units",
    }.issubset(links.columns)
    assert len(links) == 9

    run_script(
        "cluster_interviews.py",
        "--matrix",
        str(matrices_dir / "episode_x_combined_code.csv"),
        "--clusters",
        "2",
        "--assignments-output",
        str(matrices_dir / "episode_cluster_assignments.csv"),
        "--heatmap-output",
        str(matrices_dir / "episode_x_cluster.csv"),
    )
    assignments = pd.read_csv(matrices_dir / "episode_cluster_assignments.csv")
    assert set(assignments.columns) == {"episode", "cluster"}
    assert len(assignments) == 3

    checkpoint = tmp_path / "CHECKPOINT.json"
    run_script(
        "export_checkpoint.py",
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--interviews",
        str(interviews),
        "--episodes",
        str(episodes),
        "--segments",
        str(segments),
        "--mappings",
        str(mappings),
        "--clusters",
        str(clusters),
        "--output",
        str(checkpoint),
    )
    checkpoint_data = json.loads(checkpoint.read_text())
    assert len(checkpoint_data["evidence_bank"]) == 6
    assert len(checkpoint_data["codebook"]) == 6
    assert len(checkpoint_data["episode_index"]) == 3
    assert checkpoint_data["analysis_unit"] == "episode"
    assert checkpoint_data["computation"]["cluster_count"] == 2

    restored = tmp_path / "restored"
    run_script(
        "import_checkpoint.py",
        "--checkpoint",
        str(checkpoint),
        "--output-dir",
        str(restored),
    )
    assert (
        json.loads((restored / "evidence_bank.json").read_text())
        == checkpoint_data["evidence_bank"]
    )
    assert json.loads((restored / "episodes.json").read_text()) == checkpoint_data["episode_index"]

    run_script(
        "audit_report.py",
        "--report",
        str(report),
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--clusters",
        str(clusters),
    )


def test_pipeline_command(tmp_path: Path) -> None:
    output_dir = tmp_path / "pipeline"
    run_script(
        "run_pipeline.py",
        "--evidence",
        str(FIXTURES / "evidence_bank.json"),
        "--codebook",
        str(FIXTURES / "codebook.json"),
        "--mappings",
        str(FIXTURES / "evidence_mappings.json"),
        "--interviews",
        str(FIXTURES / "interviews.json"),
        "--episodes",
        str(FIXTURES / "episodes.json"),
        "--segments",
        str(FIXTURES / "segments.json"),
        "--report",
        str(FIXTURES / "synthesis_report.md"),
        "--clusters",
        "2",
        "--output-dir",
        str(output_dir),
    )
    assert (output_dir / "CHECKPOINT.json").exists()
    assert (output_dir / "matrices" / "a_to_b_associations.csv").exists()
