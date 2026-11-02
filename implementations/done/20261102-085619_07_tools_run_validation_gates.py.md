## Goal
- Add the gate mapping entry for the new routing row to `tools/run_validation_gates.py` so `drift_report()` passes (`REQ-005`: gate mapping registered).

## Scope
- In scope: one `Gate` entry in `ROUTING_GATES`. Out of scope: `drift_report()`, selection logic, other gates, and tests (`tests/tools/test_run_validation_gates.py` already checks drift against the real `routing.md`).

## Assumptions
- Step 3a verification: `ROUTING_GATES` entries are `Gate(name, command, source, mode, patterns)`; `checker_id` derives from the first command's argv; a token containing `<`, `[`, `]`, or `...` makes `requires_context` true, so a run reports `Not available` while the mapping stays (module docstring; `check_docs_structure` is the precedent with `"[glob", "...]"`). `tests/tools/test_run_validation_gates.py` has no gate-count assertion.
- The argv MUST equal row 06's Run cell tokens: `("uv", "run", "python", "tools/classify_changes.py", "[--status-file", "<path>]")`, giving id `classify_changes:[--status-file` on both sides.
- Decision (follows the Plan's statement that the gate is reported `Not available`): `patterns=("tools/classify_changes.py", "skills/git-commit-and-sync/**")`, so fast mode selects it when the tool or its skill changes and reports `Not available` (placeholder). Falsifiable if the owner prefers a never-selected gate (`patterns=()`).
- Overlap (Step 2): `tools/run_validation_gates.py` is also a target of `flowimp011` (and per Plan A6 of `flowimp001`, `flowimp003`, `flowimp004`, `flowimp005`). Judged compatible: each adds one entry or touches other functions; the later one rebases. If `flowimp005`'s hook-parity check is already applied, no hook runs this tool, so no allowlist entry is needed.
- Needs row 06 in the same change; `drift` fails if either lands alone.

## Design decisions
- `mode=MODE_FAST`, `source=SOURCE_ROUTING`; one-token-per-line formatting like the neighbors.

## Alternatives considered
- `patterns=()`: kept as the fallback if the owner finds the `Not available` row noisy.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. In `ROUTING_GATES`, insert the new `Gate` after the `check_workitem_structure` entry, named `classify_changes` (new).

### Method
- `Gate(name="classify_changes", command=(("uv", "run", "python", "tools/classify_changes.py", "[--status-file", "<path>]"),), source=SOURCE_ROUTING, mode=MODE_FAST, patterns=("tools/classify_changes.py", "skills/git-commit-and-sync/**"))`, formatted by `ruff format`.

### Details
- No other edit; the entry sits inside the tuple. Run the tool lint sequence for this file after the edit.

## Compatibility considerations
- Additive entry; fast-mode runs that touch the tool or the skill gain one `Not available` row, which Phase 4 already treats as not a failure.

## Security considerations
N/A: the entry is never executed with a placeholder argument.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/run_validation_gates.py drift`: OK (with row 06); `uv run pytest tests/tools/test_run_validation_gates.py -v`: passes.
- `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py`.

## Completion criteria
- The entry exists, its argv matches row 06, drift passes, and lint, type, and security checks are clean.

## Out of Scope
- `drift_report()` changes, hook parity, other gates, the routing row (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tools/run_validation_gates.py`: add the `classify_changes` (new) entry to `ROUTING_GATES` | Completed | 20261102-141535 | 2026-11-02 | Added classify_changes Gate; files: tools/run_validation_gates.py; landed with row 06 |
| 2 | Run drift, `tests/tools/test_run_validation_gates.py`, and the tool lint sequence on the file | Completed | 2026-11-02 | 2026-11-02 | drift OK; test_run_validation_gates + test_classify_changes 81 passed; ruff, mypy clean; bandit findings in file are pre-existing subprocess lines, none from the new entry; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-005`; acceptance `AC-6`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: tools/run_validation_gates.py
