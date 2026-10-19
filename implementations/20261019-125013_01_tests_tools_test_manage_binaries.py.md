## Goal
Add a behavior test proving `deploy/build_binaries.sh` exports `UV_SYSTEM_CERTS` as `true` by default and keeps an explicit value, without Nuitka, network access, or `/opt/llm` (`REQ-003`).

## Scope
- One helper and two tests appended to the existing module; existing tests stay untouched.

## Assumptions
- With a stub `uv` first on `PATH` that fails every call, the script stops at its nuitka resolution before creating any build directory (verified on 2026-10-19 while writing the plan).
- The module already runs the script with `subprocess` and a restricted environment in `test_build_binaries_rollback_option`; this test follows that pattern.

## Design decisions
- Assert on the value the stub recorded, not on script text order: the script defines `uv run` command arrays before its export without executing them.
- Pass an explicit environment (not `env -i` of the whole process) containing only `PATH`, `BIN_DIR`, `OUTPUT_DIR`, and optionally `UV_SYSTEM_CERTS`.

## Alternatives considered
A static check that the export line precedes the first `uv` text was rejected: array definitions containing `uv run` precede the export without running.

## Implementation
### Target file
`tests/tools/test_manage_binaries.py`

### Procedure
1. Add the helper `_run_build_with_stub_uv` (new) that writes a stub `uv` shell script into `tmp_path`, runs `bash deploy/build_binaries.sh` with the stub directory first on `PATH`, and returns the return code, the set of values the stub recorded, and whether `OUTPUT_DIR` was created.
2. Add `test_build_binaries_exports_system_certs_by_default` (new): no `UV_SYSTEM_CERTS` in the environment; assert the recorded values are exactly `{"true"}`, the return code is non-zero, and `OUTPUT_DIR` does not exist.
3. Add `test_build_binaries_keeps_explicit_system_certs` (new): environment sets `UV_SYSTEM_CERTS=false`; assert the recorded values are exactly `{"false"}`.
4. Run the new tests before the script change and confirm the default test fails.

### Method
- The stub is `#!/bin/sh`, appends `$UV_SYSTEM_CERTS` to a file under `tmp_path`, and exits 1; set `chmod 0o755`.
- Use `REPO_ROOT / "deploy" / "build_binaries.sh"` as the script path and `PATH` of `<stub dir>:/usr/bin:/bin`.
- Read the recorded file with `splitlines()` into a set; an empty first line (variable unset) must make the default test fail before the change.

### Details
- Keep names, imports, and style of the neighboring tests; no new dependency.
- Expected before the script change: the default test fails (recorded value is empty) and the override test passes.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only; the stub runs only inside `tmp_path` and the script never reaches a real `uv`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_binaries.py -q`
- `uv run ruff format tests/tools/test_manage_binaries.py && uv run ruff check tests/tools/test_manage_binaries.py`
- `uv run python tools/check_mock_patch_targets.py` and `uv run python tools/check_suppression_justification.py`

## Completion criteria
- The default test fails against the unchanged script and passes after the script change; the override test passes in both states.

## Out of scope
- Changing the script (separate procedure)
- Tests for other scripts

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper and the two tests, and run them against the unchanged script | Pending | — | — | |
| 2 | Confirm they pass after the script change and run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (stub-uv test of the certificate variable)
- **Source issue**: issues/20261019-123439_deploybin002_build-script-needs-system-certificates.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-124601_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-125013
- **Related target files**: tests/tools/test_manage_binaries.py
