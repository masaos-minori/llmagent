## Goal

- Point `scripts/eventbus/app.py` at the renamed `build_and_publish_generation()` so the lifespan baseline publication uses the new public name (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- Import/call rename only; behavior of the lifespan baseline publication is unchanged. Part of the Plan's single atomic Phase 1 cutover.

## Assumptions

- The rename lands in the same commit as `scripts/eventbus/auth.py` (sibling document 01); an intermediate state where `app.py` imports the old name would break the service, which the atomic-phase rule prevents (Plan Design "Atomicity").

## Design decisions

- Keep the existing `# noqa: PLC0415 — new module, REQ-004` comment on the import line (the noqa reason is about import placement, not the function name).

## Alternatives considered

- Importing `auth` and calling `auth.build_and_publish_generation(...)`: rejected — no need to change the import shape; minimal diff (Plan Scope).

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Change the import line 26 from `_populate_token_maps,` to `build_and_publish_generation,` (keep the noqa comment).
2. Change the lifespan call at line 84 from `_populate_token_maps(app.state.config)` to `build_and_publish_generation(app.state.config)`.
3. Keep the surrounding lifespan comments ("Populate token maps from config for authorization" may be reworded to "Build and publish the baseline authorization generation from config") and the restart-baseline audit block at lines 86-90 unchanged — it reads `current_generation()` and is unaffected (Plan Background: reference-only).

### Method
- Verified anchors at HEAD `1a13653e8`: import `app.py:26`, call `app.py:84`. `app.py` is the only production importer of the renamed function (Plan Background).

### Details
- No change to middleware attachment, audit record fields, or DB open order.

## Compatibility considerations

- Test lifespan usage via `make_eventbus_client` continues to work: the lifespan calls the renamed function after sibling document 01 lands (UNK-01 resolution path, Plan Unknowns).

## Security considerations

- N/A: name change only; the baseline audit record format (no raw tokens, hash-only detail) is untouched (REQ-004 / AC-006).

## Rollback considerations

- Revert of the single atomic commit restores the old import/call together with auth.py (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/deploy/test_setup_services_eventbus.py` (Plan Validation row 4).
- `grep -n "_populate_token_maps" scripts/eventbus/app.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- `app.py` imports and calls `build_and_publish_generation()` and references neither removed name (AC-001, AC-002).
- Lifespan publishes the baseline generation and the restart-baseline audit record as before (AC-002).

## Out of Scope

- Renaming the function itself — sibling document 01.
- The auth-restore monkeypatch in the companion deploy test — companion section below.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename import (line 26) and lifespan call (line 84) in `scripts/eventbus/app.py` — Plan Phase 1 | Pending | — | — | |
| 2 | Convert companion `tests/deploy/test_setup_services_eventbus.py` line 339 to generation restore — Plan Phase 1 | Pending | — | — | plan001 document 23 (lines 25/133) lands first; re-verify position at implementation time |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `scripts/eventbus/app.py`, `tests/deploy/test_setup_services_eventbus.py`

### Companion test files
- `tests/deploy/test_setup_services_eventbus.py`
  - Procedure: replace the no-op alias-restore monkeypatch at line 339 (`monkeypatch.setattr(auth, "_TOKEN_PRINCIPAL_MAP", auth._TOKEN_PRINCIPAL_MAP)`) with the conftest-aligned generation pattern (sibling document 05): snapshot `original_generation = auth.current_generation()` before the client context and, on teardown, `monkeypatch.setattr(auth, "_CURRENT_GENERATION", original_generation)`. Keep the db_conn restores at lines 337-338 unchanged. This file's workflow-schema fixture lines (25, 133) belong to plan001 document implementations/20261107-081028_23_tests_deploy_test_setup_services_eventbus.py.md, which lands first; regions are disjoint (Plan Assumptions).
  - Validation: `uv run pytest tests/deploy/test_setup_services_eventbus.py` green (Plan Validation row 4); `grep -n "_TOKEN_PRINCIPAL_MAP" tests/deploy/test_setup_services_eventbus.py` -> 0.
