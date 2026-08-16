# `pyproject.toml` coverage `omit` list references pre-rename `*_server.py` paths that no longer exist

## Priority
Medium

## Summary
`pyproject.toml`'s `[tool.coverage.run] omit` list still contains
`scripts/mcp_servers/{github,shell,web_search,rag_pipeline}/server.py`, but these files were
renamed to `github_server.py`/`shell_server.py`/`web_search_server.py`/`rag_pipeline_server.py`
in an earlier package-rename commit (`7ffa728ac`, resolving a `mcp` PyPI package-name collision).
Only `scripts/mcp_servers/file/*_server.py` (a glob) still matches its intended targets. As a
result, these 4 files are silently **not** omitted from coverage measurement, contradicting the
comment above the list ("FastAPI server entry points ... not unit-testable").

## Reason for Change
Discovered during a `prompts/04_refactor.md` cycle on `scripts/mcp_servers/shell/shell_server.py`
(2026-08-16): `coverage report --include=".../shell_server.py"` returned real percentages (70%,
then 92% after adding characterization tests) instead of the expected "No data to report" the
other `*_server.py` cycles observed for `scripts/mcp_servers/file/*_server.py`. This is a
project-wide config/reality mismatch, not specific to one file, and it invalidates any prior
assumption that these 4 files are coverage-exempt.

## Implementation Intent
Reconcile the omit list with the current filenames. Two valid directions — pick one explicitly:
1. Update the 4 stale glob entries to the current filenames (`shell_server.py`,
   `github_server.py`, `web_search_server.py`, `rag_pipeline_server.py`) to restore the original
   "not unit-testable, omit them" intent, or
2. Keep them measured (since endpoint-level `TestClient` tests already exist for at least
   `shell_server.py`/`web_search_server.py` as of 2026-08-16) and remove the stale entries
   entirely, documenting that these particular server files are unit-testable via `TestClient`.

Do not silently pick a direction without checking whether the existing coverage percentage for
these 4 files is already reasonable (it may already be, per the 2026-08-16 findings) — that
should inform which of the two directions is chosen.

## Target Files or Areas
- `pyproject.toml` (`[tool.coverage.run] omit`)
- `rules/toolchain.md` / `skills/python-refactoring/workflow.md` if they document the omit
  rationale and need updating to match the chosen direction

## Required Changes
- Decide (direction 1 vs 2 above) and update `pyproject.toml`'s omit list accordingly.
- Run `uv run coverage run -m pytest tests/mcp_servers/` + `uv run coverage report` before and
  after to confirm the repo-wide coverage percentage changes as expected for the chosen
  direction (drops if re-omitted, stays the same if kept measured).

## Acceptance Criteria
- `pyproject.toml`'s omit list contains no path that fails to match any file on disk (verify via
  `for p in <omit-list-entries>; do ls $p 2>/dev/null || echo "STALE: $p"; done` equivalent).
- Repo-wide `coverage report` reflects the intended, chosen behavior for these 4 files.

## Testing Expectations
Run `uv run coverage run -m pytest tests/` + `uv run coverage report` before/after; no test
behavior changes, only coverage instrumentation scope.

## Documentation Impact
If direction 2 is chosen (keep measured), update the inline comment above the omit list
("FastAPI server entry points — start HTTP servers; not unit-testable") since it would no
longer be accurate for these 4 files.

## Out of Scope
- Do not change `scripts/mcp_servers/file/*_server.py`'s omit entry (still correctly matches).
- Do not add or remove characterization tests as part of this issue — that is a separate,
  per-file refactor concern.

## AI Implementation Instruction
Verify current file paths with `find scripts/mcp_servers -name "*_server.py"` before editing
the omit list. State which direction (re-omit vs. keep-measured) was chosen and why in the PR
description. Do not touch unrelated omit entries (`scripts/db/create_schema.py`,
`scripts/agent.py`, etc.).
