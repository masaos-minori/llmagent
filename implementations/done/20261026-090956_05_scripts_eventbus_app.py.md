## Goal

Confirm the app startup lifecycle (`scripts/eventbus/app.py` lifespan) reuses the single
principal-publish entry point so no empty-map window exists at startup, and make no change
unless the lifecycle must call a new publish helper directly.

## Scope

- Read/verify `scripts/eventbus/app.py` lifespan (lines 69-83); no change expected.

## Assumptions

- `_populate_token_maps()` (auth.py, seq 02) remains the single population entry point, so
  the lifespan call at app.py:74 inherits the atomic publish.
- The import at app.py:25 (`_populate_token_maps`, `# noqa: PLC0415`) stays valid.

## Design decisions

- Treat this as a verification row: the lifespan already calls `_populate_token_maps()`,
  which now publishes atomically via seq 02. No change unless seq 02 introduces a separate
  `publish_principals()` that the lifecycle must call directly.

## Alternatives considered

- Calling a new `publish_principals()` directly from the lifespan: only if seq 02 makes
  `_populate_token_maps()` no longer the publish entry point.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Read the lifespan (app.py:69-83); confirm `_populate_token_maps(app.state.config)` is
   called after `app.state.config = load_config(...)` (app.py:71-74).
2. Confirm the publish happens-before any broker/subscriber startup (app.py:77+) so no
   concurrent request can observe an empty map at startup.
3. If seq 02 keeps `_populate_token_maps()` as the entry point, make no change. If it
   requires a direct `publish_principals()` call, amend this row's procedure after seq 02.

### Method

Read-only confirmation; no edits expected.

### Details

- Reference row: the atomic publish is implemented in seq 02.

## Compatibility considerations

- N/A: no change expected.

## Security considerations

- Confirms no empty-map window at startup (supports REQ-001).

## Rollback considerations

- N/A: revert the commit (no change expected).

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_app_isolation.py` and `uv run pytest
  tests/eventbus/` — startup population intact.

## Completion criteria

- The lifespan publishes principals through the single entry point before any subscriber
  starts.

## Out of Scope

- Any code change unless seq 02 requires a direct publish-helper call.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm lifespan reuses the single publish entry point | Pending | — | — | Read-only; edit only if seq 02 changes the entry point |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: reference row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Covered by seq 02 |
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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `scripts/eventbus/app.py`
