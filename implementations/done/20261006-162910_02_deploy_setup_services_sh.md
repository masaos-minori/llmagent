## Goal

Replace every `UV_NATIVE_TLS=true` with `UV_SYSTEM_CERTS=true` in `deploy/setup_services.sh` so `uv` stops emitting the `UV_NATIVE_TLS` deprecation warning, while preserving the same TLS security posture.

## Scope

- **In scope**: the two executable `UV_NATIVE_TLS=true` occurrences at lines 28 and 56, plus the three `echo` example lines at 112–114. Each executable occurrence is immediately preceded by `PYTHONPATH=/opt/llm/scripts`.
- **Out of scope**: any other line, setting, or variable in the file.

## Assumptions

- `UV_SYSTEM_CERTS=true` provides equivalent system-certificate handling to `UV_NATIVE_TLS=true` for the HTTPS endpoints the agent contacts (uv's documented replacement).
- `uv` still requires one of these variables to enable TLS, so the variable is renamed, not removed.

## Design decisions

- N/A: this is a data-only, single-token substitution in a shell orchestration script. None of the Python import-layer architecture applies.

## Alternatives considered

- Removing the variable entirely: rejected — `uv` needs a cert/TLS setting enabled for TLS connections.
- Updating only the executable lines and leaving the `echo` examples: rejected — user-facing copy-paste guidance must not retain the deprecated variable (Plan Background).

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

Replace `UV_NATIVE_TLS=true` → `UV_SYSTEM_CERTS=true` on lines 28, 56, and 112–114, preserving each `PYTHONPATH=/opt/llm/scripts` prefix.

### Method

- Locate all occurrences with `rg -n 'UV_NATIVE_TLS' deploy/setup_services.sh` (expected: lines 28, 56, 112, 113, 114).
- Confirm lines 28 and 56 are executable `uv run` lines prefixed by `PYTHONPATH=/opt/llm/scripts`, and lines 112–114 are `echo` example lines.
- Replace only the `UV_NATIVE_TLS=true` token on all five lines; leave the `PYTHONPATH` prefixes and all surrounding text untouched. Apply the same replacement to the `echo` examples so user-facing guidance stays consistent.

### Details

- Line 28 (executable): `if ! PYTHONPATH=/opt/llm/scripts UV_NATIVE_TLS=true uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then`
- Line 56 (executable): `EXPECTED_SCHEMA_VERSION=$(PYTHONPATH=/opt/llm/scripts UV_NATIVE_TLS=true uv run python -c \`
- Line 112 (echo example): `echo "  cd /opt/llm && UV_NATIVE_TLS=true uv run python -m rag.ingestion.crawler"`
- Line 113 (echo example): `echo "  cd /opt/llm && UV_NATIVE_TLS=true uv run python -m rag.ingestion.chunk_splitter"`
- Line 114 (echo example): `echo "  cd /opt/llm && UV_NATIVE_TLS=true uv run python -m rag.ingestion.ingester"`

## Compatibility considerations

- N/A: no config keys, symbols, or public contracts change.

## Security considerations

- `UV_SYSTEM_CERTS=true` preserves the system-certificate TLS posture; do not weaken it. Confirm the endpoints the agent contacts use system CAs (see UNK-01); if a custom CA is required, add its path rather than reverting.

## Rollback considerations

- Fully reversible: restore `UV_NATIVE_TLS=true` on the five lines to undo. No state or schema is touched.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `deploy/setup_services.sh` | Static — all occurrences replaced | `rg 'UV_NATIVE_TLS' deploy/setup_services.sh` | Zero matches; `UV_SYSTEM_CERTS=true` present on lines 28, 56, 112, 113, 114 |
| `deploy/setup_services.sh` | Integration — service setup runs | run after `deploy/init_db.sh` in a safe target | Completes without error; no deprecation warning |

## Completion criteria

- Zero `UV_NATIVE_TLS` remain in `deploy/setup_services.sh`.
- `UV_SYSTEM_CERTS=true` present on all five lines (2 executable + 3 `echo` examples) with the `PYTHONPATH=/opt/llm/scripts` prefix intact.

## Out of scope

- Any other file, any other variable, and any control-flow or logic change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `UV_NATIVE_TLS=true` → `UV_SYSTEM_CERTS=true` in `deploy/setup_services.sh` (lines 28, 56, 112–114), preserving `PYTHONPATH=/opt/llm/scripts` | Completed | — | 20261007-123128 | REQ-002, REQ-005, REQ-006 |
| 2 | Static grep + runtime verification per Validation plan | Completed | — | 20261007-123128 | REQ-001..REQ-006 static validation passed (bash -n OK; rg confirms all UV_NATIVE_TLS replaced with UV_SYSTEM_CERTS=true incl. echo examples 112-114); runtime verification requires /opt/llm prod env (unavailable in dev) |
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
- **Requirement ID**: `REQ-002`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261005-181700_replace_uv_native_tls.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-100352_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-162910
- **Related target files**: `deploy/setup_services.sh`