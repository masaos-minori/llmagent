## Goal

- Convert `tests/eventbus/test_eventbus_config.py` to the renamed publication function and the generation-reading helper (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; only import/call/docstring-level changes.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: `principal_map` import line 12; calls at 523 and 524 (`assert "admin-token" in principal_map()` / `principal = principal_map()["admin-token"]`); `_populate_token_maps` import at 508 and call at 521, import at 739 and call at 742 — 4 references total (grep-verified), matching the Plan row "4 calls" plus the `principal_map()` import/calls at 12, 523-524.

## Design decisions

- `principal_map()` calls become `current_principals()` (sibling document 04): identical read semantics (principals of the generation in force, `{}` before publication).
- `_populate_token_maps` imports/calls become `build_and_publish_generation` (new) — behavior unchanged (build-then-publish, fail leaves previous generation).

## Alternatives considered

- Reading `eb_auth.current_generation().principals` inline instead of the helper: rejected — the helpers module is the single shared read point the Plan Design defines (sibling document 04).

## Implementation
### Target file
`tests/eventbus/test_eventbus_config.py`

### Procedure
1. Line 12: change `from tests.eventbus.eventbus_helpers import principal_map` to import `current_principals` (new); update calls at 523 and 524.
2. Rename the `_populate_token_maps` import at 508 and call at 521, and the import at 739 and call at 742, to `build_and_publish_generation` (new) (keep the surrounding config-reload assertions unchanged).

### Method
- The config-reload tests compare `load_config` outputs and principal reachability; only names change (behavior locking).

### Details
- If other helpers from `eventbus_helpers` are imported on line 12 (client factories), they stay untouched.

## Compatibility considerations

- Overlap with plan003 on this file: plan003 does not list `test_eventbus_config.py` (Plan Assumptions overlap list covers subscribe/ack_nack/ack_endpoint/crash_ack only) — no shared region.

## Security considerations

- No token echo added: the admin-token key is an existing test constant used only as a dict key in assertions (AC-006 unchanged).

## Rollback considerations

- Revert of the single atomic commit restores the old imports/calls (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_config.py` green after Method (config reload cases, Plan Validation row 1 scope).
- `grep -n "principal_map\|_populate_token_maps" tests/eventbus/test_eventbus_config.py` -> no matches (AC-001; `\bprincipal_map\b` word-boundary check clean).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- File references neither removed name (AC-001, AC-003).
- Config reload -> principal reachability assertions pass unchanged (AC-002).

## Out of Scope

- Helper implementations and the conftest fixture — sibling documents 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename imports/calls at 12, 508/521, 523-524, 739/742 — Plan Phase 1 | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tests/eventbus/test_eventbus_config.py`
