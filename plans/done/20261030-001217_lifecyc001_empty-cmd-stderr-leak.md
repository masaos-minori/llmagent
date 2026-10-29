## Goal
Fix the resource leak on the empty-command startup-failure path in `SubprocessLauncher.create_and_validate_proc`: before raising `HttpStartupError` for an empty command, release the inherited stderr handle and drop its tracking entry so the path is consistent with every other branch in the method.

## Priority
Low

## Scope
- **In-Scope**:
  - Add the same stderr cleanup the other failure paths perform, immediately before the empty-command `raise HttpStartupError(...)` in `scripts/agent/http_lifecycle_subprocess_launcher.py`.
  - Update the characterization test `tests/agent/test_http_lifecycle.py` so it asserts the fixed behavior (handle closed, registry cleared) instead of asserting the leak is preserved.
- **Out-of-Scope**:
  - Any change to the success path (the handle stays open for the process lifetime and is closed later by the terminator).
  - Any change to the non-empty-value-error path or the `Popen`-failure path cleanup.
  - Any change to `Popen` construction, pipe setup, or `getpgid` handling.
  - Changing the message carried by `HttpStartupError` on this path (`"Empty command configuration"`).
- **Dependencies**: N/A: none.

## Background
`scripts/agent/http_lifecycle_subprocess_launcher.py` extracts the spawn cluster from `HttpServerLifecycleManager`. In `create_and_validate_proc`, `self._stderr_log_manager.open_log(server_key, cfg)` opens the inherited stderr handle and the caller records it in `self._stderr_files[server_key]` right after. Every failure branch then releases both before raising `HttpStartupError`:
- The value-error branch (command-validation failure) calls `self.close_stderr_log(server_key, stderr_fh)` then raises.
- The `Popen`-exception branch calls `self.close_stderr_log(server_key, stderr_fh)` then re-raises.
- The `getpgid`-failure branch releases in a `finally` via `close_stderr_log`.

`close_stderr_log` closes the handle, pops `self._stderr_files[server_key]`, and calls `self._stderr_log_manager.forget(server_key)`.

The empty-command guard is the only branch that does not call `close_stderr_log`.

## Problem
When `cfg.cmd` is empty or `cfg.cmd[0]` is falsy, `create_and_validate_proc` raises `HttpStartupError` at the empty-command guard without closing the inherited `stderr_fh` or dropping `self._stderr_files[server_key]`. This leaves:
- an open file handle for the lifetime of the launcher (resource leak), and
- a dangling reference to a soon-to-be-closed pipe in `self._stderr_files`.

It is a minor resource/state-consistency defect on a rare error path; the happy path and the normal error path are unaffected.

## Reason for Change
Consistency: every other branch in `create_and_validate_proc` releases both the handle and the registry entry before raising. The empty-command path is the sole exception. Fixing it removes the leak and keeps `self._stderr_files` consistent.

## Implementation Intent
Call the existing `self.close_stderr_log(server_key, stderr_fh)` helper immediately before the empty-command `raise HttpStartupError(...)`, mirroring the value-error and `Popen`-exception branches exactly. Then update the characterization test to assert the handle is closed and the registry entry is gone.

## Requirements
- `REQ-001`: On the empty-command failure path, `create_and_validate_proc` releases the inherited stderr handle and drops `self._stderr_files[server_key]` before raising `HttpStartupError`, via the same `close_stderr_log` helper the other branches use.
- `REQ-002`: The characterization test `test_empty_command_raises_before_spawn` in `tests/agent/test_http_lifecycle.py` asserts the fixed behavior (handle closed, registry cleared) and the suite passes.

## Implementation Target Files
**Freeze status**: Frozen (was `Draft`; set to `Frozen` only once `issue-to-plan` Step 8's Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_subprocess_launcher.py` | Modify | Add `self.close_stderr_log(server_key, stderr_fh)` before the empty-command `raise HttpStartupError(...)` so the handle and registry entry are released, matching the value-error and `Popen`-exception branches | REQ-001; AC1, AC2 | Empty-command guard at lines 72-79 raises `HttpStartupError` with no preceding cleanup; the value-error branch (lines 84-92) and `Popen`-exception branch (lines 109-111) both call `close_stderr_log` first; `close_stderr_log` defined at lines 119-123 (checked in Step 2) | `test_command_validation_failure_closes_stderr_and_raises`, `test_popen_failure_closes_stderr_and_reraises` | Verified |
| `tests/agent/test_http_lifecycle.py` | Modify | Convert the characterization lock in `test_empty_command_raises_before_spawn` from asserting the leak to asserting the fixed behavior | REQ-002; AC3 | `test_empty_command_raises_before_spawn` (lines 222-249) asserts `stderr_fh.close.assert_not_called()` and `mgr._stderr_files.get("test") is stderr_fh` (the leak); sibling tests already assert `close.assert_called_once()` + `"test" not in mgr._stderr_files` (checked in Step 2) | `test_empty_command_raises_before_spawn` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Confirm `StderrLogManager.forget` is a safe no-op (`self._log_paths.pop(server_key, None)`) so calling `close_stderr_log` on the empty-command path does not raise when the log path was never registered | `scripts/agent/http_lifecycle_subprocess_launcher.py`; REQ-001 |

## Acceptance Criteria
- Raising `HttpStartupError` on an empty command closes the inherited stderr handle (REQ-001, AC1).
- Raising `HttpStartupError` on an empty command drops `self._stderr_files[server_key]` for that server (REQ-001, AC2).
- `tests/agent/test_http_lifecycle.py` updated to assert the fixed behavior and the full suite passes (REQ-002, AC3).

## Tests
- Update `test_empty_command_raises_before_spawn` in `tests/agent/test_http_lifecycle.py` to assert `stderr_fh.close.assert_called_once()` and `assert "test" not in mgr._stderr_files`, mirroring the sibling cleanup tests (`test_command_validation_failure_closes_stderr_and_raises`, `test_popen_failure_closes_stderr_and_reraises`) (REQ-002). Keep the assertions that validate the empty-command path still short-circuits before validation/Popen (`mock_validate.assert_not_called()`, `mock_popen.assert_not_called()`, correct `reason`/`server_key`).

## Documentation Impact
None beyond the test. No external `docs/*.md` update required (REQ-001).

## Assumptions
- The fix uses `self.close_stderr_log(server_key, stderr_fh)` (which pops `self._stderr_files[server_key]`) rather than `self._stderr_files.clear()`, because `_stderr_files` is a shared tracking dict across servers; `.clear()` would wipe every server's entries. Only this server's entry must be dropped.
- Calling the real `StderrLogManager.forget` inside `close_stderr_log` during the test is safe: `forget` performs `self._log_paths.pop(server_key, None)`, a no-op when the key is absent, so the test's partial mocking of `open_log` does not need to also mock `forget`.
- The empty-command guard remains a pre-validation check; the fix adds cleanup but does not reorder or alter the guard condition.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is the empty-command failure reachable in practice, or only via a malformed config? If unreachable, the leak is effectively dead code and the fix may be lower value. | None — resolved by evidence. | Reachable: the guard fires whenever `cfg.cmd` is empty (`[]`) or `cfg.cmd[0]` is falsy (e.g. `[""]`), i.e. a malformed subprocess config. It is a rare error path, not dead code. | False |
| UNK-02 | Should the characterization test be replaced with a regression test pinning the fixed behavior, or removed entirely? | None — resolved by design. | Replace the leak-locking assertions with assertions of the fixed behavior (closed handle + cleared registry), matching the sibling cleanup tests. This converts the lock into a regression test that pins the corrected behavior. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/http_lifecycle_subprocess_launcher.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_http_lifecycle.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (≤3 files, no public/runtime interface change, no schema change). Analysis limited to direct verification of the two target files and the `forget` contract they depend on.

Fix location: the empty-command guard (lines 72-79) is the sole branch that omits cleanup. The fix adds a single `self.close_stderr_log(server_key, stderr_fh)` call before the `raise HttpStartupError(...)`, reusing the existing helper rather than inlining `stderr_fh.close()` plus a registry mutation.

Correct cleanup primitive (correction to the issue text): the issue's Required Changes suggest `stderr_fh.close()` plus `self._stderr_files.clear()`. The plan deliberately uses `close_stderr_log` instead, for two reasons verified against the current source:
- `close_stderr_log` also calls `self._stderr_log_manager.forget(server_key)`, keeping the log-path registry consistent; the raw `.close()` + `.clear()` suggestion skips this and would leave a stale log-path entry.
- `close_stderr_log` pops only `self._stderr_files[server_key]`, whereas `.clear()` wipes every server's tracking entries from the shared dict. Using `.pop(server_key)` (via the helper) matches the value-error and `Popen`-exception branches exactly.

Test approach: convert `test_empty_command_raises_before_spawn` from a characterization lock into a regression test. Assert `stderr_fh.close.assert_called_once()` and `assert "test" not in mgr._stderr_files`, matching the sibling cleanup tests. Keep the short-circuit assertions (`mock_validate.assert_not_called()`, `mock_popen.assert_not_called()`, correct `reason`/`server_key`). The real `forget` runs unmocked in the test but is a safe no-op pop (see Assumptions).

radon baseline: `create_and_validate_proc` is complexity B(7); adding one statement before the raise adds no branch, so complexity stays B. vulture and bandit report no findings on this file.

## Implementation steps
1. **Phase 1: Release resources on the empty-command path**
   - [ ] In `create_and_validate_proc` (`scripts/agent/http_lifecycle_subprocess_launcher.py`), add `self.close_stderr_log(server_key, stderr_fh)` immediately before the empty-command `raise HttpStartupError(...)` at the guard (lines 72-79), mirroring the value-error and `Popen`-exception branches (REQ-001; AC1, AC2).
2. **Phase 2: Update the characterization test to pin the fixed behavior**
   - [ ] In `test_empty_command_raises_before_spawn` (`tests/agent/test_http_lifecycle.py`), replace `stderr_fh.close.assert_not_called()` with `stderr_fh.close.assert_called_once()` and `assert mgr._stderr_files.get("test") is stderr_fh` with `assert "test" not in mgr._stderr_files`, keeping the short-circuit assertions intact (REQ-002; AC3).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/agent/test_http_lifecycle.py` and confirm all tests pass, including the updated `test_empty_command_raises_before_spawn` and the sibling cleanup tests (REQ-002, REQ-001).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_subprocess_launcher.py::create_and_validate_proc` (empty-command path) | Regression: the empty-command failure now closes the handle and clears the registry | `uv run pytest tests/agent/test_http_lifecycle.py::TestSubprocessSpawnCharacterization::test_empty_command_raises_before_spawn` | `stderr_fh.close` called once; `"test" not in mgr._stderr_files`; short-circuit assertions still hold |
| `tests/agent/test_http_lifecycle.py` | Full-suite regression | `uv run pytest tests/agent/test_http_lifecycle.py` | All tests pass |

## Risks
- **Risk**: Calling `close_stderr_log` on the empty-command path invokes `StderrLogManager.forget`, which the existing test does not mock (only `open_log` is patched). → **Mitigation**: `forget` performs `self._log_paths.pop(server_key, None)`, a no-op when the key is absent; verified by reading `http_lifecycle_stderr_log_manager.py`. The test runs the real `forget` safely.
- **Risk**: Converting the characterization test could mask a genuine behavior contract if the new assertions are too weak. → **Mitigation**: The new assertions pin the exact fixed behavior (handle closed once, registry entry removed), matching the sibling cleanup tests, so they detect a regression to the leak.
- **Risk**: Using `self._stderr_files.clear()` instead of `close_stderr_log` would wipe other servers' tracking entries from the shared dict. → **Mitigation**: The plan mandates `close_stderr_log`, which pops only this server's key; documented as a design decision and an implementation-step constraint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Release resources on the empty-command path | In Progress | — | — | Touches `scripts/agent/http_lifecycle_subprocess_launcher.py` |
| 2 | Update the characterization test to pin the fixed behavior | In Progress | — | — | Touches `tests/agent/test_http_lifecycle.py` |
| 3 | Deployment & Verification | Pending | — | — | Runs `pytest tests/agent/test_http_lifecycle.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261030-072145_01_scripts_agent_http_lifecycle_subprocess_launcher.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-072145_02_tests_agent_test_http_lifecycle.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-220634_lifecyc001_empty-cmd-stderr-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-001217
- **Related target files**: scripts/agent/http_lifecycle_subprocess_launcher.py, tests/agent/test_http_lifecycle.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / AI Implementation Instruction; empty-command guard raises without cleanup (Step 2) | `scripts/agent/http_lifecycle_subprocess_launcher.py` | Step 1 | AC1, AC2 | Empty-command path closes handle + clears registry (Step 2) | Confirmed by repository evidence |
| REQ-002 | Testing Expectations / Constraints; characterization test locks the leak (Step 2) | `tests/agent/test_http_lifecycle.py` | Step 2 | AC3 | Updated `test_empty_command_raises_before_spawn` (Step 2) | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-072145 -->