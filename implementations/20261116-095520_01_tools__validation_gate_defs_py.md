## Goal

Add a fast-mode routing gate to `ROUTING_GATES` in `tools/_validation_gate_defs.py`
that runs `ruff format --check` then `ruff check` on the changed `scripts/` Python
files, so `tools/run_validation_gates.py`'s fast mode can fail locally on a ruff
regression before push (`REQ-001`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

Data-only change to `tools/_validation_gate_defs.py` only. The orchestrator half that
expands the changed-file sentinel into the ruff argv lives in
`tools/run_validation_gates.py` (sibling document). No signature, constant, helper, or
other symbol in this module changes.

## Assumptions

- `Gate` is a frozen `@dataclass` whose `command` is a tuple of argv tuples and whose
  `requires_context` returns `True` only when a token matches the placeholder regex
  `[<\[\]]|\.\.\.` (see `_PLACEHOLDER_TOKEN_RE`, line 122). A token without `<`, `[`,
  `]`, or `...` therefore keeps `requires_context` `False`.
- `checker_id` derives from `command[0]` via `_checker_id_from_command`: when no token
  carries a `tools/<name>.py` match it returns the first token verbatim (line 67). With
  `("uv", "run", "ruff", ...)` that is `uv`.
- The two-command form mirrors the existing `ruff-format-lint` toolchain gate
  (lines 140-148); `run_validation_gates.py` stops at the first non-zero exit, so a
  format finding fails before the check runs.

## Design decisions

- **Sentinel marks the changed-file position, not a placeholder.** The static
  `Gate.command` carries the literal token `__CHANGED_FILES__` (no `<`, `[`, `]`, `...`),
  so `requires_context` stays `False` and the gate is auto-runnable rather than reported
  `Not available`. The orchestrator (sibling document) substitutes the changed `scripts/`
  paths for this token at run time.
- **`checker_id` is the auto-derived `uv`.** With no `tools/<name>.py` token the id is
  the first token, `uv`. It is currently unique among the 43 routing gates (none derive
  to `uv`), and the matching `routing.md` Run cell derives to the same `uv`, so the drift
  invariant holds (`REQ-005`).

## Alternatives considered

- **A `tools/` helper (Design 2).** A small scoped-ruff helper under `tools/` that
  imports `_changed_files` and runs ruff itself. Rejected: a new tool triggers the
  "Adding a new tool" routing.md sequence (`check_tool_descriptions_sync` /
  `tools/TOOL_DESCRIPTIONS.md`) and the `tools/` size baseline; Design 1 keeps the change
  to existing tools only and most literally reuses the orchestrator's own changed-file
  selection.
- **A full-mode toolchain gate.** Rejected: fast mode is what `git-commit-and-sync`
  Phase 4 runs by default, and the issue requires the local check there.

## Implementation
### Target file
`tools/_validation_gate_defs.py`

### Procedure
1. Append one `Gate` to the end of the `ROUTING_GATES` tuple (after the
   `check_workitem_traceability` gate, near line 759).

### Method
- Add the gate with `mode=MODE_FAST`, `source=SOURCE_ROUTING`, and the script patterns:
  ```python
  Gate(
      name="ruff_format_check_changed",
      command=(
          ("uv", "run", "ruff", "format", "--check", "__CHANGED_FILES__"),
          ("uv", "run", "ruff", "check", "__CHANGED_FILES__"),
      ),
      source=SOURCE_ROUTING,
      mode=MODE_FAST,
      patterns=("scripts/*.py", "scripts/**/*.py"),
  ),
  ```
  Place it after the `check_workitem_traceability` gate and before the closing `)` of
  `ROUTING_GATES`. Match the surrounding multi-line `Gate(...)` style and trailing-comma
  convention.

### Details
- `name` is `` `ruff_format_check_changed` (new) `` (unique; used as the summary label and by tests).
- `patterns=("scripts/*.py", "scripts/**/*.py")` selects the gate when a changed path
  matches either glob, exactly as the plan's affected-areas analysis records.
- The sentinel `__CHANGED_FILES__` sits where the file list belongs in each argv; the
  orchestrator sibling expands it to the changed `scripts/` paths (`REQ-004`).
- Do not touch `TOOLCHAIN_GATES`, the constants, the helpers, or the `Gate` dataclass.

## Compatibility considerations

- Additive tuple member only. `run_validation_gates.py` iterates `_ALL_GATES`
  (`(*ROUTING_GATES, *TOOLCHAIN_GATES)`); a new tuple member cannot break callers. Blast
  radius is confined to this module's importers.

## Security considerations

N/A: no authentication, authorization, or input-handling change.

## Rollback considerations

Revert this single commit; the added `Gate` is new and touches no runtime data shape.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py` — the new gate appears in
  `ROUTING_GATES`, `mode==MODE_FAST`, `patterns` contains `scripts/*.py`,
  `requires_context is False`, and `checker_id == "uv"` (`REQ-001`, `REQ-003`, `REQ-004`).
- `uv run ruff check tools/_validation_gate_defs.py`; `uv run mypy tools/` — clean.
- Manual: run the fast gate against a `scripts/` file carrying a deliberate `I001`
  error (reverted after) and confirm it reports `Fail` and names the file (`AC-001`).

## Completion criteria

- The gate exists in `ROUTING_GATES` with `mode=MODE_FAST`, `patterns=("scripts/*.py",
  "scripts/**/*.py")`, the non-placeholder `__CHANGED_FILES__` sentinel, and
  `checker_id == "uv"` (`REQ-001`, `REQ-003`, `REQ-004`).
- It maps to a `routing.md` row so the drift invariant stays green (`REQ-005`, sibling
  document).

## Out of Scope

- Expanding the sentinel into the changed `scripts/` paths (orchestrator sibling
  document).
- Adding the `routing.md` drift row, the unit tests, and the `rules/toolchain.md` doc
  (separate documents).
- Any other CI `lint` step (mypy, bandit, architecture, security).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the fast-mode ruff routing `Gate` to `ROUTING_GATES` in `tools/_validation_gate_defs.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261115-183024_lintgate001_ruff-check-local-gate.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-202908_lintgate001_ruff-check-local-gate.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095520
- **Related target files**: `tools/_validation_gate_defs.py`
