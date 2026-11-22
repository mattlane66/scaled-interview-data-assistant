"""Create evidence-grounded cross-episode research maps; no model or external API calls."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulation.core import (  # noqa: E402
    SimulationError,
    load_checkpoint,
    read_json,
    write_json,
)
from simulation.mechanism_map import (  # noqa: E402
    compile_map,
    inventory,
    make_study,
    planning_handoff,
    render_map,
)


def _path(command: argparse.ArgumentParser, name: str, *, required: bool = True) -> None:
    command.add_argument(name, type=Path, required=required)


def parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="command", required=True)

    init = actions.add_parser("init", help="Create an explicitly unreviewed hypothesis study")
    _path(init, "--checkpoint")
    _path(init, "--output")
    group = init.add_mutually_exclusive_group(required=True)
    group.add_argument("--cluster")
    group.add_argument("--episode", action="append")

    preview = actions.add_parser("inventory", help="Inspect source evidence before review")
    _path(preview, "--checkpoint")
    _path(preview, "--study")
    _path(preview, "--output")

    compiled = actions.add_parser(
        "compile", help="Produce a provisional map from an approved human-coded study"
    )
    _path(compiled, "--checkpoint")
    _path(compiled, "--study")
    _path(compiled, "--output")
    _path(compiled, "--report", required=False)
    _path(compiled, "--planning-handoff", required=False)
    return parser


def main(args: argparse.Namespace) -> None:
    checkpoint, digest = load_checkpoint(args.checkpoint)
    if args.command == "init":
        scope = (
            {"kind": "CLUSTER", "cluster_id": args.cluster}
            if args.cluster else
            {"kind": "EPISODES", "episode_ids": args.episode}
        )
        write_json(args.output, make_study(checkpoint, digest, scope))
        return

    study = read_json(args.study)
    if args.command == "inventory":
        write_json(args.output, inventory(checkpoint, digest, study))
        return
    if args.command == "compile":
        mapped = compile_map(checkpoint, digest, study)
        write_json(args.output, mapped)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(render_map(mapped), encoding="utf-8")
        if args.planning_handoff:
            write_json(args.planning_handoff, planning_handoff(mapped))
        return
    raise SimulationError("Unknown command")


if __name__ == "__main__":
    parser = parse()
    try:
        main(parser.parse_args())
    except (OSError, ValueError, SimulationError) as exc:
        parser.error(str(exc))
