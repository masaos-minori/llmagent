## Goal

Create `tools/_validation_gate_report.py` (new): the gate-summary renderer that hides
runtime-argument `Not available` rows by default, prints their count and the flag that shows
them, keeps every other row visible, and prints the base ref the run actually used.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 1 of the plan's frozen `Implementation Target Files` table:
`tools/_validation_gate_report.py` (REQ-002 hide-by-default with count line, REQ-003 verbose
form, REQ-004 real base in the header, REQ-005 the renderer moves out of the runner and
stays below grade C, AC-2 to AC-5).

## Assumptions
- The per-row classification this renderer hides on comes from the `reason` field the seq 02
  document adds to `GateResult` (plan REQ-001); this document reads it, does not define it.
- `GateResult` stays in the runner (Decision 4), so this module must not import the runner at
  runtime: type the results through `if TYPE_CHECKING: from tools.run_validation_gates import GateResult`
  or duck-type on `name`, `status`, `command`, `detail`, and `reason`. The runner imports
  this module; no cycle.
- The printed header and summary have no consumer in the repository (plan Design, Dependency
  graphing), so changing the default output affects only a reader.

## Design decisions
- Hide only `runtime-argument`: a `missing-tool` or `os-error` row is a check that did not
  run and stays visible (`rules/ai-execution.md` item 12; Decision 2).
- A count line plus the flag name in the default output replaces the hidden rows; no count
  line when nothing was hidden (REQ-002).
- The header receives the run's base as a parameter instead of a fixed `master` text
  (Decision 5).

## Alternatives considered
- Matching the existing detail text instead of a reason field (rejected in Decision 1: a
  reworded message would silently change what is hidden); hiding every `Not available`
  (rejected in Decision 2); a dedicated `--show-unrunnable` flag (rejected in Decision 3).

## Implementation
### Target file
`tools/_validation_gate_report.py` (new)
### Procedure
Move the body of the runner's `_print_summary` into this module as `render_summary` (new),
gain the hide rule, count line, verbose form, and base parameter, and keep every function
below radon grade C and the file under the 24576-byte gate (REQ-005).
### Method
- Signature shape: results list, changed-file list, mode, base ref, verbose flag. The runner
  calls it once per run.
- Default: drop rows whose reason is `runtime-argument`; when any are dropped print exactly
  one count line naming the count and `--verbose`; `Pass`, `Fail`, `Partial`, `Blocked`, and
  the other `Not available` rows print as today.
- `verbose=True`: print every row including the runtime-argument rows with their detail
  (REQ-003).
- Header line prints the passed base ref (REQ-004); keep the existing canonical-vocabulary
  framing (`rules/ai-execution.md` item 11) unchanged.
### Details
No imports of other tool modules beyond the type-checking import in Assumptions; mode and
base arrive as strings.

## Compatibility considerations
Only a reader consumes the summary today; `tools/run_validation_gates.py` (seq 02) and
`tests/tools/test_run_validation_gates.py` (seq 03) are the only importers/tests. The
`drift` subcommand and gate selection do not pass through this module.

## Security considerations
N/A: pure formatting of already-collected results; no subprocess, no file write.

## Rollback considerations
N/A: revert the commit (the file is new; the runner's inline printer returns with it).

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -v` — renderer cases pass (AC-2,
  AC-3, AC-4).
- `uv run radon cc tools/_validation_gate_report.py -s -n C` — reports nothing.
- `uv run bandit tools/_validation_gate_report.py` — clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — passes for the new file.

## Completion criteria
Default output omits runtime-argument rows and prints the count line only when rows were
hidden; `--verbose` output equals the full row set; the header shows the run's base; the
runner's import of this module replaces the inline printer and both files pass the size gate
(AC-2 to AC-5).

## Out of Scope
`GateResult` and the `reason` field (seq 02); parser flags in the runner (seq 02); test
modules (seq 03); documentation rows (seq 04, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the renderer per Procedure/Method/Details after the seq 03 tests (plan Phase 1) and the seq 02 `reason` field land | Completed | — | 20261117-231500 | plan Phase 2 render_summary created; reason read from GateResult, TYPE_CHECKING import only |
| 2 | Run the validation sequence (`rules/toolchain.md`) for this module | Completed | — | 20261117-231500 | plan Phase 5 pytest 98 passed; radon -n C empty after splitting render_summary into 3 funcs (was C 11); bandit clean; mypy clean; size gate OK |

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
- **Requirement ID**: `REQ-002` (hide-by-default output), `REQ-003` (verbose form), `REQ-004` (real base header), `REQ-005` (module home and limits)
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125737_wftool006_gate-output-noise.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-201532
- **Related target files**: `tools/_validation_gate_report.py`