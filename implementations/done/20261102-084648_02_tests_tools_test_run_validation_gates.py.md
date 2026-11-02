## Goal
- Cover the new drift behavior (`REQ-001`: unmapped, allowlisted, malformed, reasonless entries) and the trigger selection of the seven new gates (`REQ-002`: patterns mirror hook filters).

## Scope
- In scope: new test functions and import additions in `tests/tools/test_run_validation_gates.py`. Out of scope: any production code; the existing drift tests stay unchanged.

## Assumptions
- The names `parse_precommit_hooks`, `COMMIT_ONLY_HOOKS`, and the `drift_report(routing_text, precommit_text)` second parameter are created by the earlier-`seq` procedure for `tools/run_validation_gates.py` (row 01) and will exist when `code-implementation` runs the rows in order.
- Step 3a: the existing tests `test_drift_all_routing_checkers_mapped`, `test_drift_reports_unmapped_checker`, and `test_selection_*` are present and still valid; `ROUTING_MD` is already defined at module level.
- Overlap (Step 2): no other open Plan targets this test file.

## Design decisions
- Tests drive `drift_report` with synthetic config text, never the live file, except one live-repo test that asserts the real config produces no drift.

## Alternatives considered
- Parametrize the seven trigger cases in one test instead of seven functions; keeps the file small and the fixture table next to the hook filters it mirrors.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`

### Procedure
- Extend the `from tools.run_validation_gates import (...)` block with `COMMIT_ONLY_HOOKS` and `parse_precommit_hooks` (both created by the row 01 procedure).
- Add a `# --- hook parity (REQ-001) ---` section after `test_drift_ignores_the_orchestrators_own_row`.
- Add a `# --- new gate triggers (REQ-002) ---` section after the existing `test_selection_*` tests.

### Method
- Drift tests (use a helper `_hook_config(entry)` that builds a one-hook YAML string): (1) unmapped tool-backed hook `python -m tools.nonexistent_checker_xyz` makes `count >= 1` and the message names the hook id; (2) the same hook is not reported when a monkeypatched `COMMIT_ONLY_HOOKS` lists its id with a reason; (3) malformed YAML (`repos: [`) yields an error, and a mapping without `repos` yields an error; (4) an allowlist entry with an empty reason yields an error; (5) a non-tool hook (`bash -c ...`, `uv run mypy ...`) and a hook with no `entry` are ignored; (6) a hook naming `tools.run_validation_gates` is skipped; (7) each entry form in the live config parses to a mapped id (`python -m tools.x`, `uv run python -m tools.x`, entry with a trailing flag); (8) the live `.pre-commit-config.yaml` plus `routing.md` produce zero drift errors; (9) every `COMMIT_ONLY_HOOKS` reason is non-blank.
- Trigger tests, parametrized over `(path, gate name)`: `docs/10_adr/adr_01_index.md` selects `check_adr_invariant_matrix`, `check_adr_reference`, `check_adr_structure`; `scripts/x.py` selects the same three; `routing.md` (root level) selects the three; `docs/a.md` and `docs/sub/a.md` select `check_known_deviation_sync`; `plans/p.md` selects `check_plan_target_overlaps`; `tests/conftest.py` and `tests/agent/conftest.py` select `check_conftest_integrity`; `issues/i.md`, `plans/done/p.md`, `implementations/i.md` select `check_workitem_traceability`; (corrected in Step 3b of row 01: that gate is full-mode only, so the trigger test selects in full mode and a separate test asserts it is absent from the fast selection) `assets/logo.png` selects none of the seven.
- AC-3 fixture: changed files include `docs/10_adr/adr_01_index.md` (the ADR that cites the removed test); assert `check_adr_invariant_matrix` is in `select_gates(..., MODE_FAST)` and that `run_gate` with `_runner_for(1)` (the existing injected runner helper) returns status `Fail`.

### Details
- Command test: the `check_workitem_traceability` gate's `checker_id` equals `check_workitem_traceability:--active-only`, matching the hook-derived id.
- If row 01 introduces the full-mode-only guard, add a test that a gate with `mode=MODE_FULL` is absent from the fast selection and present in the full selection.

## Compatibility considerations
N/A: test-only file; no contract or persisted data.

## Security considerations
N/A: tests use synthetic strings and a runner double; no subprocess or network.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -v`.
- `uv run ruff format tests/tools/test_run_validation_gates.py`; `uv run ruff check tests/tools/test_run_validation_gates.py`; `uv run mypy tests/tools/test_run_validation_gates.py` if the test tree is in the mypy scope.

## Completion criteria
- Every new test passes against the row 01 implementation and fails against the pre-change `drift_report` (spot check by temporarily stubbing the second parameter).
- The AC-3 fixture test and the unmapped, allowlisted, malformed-config, and blank-reason cases exist.

## Out of Scope
- Production code changes belong to the row 01 document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-092223 | 20261102-092223 | Add the two test sections and imports Stale check clean after row 01 landed. Changed: tests/tools/test_run_validation_gates.py. Step 3b: workitem trigger test uses full mode (gate is full-mode only); full-mode-only guard test added. Full suite deferred to plan end |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-092223 | 20261102-092223 | pytest on this file, ruff, mypy pytest 56 passed; ruff format/check clean; mypy clean (1 file); testmon-forceselect 56 passed + known mdq env failure |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261030-191302_flowimp005_gates-hook-parity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075445_flowimp005_gates-hook-parity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084648
- **Related target files**: tests/tools/test_run_validation_gates.py