# Implementation: Delete Obsolete Stub Files

## Goal

Delete three stub/obsolete files from `scripts/agent/` that are confirmed to have no live import paths.

## Scope

**In:**
- Delete `scripts/agent/repl_debug.py` (split-notice stub only)
- Delete `scripts/agent/context_detection.py` (obsolete two-stage context detection)
- Delete `scripts/agent/rag_debug.py` (not imported by any live code)

**Out:**
- Deleting `scripts/mcp/rag/server.py` `rag_debug_pipeline` (MCP tool — different file, unrelated)

## Assumptions

- `scripts/agent/repl_debug.py`: contains only a comment saying it has been split into `rag_debug.py` and `context_detection.py`
- `scripts/agent/context_detection.py`: two-stage context detection helper — not imported by any current code path (confirmed by `grep`)
- `scripts/agent/rag_debug.py`: in `scripts/agent/` only; `scripts/mcp/rag/` has a different, active `rag_debug_pipeline` tool — do not confuse them
- No test file imports these three files directly

## Implementation

```bash
# 1. Verify no imports exist before deletion
grep -r "from agent.repl_debug" scripts/ tests/
grep -r "from agent.context_detection" scripts/ tests/
grep -r "from agent.rag_debug" scripts/ tests/
# Expected: no output (zero matches)

# 2. Delete the files
rm scripts/agent/repl_debug.py
rm scripts/agent/context_detection.py
rm scripts/agent/rag_debug.py

# 3. Run full test suite to confirm nothing breaks
uv run pytest -v
```

## Validation plan

```bash
uv run ruff check scripts/
uv run mypy scripts/
uv run pytest -v
```

Confirm:
- `pytest` passes with zero new failures
- `mypy` reports no "Module not found" errors related to the deleted files
- `grep -r "repl_debug\|context_detection\|rag_debug" scripts/` returns zero matches in `scripts/agent/` (MCP rag_debug_pipeline hits are acceptable and expected)
