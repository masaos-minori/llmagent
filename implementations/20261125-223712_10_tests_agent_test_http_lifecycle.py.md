## Goal

Replace the test that pins the removed `cfg.fields` override behavior, and make the validation-failure test exercise the real validator's `HttpStartupError` so the stderr leak is visible (REQ-002 no override, REQ-008 handle release, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `test_cfg_fields_reach_popen_kwargs` (`:295-299`) is the only test that passes `fields` to the config helper, and it asserts the behavior REQ-002 removes; it is replaced, not extended.
- `test_command_validation_failure_closes_stderr_and_raises` (`:190-208`) mocks `validate` with `side_effect=ValueError` (`:195`), which is why the current leak is invisible (Plan Issue Verification, "Contradicted").

## Design decisions

- The replacement test asserts impossibility at the spawn boundary: it captures the `Popen` call and asserts the keyword set contains no `cwd`, `shell`, `env` override, `stdout`, `stderr` override, `start_new_session=False`, or `preexec_fn`, and that `argv[0]` is the path the validator returned (AC-1, AC-2).
- The validation-failure test uses a real `CommandValidator` with a command that cannot pass validation, instead of a mocked exception type, so the exception the production code actually raises is what the cleanup path must handle.

## Alternatives considered

Keeping the `fields` test with a denylist assertion was rejected: REQ-002 removes the dictionary, so there is nothing left to filter.

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`
### Procedure
Replace the `fields` test with an override-impossible test and retarget the validation-failure test to `HttpStartupError`.

### Method
- Delete `test_cfg_fields_reach_popen_kwargs` (`:295-321`) and its `fields={"cwd": "/tmp/opencode"}` config (`:299`); add `test_popen_options_cannot_be_overridden` (new) that builds a config with a hostile `env` and `credential_env`, patches `subprocess.Popen`, and asserts the recorded kwargs and `argv[0]` against AC-1 and AC-2.
- Rewrite `test_command_validation_failure_closes_stderr_and_raises` (`:190-208`): inject a real `CommandValidator` and a `cmd` that fails validation, assert `HttpStartupError` propagates, the stderr handle is closed, and `_stderr_files` is empty (REQ-008).
- Add a case that a `ValueError` from the validator still releases the handle, so both raise shapes stay covered.
- Add a case that a changed file identity between validation and spawn aborts with a `StartupFailure` (AC-1).

### Details
- Keep the existing termination, budget, and shutdown cases (`:58-186`, `:229-345`) unchanged; only the two named cases and the config helper call change.
- Remove the `fields` keyword from the shared `_make_cfg` helper once no case passes it.

## Compatibility considerations

The file is the only test that constructs a config with `fields`, so its change is what makes row 4's deletion safe (Plan Assumptions).

## Security considerations

N/A: this row only asserts the guarantees rows 1-4 implement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle.py`
- Expected outcome before rows 1-4 land: the new and retargeted cases fail (Plan Phase 1)

## Completion criteria

- No test in the file passes `fields` or asserts that a config value reaches the `Popen` kwargs.
- A real-validator rejection leaves no open stderr handle and no `_stderr_files` entry.
- The spawn-side assertions prove `argv[0]` is the validated path.

## Out of Scope

- Implementing the launcher change (row 4).
- The spec-level contract cases (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1: expected to fail until rows 1-4 land |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (no `fields` override), REQ-008 (release stderr on `HttpStartupError`), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/agent/test_http_lifecycle.py`
