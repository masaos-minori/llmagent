## Goal

Edit `tools/run_validation_gates.py`: add the `reason` field to `GateResult`, set it in
`run_gate`, add `--verbose`, call the new renderer, and remove the inline printer so the
runner ends smaller than today.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 2 of the plan's frozen `Implementation Target Files` table:
`tools/run_validation_gates.py` (REQ-001 reason classification in the result model, REQ-003
the `--verbose` flag, REQ-005 the runner shrinks and stays under the size gate, AC-1, AC-3,
AC-5).

## Assumptions
- The renderer it calls is created by the seq 01 document (`tools/_validation_gate_report.py`).
- Plan dependency `wftool004 phase 1` (both Plans edit the runner's import block): at
  procedure-generation time that Plan is held for a design revision (its frozen design cites
  structures absent from the current code). With the current `Gate`-table architecture the
  overlap is limited to the import list; resolve the landing order at implementation time
  and land this edit's single import line after any wftool004 import edit.
- `GateResult` is read by tests only through `status` and `detail` (plan Design), so a
  defaulted new field cannot break constructors.

## Design decisions
- `reason` is a dataclass field with a default (`reason: str = ""`) so every existing
  `GateResult` constructor keeps working (REQ-001, Decision 1).
- `--verbose` is the flag name; `GateResult` stays in the runner (Decisions 3 and 4).

## Alternatives considered
- Carrying the classification in the detail text (rejected in Decision 1); a
  `--show-unrunnable` flag (rejected in Decision 3).

## Implementation
### Target file
`tools/run_validation_gates.py`
### Procedure
Three narrow edits in the order of the plan's Phase 2 step 1 and Phase 3.
### Method
- Add `reason` (new) to `GateResult` with an empty default.
- In `run_gate`: the `requires_context` branch sets `runtime-argument` (new), the
  `FileNotFoundError` branch sets `missing-tool` (new), the `OSError` branch sets `os-error`
  (new); `Pass` and `Fail` results keep the empty default (REQ-001).
- Add `--verbose` to the argument parser (the parser today has `--base`, `--full`, and
  `--jobs` plus the `drift` subcommand); pass the flag and the run's base ref to the new
  renderer; delete the inline `_print_summary` and import `tools/_validation_gate_report.py`
  (REQ-003, REQ-005).
### Details
Gate selection, mappings, the `drift` subcommand, and exit codes MUST NOT change (plan
Out-of-Scope). The file must end below 23988 bytes (AC-5); the four grade-C functions named
in the plan are not touched.

## Compatibility considerations
Existing tests constructing `GateResult` without `reason` keep working (defaulted field);
callers of the runner read only exit codes and the printed summary.

## Security considerations
N/A: no new subprocess or I/O paths; the change is classification data plus rendering
delegation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/run_validation_gates.py drift` — parity (REQ: mappings unchanged).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — runner smaller than 23988 B (AC-5).
- `uv run python tools/run_validation_gates.py` and the same with `--verbose` — default hides runtime-argument rows and prints the count line; `--verbose` shows them (AC-2, AC-3).
- `uv run pytest tests/tools/test_run_validation_gates.py -v` — reason classification and `--verbose` tests pass (AC-1, AC-3).

## Completion criteria
`run_gate` returns the three `Not available` reasons exactly as in AC-1; `--verbose` changes
only display, not selection or exit codes; the inline printer is gone, the runner imports the
renderer, and its byte size is below 23988 (AC-1, AC-3, AC-5).

## Out of Scope
The renderer module (seq 01); tests (seq 03); documentation (seq 04, 05); the gate tables and
`drift` behavior; the `--fast`/stop-on-first-Fail prose drift recorded as UNK-02 (follow-up
issue, not this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `reason` field and set it in `run_gate` | Pending | — | — | plan Phase 2 |
| 2 | Add `--verbose`, call the renderer, remove the inline printer | Pending | — | — | plan Phase 3; import-block landing order per Assumptions |
| 3 | Run the validation sequence (`rules/toolchain.md`), drift, size gate, smoke runs | Pending | — | — | plan Phase 5 |

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
- **Requirement ID**: `REQ-001` (reason classification), `REQ-003` (`--verbose`), `REQ-005` (runner shrinks)
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125737_wftool006_gate-output-noise.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-201532
- **Related target files**: `tools/run_validation_gates.py`
