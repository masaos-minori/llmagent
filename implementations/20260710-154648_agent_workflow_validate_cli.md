# Implementation: `scripts/agent/workflow/validate.py` standalone validation CLI

## Goal

Create a standalone CLI (`python -m agent.workflow.validate <path>`) that validates a workflow-definition JSON file using the existing, already-tested `WorkflowLoader`, without starting any agent/MCP/LLM service.

## Scope

**In:**
- New file `scripts/agent/workflow/validate.py`

**Out:**
- No changes to `scripts/agent/workflow/workflow_loader.py` or its validation rules — this CLI is a thin wrapper only
- No `deploy.sh` wiring (handled by the companion implementation doc for this plan's `deploy.sh` integration step)

## Assumptions

1. `WorkflowLoader.__init__(workflows_dir: Path | None = None)` + `.load(name: str = "default")` builds the target path as `workflows_dir / f"{name}.json"` — calling `WorkflowLoader(workflows_dir=path.parent).load(name=path.stem)` validates an arbitrary file path without any change to `WorkflowLoader`'s public API.
2. `WorkflowLoader.load()` has no network I/O or service-startup side effects (its only imports are `orjson`, `pathlib`, `logging`, `agent.workflow.models`) — already satisfies "must not start the agent or any MCP/LLM service."

## Implementation

### Target file

`scripts/agent/workflow/validate.py` (new file)

### Procedure

1. Create the file with the content below.
2. Confirm `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` exits 0 and prints `OK: ...` against this repo's real `default.json`.
3. Confirm it exits 1 with a `[FATAL]` message against a deliberately malformed scratch JSON file (e.g. missing `retry_policy`).

### Method

Thin CLI wrapper: argument parsing + path-to-name translation + exit-code/message formatting only. All validation logic is delegated to `WorkflowLoader`/`_validate()`.

### Details

```python
#!/usr/bin/env python3
"""agent/workflow/validate.py
Standalone CLI to validate a workflow-definition JSON file at deploy time.
Does not start the agent or any MCP/LLM service.

Usage: python -m agent.workflow.validate <path-to-workflow.json>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.workflow.workflow_loader import WorkflowLoadError, WorkflowLoader


def validate_path(path: Path) -> None:
    """Raise WorkflowLoadError if the workflow file at `path` is invalid."""
    loader = WorkflowLoader(workflows_dir=path.parent)
    loader.load(name=path.stem)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to a workflow definition JSON file")
    args = parser.parse_args()

    try:
        validate_path(args.path)
    except WorkflowLoadError as exc:
        print(f"[FATAL] Invalid workflow definition {args.path}: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {args.path} is a valid workflow definition")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- `validate_path()` is a separate, importable function (not inlined into `main()`) so the companion plan (`plans/done/20260710-153144_plan.md`, metadata printing) can later extend `main()` to retain the returned `WorkflowDef` without restructuring this function.

## Validation plan

```bash
uv run ruff check scripts/agent/workflow/validate.py
uv run mypy scripts/agent/workflow/validate.py
PYTHONPATH=scripts uv run lint-imports
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json
# Negative tests:
echo '{"name": "x"}' > /tmp/bad_workflow.json
PYTHONPATH=scripts uv run python -m agent.workflow.validate /tmp/bad_workflow.json; echo "exit: $?"
echo 'not json' > /tmp/bad_workflow2.json
PYTHONPATH=scripts uv run python -m agent.workflow.validate /tmp/bad_workflow2.json; echo "exit: $?"
```

Expected outcome: exit 0 with "OK: ..." against the real `default.json`; exit 1 with a `[FATAL]` message naming the specific problem for each malformed scratch file; `lint-imports` reports 0 violations (module stays within the `agent` layer).
