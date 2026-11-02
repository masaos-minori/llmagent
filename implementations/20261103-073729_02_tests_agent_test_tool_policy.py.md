# Implementation Procedure: tests/agent/test_tool_policy.py (shellrisk001)

## Goal
- Add the `--flag=value` path-candidate regression tests to `tests/agent/test_tool_policy.py`
  (REQ-003; AC-3, AC-4), executed as the red baseline before the code change in the sibling
  document `implementations/20261103-073729_01_scripts_agent_tool_policy.py.md`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Sequencing (Plan Execution Status note on step 1): execute the test additions FIRST —
  the escalation tests must FAIL against the current `_check_positional_args`, and the
  recorded failures are the red baseline (AC-3) for seq 01. After seq 01 lands, the whole
  file passes.
- Reconciliation the Plan requires (its ordering bullet): after the shellprefix001
  procedures (`implementations/20261103-072856_*`) are implemented, `python` and `pytest`
  commands are no longer auto-approval candidates and `git diff --output=<file>` is
  rejected by the git safe-shape rule. Primary escalation cases therefore use commands
  that still reach `_check_positional_args`: `cat --file=/etc/shadow`,
  `grep --include=/etc/shadow x`, `ls --ignore=/etc` (read-only executables with
  path-taking flags). Keep `git diff --output=/etc/x` as a high pin (it passes through
  the git rule, not through this fix). Record the deviation from the Plan's example
  executables in the implementation cycle notes.
- This file is also the target of `implementations/20261103-072856_03_tests_agent_test_tool_policy.py.md`
  (shellprefix001); keep edits disjoint — this document only adds the new class, and the
  shellprefix001 document only adds `TestShellSafeShape` and migrates the three A7 pins.

## Design decisions
- New class `TestFlagValuePathCandidates` (new) placed beside the existing `shell_run`
  positional tests (`test_cat_protected_path_escalates`,
  `test_cat_outside_allowed_root_escalates`,
  `test_positional_arg_value_error_in_resolve_escalates`,
  `test_flag_only_no_positional_routing_needed`), reusing the file's `_cfg` builder.

## Alternatives considered
- Adding the cases to the existing positional-test class — rejected: the new extraction
  rule deserves its own named group for the Plan's AC-3 red-baseline recording.

## Implementation
### Target file
- `tests/agent/test_tool_policy.py`

### Procedure
1. Add class `TestFlagValuePathCandidates` (new) with tests (all names (new)):
   - `test_flag_value_protected_path_escalates` — `cat --file=/etc/shadow` → `high`.
   - `test_flag_value_outside_allowed_root_escalates` — `grep --include=/etc/shadow x`
     and `ls --ignore=/etc` → `high`.
   - `test_flag_value_parity_with_separate_token` — each escalation case asserted equal
     to its space-separated form (already `high` today).
   - `test_flag_value_in_root_stays_none` — `cat --file=<in-root path>` → `none`.
   - `test_flag_value_non_path_stays_none` — `ls --ignore=*.py` (in-root cwd) → `none`
     (candidate resolves to an in-root path; fail-closed parity documented).
   - `test_bare_flag_and_empty_value_stay_none` — `ls --ignore`, `ls --ignore=` → `none`.
   - `test_flag_value_nul_escalates` — `cat --file=x` with an embedded NUL → `high`
     (escalates through the existing `ValueError` branch).
   - `test_git_diff_output_flag_high_pin` — `git diff --output=/etc/x` → `high` pin
     (reaches `high` via the shellprefix001 git rule once that Plan lands; recorded as a
     deviation note until then).
2. Record the baseline: run the file and record which new tests fail pre-change in the
   Execution Status Notes (Plan step 2; AC-3).

### Method
- Set `allowed_root` to a `tmp_path` and `monkeypatch.chdir` it for every relative-value
  test (Plan Risks mitigation: no dependence on the process cwd).
- No test executes a command; all tests call `classify_risk(cfg, "shell_run", {"command": ...})`.

### Details
- Keep every pre-existing test byte-identical (AC-2).

## Compatibility considerations
- Existing `TestPrefixCollision` and positional tests unchanged; the new class only adds
  escalations and `none` pins.

## Security considerations
- N/A: test-only change; the red baseline pins the `--flag=value` bypass before the fix.

## Rollback considerations
- N/A: revert the commit; reverts together with seq 01.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py -q` — before seq 01: exactly the new
  escalation tests fail (baseline recorded); after seq 01: whole file green (AC-1, AC-3).
- `uv run ruff check tests/agent/test_tool_policy.py` — clean.

## Completion criteria
- Red baseline recorded; after seq 01: all new tests pass, every pre-existing test is
  unchanged and green (AC-2, AC-4).

## Out of Scope
- `_iter_path_candidates` implementation — seq 01 document.
- `TestShellSafeShape` and the three A7 pin migrations — shellprefix001 seq 03 document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestFlagValuePathCandidates`; record red baseline | Pending | — | — | Execute after the shellprefix001 procedures land; before seq 01 (Plan phase order) |
| 2 | Re-run validation after seq 01 lands (whole file green) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (`--flag=value` regression tests)
- **Source issue**: issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142514_shellrisk001_shell-risk-check-misses-flag-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-073729
- **Related target files**: `tests/agent/test_tool_policy.py`
