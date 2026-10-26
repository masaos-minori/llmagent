## Goal

Enforce the production-path principal construction in `tests/eventbus/test_eventbus_crash_ack.py`
by removing the direct `_TOKEN_PRINCIPAL_MAP` mutations (lines 85-91, 102-109) and building
the per-consumer restriction via `_populate_token_maps()` with a config that carries it.

## Scope

- Modify only `tests/eventbus/test_eventbus_crash_ack.py` (direct-map assignments at
  lines 85-91 and 102-109).

## Assumptions

- `_populate_token_maps(config)` (auth.py, seq 02) is the single population entry point and
  accepts a config carrying the per-consumer restriction.
- `_TOKEN_PRINCIPAL_MAP` is referenced 82 times across `tests/`; this row changes only the
  two direct-mutation sites in this file (REQ-006; Acceptance 4).

## Design decisions

- Replace direct global assignment with a config-driven `_populate_token_maps()` call so the
  test exercises the production path.

## Alternatives considered

- Keeping direct mutation but adding a noqa: rejected — REQ-006 requires production-path
  construction.

## Implementation

### Target file

`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure

1. Remove the direct assignment `_TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(...)`
   at lines 85-91 and 102-109.
2. Build the per-consumer restriction via `_populate_token_maps(config)` using a config that
   carries the restriction (the same path the app lifecycle uses).
3. Keep `_populate_token_maps()` as the sole population entry point; do not re-introduce
   direct map mutation elsewhere in this file.

### Method

Refactor the two setup sites to the production path.

### Details

- If the injected `Principal` in the crash-ack test carries state that `_populate_token_maps()`
  cannot express from a config, record this as `Needs confirmation` rather than bypassing
  REQ-006.

## Compatibility considerations

- Preserves the crash-ack behavior under test; only the principal-construction mechanism
  changes.

## Security considerations

- Confirms principals are built through the validated population path (supports REQ-006).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py` — passes with production-path
  principals; no direct `_TOKEN_PRINCIPAL_MAP` mutation remains.
- `uv run pytest tests/eventbus/` — full suite passes.

## Completion criteria

- No direct `_TOKEN_PRINCIPAL_MAP` mutation remains in this file; principals are built via
  `_populate_token_maps()`.

## Out of Scope

- Other test files (seq 06-09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row IS the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `tests/eventbus/test_eventbus_crash_ack.py`
