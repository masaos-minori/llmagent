## Goal

Remove the unused, duplicate `GitServiceError` class definition from
`scripts/mcp_servers/git/git_models.py` so exactly one canonical
`GitServiceError` (`scripts/mcp_servers/git/errors.py`) exists anywhere in the
Git MCP codebase (REQ-001: eliminate the latent isinstance-mismatch risk).

## Scope

- In scope: delete the `GitServiceError` class and its "Domain exceptions"
  section-header comment block from `git_models.py`.
- Out of scope: `errors.py`'s canonical definition (unchanged); any caller
  migration (none needed — confirmed zero references to the duplicate).

## Assumptions

- No assumption beyond the Plan's own (REQ-001, AC-1, AC-2): this class has no
  caller anywhere in `scripts/` or `tests/`.

## Design decisions

- Remove the class and its section-header comment together, rather than
  leaving an empty "Domain exceptions" section header with nothing under it —
  keeps the file free of a dangling, purposeless section divider.

## Alternatives considered

- Keep the class but mark it deprecated/re-export `errors.GitServiceError`
  under the same name: rejected — the Plan's own evidence shows zero callers,
  so a deprecation shim adds a maintenance liability with no migrating caller
  to serve.

## Implementation

### Target file
`scripts/mcp_servers/git/git_models.py`

### Procedure
1. Delete the "Domain exceptions" section-header comment block and the
   `GitServiceError` class definition.
2. Confirm no other symbol in this file references `GitServiceError` after
   removal.

### Method
Direct deletion — no replacement code, no signature change to any other
symbol in the file.

### Details
- Remove lines 68–76 (re-verified 2026-09-05; current content, exact text to
  delete):
  ```python
  # ──────────────────────────────────────────────────────────────────────────────
  # Domain exceptions
  # ──────────────────────────────────────────────────────────────────────────────


  class GitServiceError(RuntimeError):
      """Raised on general git service errors."""


  ```
  (the blank lines immediately before the next section header,
  `# Pydantic schema definitions`, at line 78, should collapse to the file's
  normal two-blank-line separation between sections — do not leave three or
  more consecutive blank lines).
- No import needs updating in this file: `git_models.py` does not import
  `errors.GitServiceError` and does not need to — it never raises or catches
  `GitServiceError` itself.
- Verified this cycle (2026-09-05): `rg -n "GitServiceError"
  scripts/mcp_servers/git/git_models.py` matches only the definition line
  (line 73) — no other line in the file references it, confirming safe
  removal with no follow-on edit required in this file.

## Compatibility considerations

- No external caller exists (confirmed via repo-wide `rg` for
  `git_models.GitServiceError` / `from ... git_models import ... GitServiceError`
  — zero matches), so this is a source-compatible removal: nothing outside
  this file imports the removed symbol.

## Security considerations

- N/A: no change to authorization, validation, or error-handling behavior —
  the canonical `errors.GitServiceError` (already used by every live caller)
  is unaffected.

## Rollback considerations

- Single-file, single-symbol deletion; reverting is a plain `git revert` of
  this file's diff with no data or state migration involved.

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_git_models.py -v` — expect all
  tests to pass with no reference to the removed class (the Plan's own
  investigation confirmed no test imports it; this run confirms it).
- `uv run ruff check scripts/mcp_servers/git/git_models.py`
- `uv run mypy scripts/mcp_servers/git/git_models.py`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- `GitServiceError` is defined exactly once in the Git MCP codebase
  (`scripts/mcp_servers/git/errors.py`).
- `rg -n "class GitServiceError" scripts/mcp_servers/git/` returns exactly one
  match.
- `tests/mcp_servers/git/test_git_models.py` passes unchanged.

## Out of scope

- `scripts/mcp_servers/git/errors.py` (canonical definition — no change).
- `git_service.py`'s separate `RepoValidationResult` class (REQ-005, deferred
  to `gitdispatch`'s Plan per this Plan's own Design section) — unrelated to
  this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `git_models.py`'s duplicate `GitServiceError` class and its section-header comment | Pending | — | — | |
| 2 | Run `tests/mcp_servers/git/test_git_models.py` and confirm no reference to the removed class | Pending | — | — | |
| 3 | Run the validation sequence (ruff, mypy, lint-imports) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` — remove `git_models.py`'s unused duplicate `GitServiceError` declaration
- **Source issue**: issues/20260902-144913_giterrors_consolidate_domain_errors_and_validation_results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-205531
- **Related target files**: scripts/mcp_servers/git/git_models.py
