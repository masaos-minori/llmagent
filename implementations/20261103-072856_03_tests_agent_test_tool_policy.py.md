# Implementation Procedure: tests/agent/test_tool_policy.py (shellprefix001)

## Goal
- Add the `classify_risk` regression tests for the `shell_run` safe-shape policy using the
  shipped config values (REQ-011: reproduction commands not auto-approved, read-only forms
  preserved), and migrate the three `TestPrefixCollision` pins that auto-approve synthetic
  executables (Plan A7, owner-confirmed strict deny-by-default).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- This document is executed FIRST (Plan Phase 1): the new tests and the migrated pins must
  all FAIL against the current code, and the recorded failures are the red baseline for
  seq 01/02. After seq 01 (code) and seq 02 (config) land, the whole file passes (AC-5).
- Reproduction commands and migrated pins are asserted `high` (not `medium`): the
  safe-shape path returns `RiskLevel.HIGH` on rule absence/violation, independent of the
  base risk rule (`_cfg`'s `approval_risk_rules={}`).
- Read-only `none` assertions are pinned with the working directory INSIDE `allowed_root`;
  outside the root, a bare subcommand token (e.g. `status`) already escalates through
  `_check_positional_args` (current behavior, unchanged by this Plan).

## Design decisions
- New tests go in one new class `TestShellSafeShape` (new) placed after `TestPrefixCollision`
  (L464-733), reusing the file's `_cfg(approval_shell_safe_prefixes=..., allowed_root=...,
  approval_protected_paths=...)` builder and `monkeypatch.chdir` for cwd control
  (relative-value resolution depends on the process cwd).
- Module constant `SHELL_PREFIXES_STRICT` (new): the post-change shipped list — `ls`, `cat`,
  `echo`, `git`, `pwd`, `find`, `grep` (mirrors seq 02); protected paths `("/etc/", "/opt/")`
  mirror the shipped `approval_protected_paths`.

## Alternatives considered
- N/A: test placement and assertion levels follow the Plan Tests section directly.

## Implementation
### Target file
- `tests/agent/test_tool_policy.py`

### Procedure
1. Add `SHELL_PREFIXES_STRICT` (new) and class `TestShellSafeShape` (new) with tests
   (all names (new)):
   - `test_python_interpreter_not_auto_approved` — `python -c print(1)` → `high`, cwd
     inside and outside `allowed_root`.
   - `test_pytest_not_auto_approved` — `pytest tests/` → `high`, both cwds.
   - `test_uv_run_not_auto_approved` — `uv run pytest` → `high`, both cwds.
   - `test_git_branch_delete_not_auto_approved` — `git branch -D feature` → `high`.
   - `test_git_diff_output_flag_not_auto_approved` — `git diff --output=/tmp/x` → `high`
     (cwd inside `allowed_root`; the escalation must come from the git rule, not the path
     check, so use an in-root tmp root).
   - `test_full_path_find_delete_escalates` — full-path `find` invocation with `-delete`
     → `high` (REQ-008: normalized name must hit the denylist).
   - `test_git_readonly_forms_remain_none` — `git status`, `git log --oneline`, `git diff`,
     `git show`, `git branch` → `none` (cwd inside `allowed_root`).
   - `test_full_path_git_log_remains_none` — full-path `git log --oneline` → `none` (AC-3).
2. Migrate the three A7 pins in `TestPrefixCollision` to expect `high`, keeping their
   names and updating their docstrings to state the strict deny-by-default reason:
   `test_single_letter_prefix_matches_exact_name`, `test_case_sensitive_prefix_accept`,
   `test_backslash_escape_in_prefix` (current expectations are `none` at HEAD, verified
   20261103 by reading the file).

### Method
- For cwd control: `allowed_root=str(tmp_path)`, `monkeypatch.chdir(tmp_path)` for the
  inside case; for the outside case `monkeypatch.chdir` a second tmp dir outside the root.
- For protected-path coverage use absolute /etc paths only in assertions against the
  escalation tests of the companion `shellrisk001` scope — not needed here beyond what is
  listed above.
- No test executes a command; all tests call `classify_risk(cfg, "shell_run", {"command": ...})`.

### Details
- Baseline recording: run `uv run pytest tests/agent/test_tool_policy.py -q` after step 1-2
  and record the failing test names in the Execution Status Notes (Plan Phase 1); do not
  fix the source in this document.
- Keep existing `TestPrefixCollision` cases other than the three pins byte-identical.

## Compatibility considerations
- The migrated pins are a recorded deviation from the Plan's earlier "every existing case
  keeps passing" wording, corrected in the Plan (A7) before this document was generated;
  precedent: healthcascade001 / toolarg001 pin migrations.

## Security considerations
- N/A: test-only change; coverage is the security value (red baseline pins the fail-open
  behavior before the fix).

## Rollback considerations
- N/A: revert the commit; the pins revert to `none` expectations together with seq 01/02.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py -q` — before seq 01/02: exactly the new
  tests and the three migrated pins fail (baseline); after seq 01/02: whole file green.
- `uv run ruff check tests/agent/test_tool_policy.py` — clean.

## Completion criteria
- Red baseline recorded; after seq 01 and seq 02: all eight new tests pass, the three
  migrated pins pass with `high` expectations, and every other pre-existing test is
  unchanged and passing (AC-5).

## Out of Scope
- `--flag=value` extraction tests — owned by `plans/20261101-142514_shellrisk001_...`,
  added by its procedure after this Plan is implemented.
- Source changes — seq 01; config changes — seq 02; docs — seq 04/05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestShellSafeShape` tests + migrate the three A7 pins; record red baseline | Pending | — | — | Plan Phase 1; execute before seq 01/02 |
| 2 | Re-run validation after seq 01/02 land (whole file green) | Pending | — | — | |

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
- **Requirement ID**: `REQ-011` (regression tests with shipped values; pin migration per
  Plan A7)
- **Source issue**: `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-072856
- **Related target files**: `tests/agent/test_tool_policy.py`
