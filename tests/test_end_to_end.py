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
    )

    run_script(
        "build_matrices.py",
        "--mappings",
        str(mappings),
        "--output-dir",
        str(matrices_dir),
    )
    combined = pd.read_csv(matrices_dir / "interview_x_combined_code.csv")
    assert set(combined["interview"]) == {"I01", "I02", "I03"}
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
    assert {"a_code", "b_code", "jaccard", "phi", "cosine"}.issubset(links.columns)
    assert len(links) == 9

    run_script(
        "cluster_interviews.py",
        "--matrix",
        str(matrices_dir / "interview_x_combined_code.csv"),
        "--clusters",
        "2",
        "--assignments-output",
        str(matrices_dir / "interview_cluster_assignments.csv"),
        "--heatmap-output",
        str(matrices_dir / "interview_x_cluster.csv"),
    )
    assignments = pd.read_csv(matrices_dir / "interview_cluster_assignments.csv")
    assert set(assignments.columns) == {"interview", "cluster"}
    assert len(assignments) == 3

    checkpoint = tmp_path / "CHECKPOINT.json"
    run_script(
        "export_checkpoint.py",
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
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
        "--n-interviews",
        "3",
    )
