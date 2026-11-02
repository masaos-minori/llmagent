## Goal
- Add the gate mapping entry for the new routing row to `tools/run_validation_gates.py` so `drift_report()` passes (`REQ-005`: gate mapping registered).

## Scope
- In scope: one `Gate` entry in `ROUTING_GATES`. Out of scope: `drift_report()`, hook parity, selection logic, and tests (the existing drift test covers it).

## Assumptions
- Step 3a verification: `ROUTING_GATES` entries are `Gate(name, command, source, mode, patterns)`; `checker_id` derives from the first command's argv; a token containing `<`, `[`, `]`, or `...` makes `requires_context` true, so the run reports `Not available` while the mapping stays (module docstring; `rename_doc` is the precedent with `<old> <new>`). A gate with no `patterns` is never auto-selected.
- The argv must equal the row 06 Run cell tokens exactly: `("uv", "run", "python", "tools/scan_change_consumers.py", "--seed", "<seed>")`, giving id `scan_change_consumers:<seed>` on both sides.
- Overlap (Step 2): `tools/run_validation_gates.py` is also a target of the Plans filed from `flowimp003`, `flowimp005` (changes `drift_report()`, adds seven entries, and a hook-parity check that skips tool-less hooks; this tool has no hook), `flowimp010`, and `flowimp011`. Judged compatible: each adds one entry or touches other functions; whichever lands second rebases. Source plan A6 and A9 record it. If flowimp005 is already applied, the new gate needs no allowlist entry because no hook runs this tool.
- Needs routing row 06 in the same change; `drift` fails if either lands alone.

## Design decisions
- `patterns=()`: a planning-time tool tied to no changed path, so fast mode never auto-selects it. `mode=MODE_FAST`, `source=SOURCE_ROUTING`.

## Alternatives considered
- Path patterns such as `scripts/db/**`: rejected, the trigger is a change class chosen at planning time, not a path set, and a placeholder gate cannot run unattended anyway.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. Locate the `check_workitem_structure` `Gate` in `ROUTING_GATES` by its `name` and insert the new `Gate` after it (the same neighborhood as routing row 06).

### Method
- `Gate(name="scan_change_consumers", command=(("uv","run","python","tools/scan_change_consumers.py","--seed","<seed>"),), source=SOURCE_ROUTING, mode=MODE_FAST, patterns=())`, formatted in the file's one-token-per-line style, with a one-line comment that it is a planning-time candidate scan (manual, placeholder).

### Details
- No other edit: `ROUTING_GATES` is a tuple, so the entry goes inside it before the closing parenthesis of the neighbors.

## Compatibility considerations
- N/A: additive entry; the gate runner reports `Not available` for it at run time by design.

## Security considerations
- N/A: argv list, no shell; the placeholder blocks auto-invocation.

## Rollback considerations
- N/A: revert the commit together with row 06.

## Validation plan
- `uv run python tools/run_validation_gates.py drift` reports no unmapped checker.
- `uv run pytest tests/tools/test_run_validation_gates.py -v`
- `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py`

## Completion criteria
- The entry exists, `drift` and `test_drift_all_routing_checkers_mapped` pass with row 06 applied, and the lint sequence is clean.

## Out of Scope
- Hook parity, selection logic, additional gates, and edits to `tests/tools/test_run_validation_gates.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the `scan_change_consumers` (new) `Gate` entry after `check_workitem_structure` | Completed | 2026-11-02 | 2026-11-02 | Inserted Gate scan_change_consumers (patterns empty, placeholder seed) after check_workitem_structure; files changed: tools/run_validation_gates.py |
| 2 | Run `drift` and `tests/tools/test_run_validation_gates.py` | Completed | 2026-11-02 | 2026-11-02 | drift OK and test_run_validation_gates 56 passed (includes test_drift_all_routing_checkers_mapped); fast-mode run reports the gate Not available by design; full suite deferred to plan end |
| 3 | Run format, ruff, mypy, and bandit on the file (`routing.md` "Adding a new tool") | Completed | 2026-11-02 | 2026-11-02 | ruff format and check clean, mypy clean, bandit 0 medium/high (5 low pre-existing in file); no new gate needs a hook allowlist entry |

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
- **Requirement ID**: `REQ-005` (gate mapping entry)
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080004_flowimp001_consumer-impact-scan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085054
- **Related target files**: tools/run_validation_gates.py
