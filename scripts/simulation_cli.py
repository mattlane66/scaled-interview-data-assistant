"""Optional, offline, evidence-bounded behavioral simulation CLI.

No model API calls, external data upload, or modification of original JTBD registries.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulation.core import (  # noqa: E402
    SimulationError,
    ensure_run_matches,
    initialize,
    inspect_scenario,
    load_checkpoint,
    prepare,
    read_json,
    record,
    schema_check,
    write_json,
)
from simulation.evaluation import assess  # noqa: E402
from simulation.handoff import protocol_input, protocol_runs  # noqa: E402
from simulation.report import render  # noqa: E402
from simulation.ssr import measure  # noqa: E402


def _path(parser: argparse.ArgumentParser, flag: str, *, required: bool = True) -> None:
    parser.add_argument(flag, type=Path, required=required)


def configure() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="command", required=True)
    init = actions.add_parser("init", help="Draft a checkpoint-bound scenario (review gates OFF)")
    _path(init, "--checkpoint")
    _path(init, "--output")
    init.add_argument("--episode", action="append", required=True)
    init.add_argument("--evidence", action="append", required=True)

    prep = actions.add_parser("prepare", help="Make a privacy-gated model prompt packet")
    _path(prep, "--checkpoint")
    _path(prep, "--scenario")
    _path(prep, "--output")
    prep.add_argument("--include-verbatim", action="store_true")

    rec = actions.add_parser("record", help="Validate and store externally generated model output")
    _path(rec, "--checkpoint")
    _path(rec, "--scenario")
    _path(rec, "--model-output")
    _path(rec, "--output")
    rec.add_argument("--run-id", default="R001")

    ssr = actions.add_parser("ssr", help="Map supplied embedding vectors to Likert distributions")
    _path(ssr, "--run")
    _path(ssr, "--vectors")
    _path(ssr, "--output")

    eva = actions.add_parser("evaluate", help="Evaluate SSR against person-grouped human holdout")
    for flag in ("--checkpoint", "--scenario", "--run", "--measurement", "--holdout", "--output"):
        _path(eva, flag)

    upstream = actions.add_parser(
        "handoff", help="Export companion Behavioral Simulation v0.1.0 files"
    )
    for flag in ("--checkpoint", "--scenario", "--run"):
        _path(upstream, flag)
    _path(upstream, "--output-dir")

    rep = actions.add_parser("report", help="Render separate simulation report")
    for flag in ("--checkpoint", "--scenario", "--run", "--output"):
        _path(rep, flag)
    _path(rep, "--measurement", required=False)
    _path(rep, "--validation", required=False)
    return parser


def execute(args: argparse.Namespace) -> None:
    if args.command == "init":
        write_json(args.output, initialize(args.checkpoint, args.episode, args.evidence))
        return
    if args.command == "ssr":
        write_json(args.output, measure(read_json(args.run), read_json(args.vectors)))
        return

    checkpoint, digest = load_checkpoint(args.checkpoint)
    scenario = read_json(args.scenario)
    inspect_scenario(checkpoint, digest, scenario)
    if args.command == "prepare":
        write_json(args.output, prepare(checkpoint, digest, scenario, args.include_verbatim))
        return
    if args.command == "record":
        write_json(args.output,
                   record(checkpoint, digest, scenario, read_json(args.model_output),
                          run_id=args.run_id))
        return

    run = read_json(args.run)
    ensure_run_matches(run, scenario, digest)
    if args.command == "handoff":
        upstream_input = protocol_input(scenario)
        upstream_runs = protocol_runs(run, scenario)
        schema_check(upstream_input, "behavioral-input-v0.1.0.schema.json")
        schema_check(upstream_runs, "behavioral-runs-v0.1.0.schema.json")
        write_json(args.output_dir / "input.json", upstream_input)
        write_json(args.output_dir / "runs.json", upstream_runs)
        return
    if args.command == "evaluate":
        measurement = read_json(args.measurement)
        holdout = read_json(args.holdout)
        write_json(args.output, assess(checkpoint, scenario, run, measurement, holdout))
        return
    if args.command == "report":
        measurement = read_json(args.measurement) if args.measurement else None
        validation = read_json(args.validation) if args.validation else None
        text = render(scenario, run, measurement, validation)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        return
    raise SimulationError("Unknown simulation command")


if __name__ == "__main__":
    parser = configure()
    try:
        execute(parser.parse_args())
    except (SimulationError, OSError, ValueError) as error:
        parser.error(str(error))
