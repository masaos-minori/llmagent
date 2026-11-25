## Goal

Make the launcher execute exactly what the validator validated, remove the `cfg.fields` override channel, and release the stderr handle when the real validator rejects a command (REQ-001 spec-only Popen, REQ-002 no override, REQ-003 validated path, REQ-008 handle release).

## Scope
**Release unit**: R1-launch-spec

## Assumptions

- `CommandValidator.validate` raises `HttpStartupError`, which is a `RuntimeError` (`scripts/agent/http_lifecycle_errors.py:28`), so the existing `except ValueError` at `:85` never catches a real validation failure (Plan Issue Verification, "Contradicted").
- `scripts/agent/http_lifecycle.py:346-348` keeps calling `create_and_validate_proc` unchanged; only the body of that method changes here.
- The identity re-check is performed by `LaunchSpec.verify_identity` (row 2); this row only calls it at the right moment.

## Design decisions

- The launcher's only `Popen` input is the spec: `Popen(spec.argv, **spec.popen_kwargs())`. No keyword is constructed here, which is what makes REQ-002 checkable at the call site.
- Validation failure handling is widened to `except (ValueError, HttpStartupError)` rather than catching `Exception`: the two shapes the validator can raise are named, and the release path stays identical to the existing `ValueError` path (`:85-95`).
- The stderr handle and its `_stderr_files` entry are released by the same helper the other failure paths already use (`self._stderr_files.pop(server_key, None)` at `:123`), so one cleanup route covers all startup failures.

## Alternatives considered

Catching `Exception` around `validate` was rejected: it would swallow programming errors that the existing `except Exception` at `:110` already covers for the spawn itself. Keeping `popen_kwargs` as a local dict with a denylist was rejected: REQ-002 removes the dictionary entirely.

## Implementation
### Target file
`scripts/agent/http_lifecycle_subprocess_launcher.py`
### Procedure
Build a `LaunchSpec` from the validated path and identity, spawn from it, and release the stderr handle on `HttpStartupError`.

### Method
- Keep the validator call at `:84` but bind its result: the resolved path and the identity pair returned by row 3.
- Widen the handler at `:85` to `except (ValueError, HttpStartupError) as e:` and keep the existing cleanup and `StartupFailure`-shaped raise.
- Delete `env = self._command_validator.filter_env(cfg.env)` at `:69`; the environment is built inside `build_launch_spec` (row 2).
- Delete the `popen_kwargs` literal at `:96-101` and the `if cfg.fields: popen_kwargs.update(cfg.fields)` merge at `:102-103`.
- Call `build_launch_spec(server_key, cfg, resolved_path, identity, stderr_fh)` (row 2), then `spec.verify_identity()` immediately before the spawn, and raise `HttpStartupError(StartupFailure(...))` when the identity no longer matches (AC-1).
- Replace `subprocess.Popen(cfg.cmd, **popen_kwargs)` at `:106-107` with `subprocess.Popen(spec.argv, **spec.popen_kwargs())`.

### Details
- Keep the `# nosec B603` justification comment updated: `argv[0]` is now the validator-resolved absolute path, not a config string.
- Keep the process-group capture (`os.getpgid`) and the post-spawn validation paths (`:110-127`) unchanged.
- The identity-mismatch reason text names the server key and the resolved path, and never an environment value.

## Compatibility considerations

`create_and_validate_proc` keeps its signature and its `(Popen, IO[bytes])` return, so `scripts/agent/http_lifecycle.py` and the manager's tracking dicts are unaffected. The `cfg.fields` removal breaks `tests/agent/test_http_lifecycle.py:295-299`, which row 10 replaces in the same unit.

## Security considerations

Executing the validated path closes the validate-then-run-different-binary gap (REQ-003, AC-1). Removing the `fields` merge closes the `shell`/`env`/`start_new_session`/`preexec_fn` override channel (REQ-002, AC-2). Releasing the handle on `HttpStartupError` closes the leaked file descriptor and stale `_stderr_files` entry (REQ-008).

## Rollback considerations

Revert the commit. This row is the consumer of rows 2 and 3; reverting it alone leaves the launcher calling a removed `filter_env`.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle.py`
- `uv run mypy scripts/agent/http_lifecycle_subprocess_launcher.py`
- `uv run ruff format` and `uv run ruff check`
- `uv run bandit -r scripts/agent/http_lifecycle_subprocess_launcher.py -c pyproject.toml`

## Completion criteria

- The executable passed to `Popen` is the path `validate` returned, and no keyword other than those `popen_kwargs()` produces reaches `Popen`.
- No reference to `cfg.fields`, `popen_kwargs`, or `filter_env` remains in the module.
- A command rejected by the real `CommandValidator` leaves no open stderr handle and no `_stderr_files` entry, and the error still propagates.
- A changed file identity between validation and spawn aborts the start with a `StartupFailure`.

## Out of Scope

- Defining `LaunchSpec` and `build_launch_spec` (row 2).
- The confinement and identity-capture rules themselves (row 3).
- The test that pins the removed override behavior (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after the row 10 Phase 1 tests are in place (REQ-009) |
| 2 | Confirm the Phase 1 test additions from row 10 fail before this change and pass after it | Pending | — | — | Tests-first order per Plan Phase 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (spec is the only Popen input), REQ-002 (no option override), REQ-003 (execute the validated path), REQ-008 (release stderr on `HttpStartupError`)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `scripts/agent/http_lifecycle_subprocess_launcher.py`
