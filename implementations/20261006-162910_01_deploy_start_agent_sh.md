## Goal

Replace every `UV_NATIVE_TLS=true` with `UV_SYSTEM_CERTS=true` in `deploy/start_agent.sh` so `uv` stops emitting the `UV_NATIVE_TLS` deprecation warning during AgentREPL startup, while preserving the same TLS security posture.

## Scope

- **In scope**: the two `UV_NATIVE_TLS=true` occurrences at lines 65 and 76, each immediately preceded by `PYTHONPATH="${PYTHONPATH}"`.
- **Out of scope**: any other line, setting, or variable in the file.

## Assumptions

- `UV_SYSTEM_CERTS=true` provides equivalent system-certificate handling to `UV_NATIVE_TLS=true` for the HTTPS endpoints the agent contacts (uv's documented replacement).
- `uv` still requires one of these variables to enable TLS, so the variable is renamed, not removed.

## Design decisions

- N/A: this is a data-only, single-token substitution in a shell orchestration script. None of the Python import-layer architecture applies (no `import` boundaries, module cycles, or Python symbols involved).

## Alternatives considered

- Removing the variable entirely: rejected — `uv` needs a cert/TLS setting enabled for TLS connections.
- Adding `UV_SYSTEM_CERTS` alongside the old token: rejected — a uniform rename removes the deprecated token and avoids leaving dead configuration behind.

## Implementation

### Target file

`deploy/start_agent.sh`

### Procedure

Replace `UV_NATIVE_TLS=true` → `UV_SYSTEM_CERTS=true` at lines 65 and 76, preserving the `PYTHONPATH="${PYTHONPATH}"` prefix on each line.

### Method

- Locate both occurrences with `rg -n 'UV_NATIVE_TLS' deploy/start_agent.sh` (expected: lines 65 and 76).
- Confirm each sits on a `uv run` line prefixed by `PYTHONPATH="${PYTHONPATH}"`.
- Replace only the `UV_NATIVE_TLS=true` token on those two lines; leave the `PYTHONPATH` prefix and all surrounding text untouched.

### Details

- Line 65 (executable): `if ! PYTHONPATH="${PYTHONPATH}" UV_NATIVE_TLS=true uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then`
- Line 76 (executable): `PYTHONPATH="${PYTHONPATH}" UV_NATIVE_TLS=true uv run python -m agent.repl`
- Both occurrences are executable `uv run` invocations; there are no `echo` copies of this line in this file.

## Compatibility considerations

- N/A: no config keys, symbols, or public contracts change.

## Security considerations

- `UV_SYSTEM_CERTS=true` preserves the system-certificate TLS posture; do not weaken it. Confirm the endpoints the agent contacts use system CAs (see UNK-01); if a custom CA is required, add its path rather than reverting.

## Rollback considerations

- Fully reversible: restore `UV_NATIVE_TLS=true` on the two lines to undo. No state or schema is touched.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `deploy/start_agent.sh` | Static — all occurrences replaced | `rg 'UV_NATIVE_TLS' deploy/start_agent.sh` | Zero matches; `UV_SYSTEM_CERTS=true` present on lines 65 and 76 |
| `deploy/start_agent.sh` | Integration — clean startup | `bash /opt/llm/start_agent.sh` | No `UV_NATIVE_TLS` deprecation warning; TLS MCP connection works |

## Completion criteria

- Zero `UV_NATIVE_TLS` remain in `deploy/start_agent.sh`.
- `UV_SYSTEM_CERTS=true` present on both `uv run` lines with the `PYTHONPATH="${PYTHONPATH}"` prefix intact.

## Out of scope

- Any other file, any other variable, and any control-flow or logic change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `UV_NATIVE_TLS=true` → `UV_SYSTEM_CERTS=true` in `deploy/start_agent.sh` (lines 65, 76), preserving `PYTHONPATH="${PYTHONPATH}"` | Pending | — | — | REQ-001, REQ-005, REQ-006 |
| 2 | Static grep + runtime verification per Validation plan | Pending | — | — | REQ-001..REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | N/A: shell script, no Python lint/type/security gate | Pending | — | — |
| 4 | Update documentation, if in scope | N/A: no docs reference the variable | Pending | — | — |

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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261005-181700_replace_uv_native_tls.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-100352_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-162910
- **Related target files**: `deploy/start_agent.sh`
