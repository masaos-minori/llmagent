#!/usr/bin/env python3
"""scripts/agent/workflow/validate.py

Standalone CLI to validate a workflow-definition JSON file at deploy time.
Does not start the agent or any MCP/LLM service.

Usage: python -m agent.workflow.validate <path-to-workflow.json>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.commands.output_port import CliOutputPort
from agent.output_tags import OutputTag
from agent.workflow.models import WorkflowDef
from agent.workflow.workflow_loader import WorkflowLoader, WorkflowLoadError


def validate_path(path: Path) -> WorkflowDef:
    """Return the loaded WorkflowDef, or raise WorkflowLoadError if invalid."""
    loader = WorkflowLoader(workflows_dir=path.parent)
    return loader.load(name=path.stem)


def main() -> int:
    """Validate a workflow definition JSON file against the schema."""
    port = CliOutputPort()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path", type=Path, help="Path to a workflow definition JSON file"
    )
    parser.add_argument(
        "--print-metadata",
        action="store_true",
        help="On success, also print name/version/stage IDs",
    )
    args = parser.parse_args()

    try:
        wdef = validate_path(args.path)
    except WorkflowLoadError as exc:
        port.write_stderr(f"{OutputTag.FATAL} Invalid workflow definition {args.path}: {exc}")
        return 1

    port.write(f"OK: {args.path} is a valid workflow definition")
    if args.print_metadata:
        port.write(f"Name     : {wdef.name}")
        port.write(f"Version  : {wdef.version}")
        port.write(f"Stages   : {', '.join(s.id for s in wdef.stages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
