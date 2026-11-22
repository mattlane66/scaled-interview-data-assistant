"""Run the advisory research router on an explicit local request JSON.

No model calls or external URLs. A real checkpoint is optional; its source
references are validated but human interpretation still is not.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plugin_runtime.operations import propose_transcript_research_route


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    checkpoint = (
        args.checkpoint.read_text(encoding="utf-8") if args.checkpoint else ""
    )
    route = propose_transcript_research_route(request, checkpoint)
    result = json.dumps(route, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
