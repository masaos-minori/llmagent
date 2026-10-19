## Goal
Export `UV_SYSTEM_CERTS` with an operator-overridable default of `true` before the script's first `uv` execution, so `uv` can fetch nuitka on hosts whose certificates are only in the system store (`REQ-001`).

## Scope
- One comment block and one `export` line beside the existing `UV_NO_DEV` export; nothing else in the script changes.

## Assumptions
- The installed `uv` honors `UV_SYSTEM_CERTS`; the other deploy scripts and `AGENTS.md` already rely on it.
- The `UV_NO_DEV` export precedes every `uv` execution (`command -v uv`, `uv python find`, `uv python dir`, and the nuitka resolution), so the new export placed after it is early enough.

## Design decisions
- Use the script's existing `"${VAR:-default}"` convention so an operator-set value, including `false`, is never overwritten.
- Write the comment in Japanese like the neighboring comments, stating why the variable is set and how to override it.

## Alternatives considered
Prefixing each `uv` call with `UV_SYSTEM_CERTS=true` was rejected: the nuitka commands are built as arrays and run in several places, so one export is simpler and covers them all.

## Implementation
### Target file
`deploy/build_binaries.sh`

### Procedure
1. Insert, directly after `export UV_NO_DEV="${UV_NO_DEV:-1}"`, a short comment and `export UV_SYSTEM_CERTS="${UV_SYSTEM_CERTS:-true}"`.
2. Run the stub test, `bash -n`, and the existing script tests.

### Method
- Comment text: uv は既定で内蔵の証明書バンドルを使うため、システムの証明書ストアにしか証明書がない環境では PyPI から nuitka を取得できず UnknownIssuer で失敗する。他の deploy スクリプトと同様に既定でシステムの証明書ストアを使い、UV_SYSTEM_CERTS=false で無効化できる。
- Do not change `UV_NO_DEV`, `UV_PYTHON`, the nuitka command arrays, or any other line.

### Details
- No other file in the repository sets this variable for the build; the deploy skill sentence is a separate procedure.

## Compatibility considerations
Behavior change only for a host where the system store matters: `uv` now uses it by default during the build. An operator-set `UV_SYSTEM_CERTS` (for example `false`) keeps the previous behavior.

## Security considerations
Using the system certificate store is the project's existing convention for `uv`; certificate verification stays enabled.

## Rollback considerations
N/A: revert the commit; operators can also set `UV_SYSTEM_CERTS=false` without reverting.

## Validation plan
- `bash -n deploy/build_binaries.sh`
- `uv run pytest tests/tools/test_manage_binaries.py -q`
- No real build is run as part of this procedure (separate approved action)

## Completion criteria
- The script exports `UV_SYSTEM_CERTS` with a `true` default before its first `uv` execution and preserves an explicit value; `bash -n` and the tests pass.

## Out of scope
- Nuitka flags, the entry table, and other scripts
- Running a real build or touching `/opt/llm`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the comment and the overridable export | Pending | — | — | |
| 2 | Run `bash -n` and the stub test, then the validation sequence (`rules/toolchain.md`) for the changed script and test | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (overridable certificate export)
- **Source issue**: issues/20261019-123439_deploybin002_build-script-needs-system-certificates.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-124601_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-125013
- **Related target files**: deploy/build_binaries.sh
