#!/usr/bin/env bash
# tools/close_procedure.sh — mark every step of an implementation procedure
# Completed for a given date, then archive it to implementations/done/.
# Usage: close_procedure.sh <procedure-doc> <YYYY-MM-DD> [--note N:TEXT]...
# Extracted 2026-10-25 per AGENTS.md rule 7 (the set_execution_status +
# close-implementation pair ran 3+ times in one batch).
set -euo pipefail
doc="$1"; date="$2"; shift 2
uv run python tools/set_execution_status.py "$doc" --all --date "$date" "$@"
uv run python tools/manage_workitem_stage.py close-implementation "$doc"
