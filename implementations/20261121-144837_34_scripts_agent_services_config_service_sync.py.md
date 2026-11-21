## Goal

Remove the unused `rag_cfg` parameter from `ServiceSyncer.sync_all()`, since the caller can no longer supply a RAG section (REQ-001; fallout of Plan rows 1, 33).

## Scope
**Release unit**: RU-1

## Assumptions
- No test file exists for this module; verification is the affected test run named by the Plan's amendment row (Plan row 33's tests).
- `llm_cfg` and `tool_cfg` keep their behaviour; the syncer reads `ctx.cfg.llm` and `ctx.cfg.tool` in its body, so those parameters stay.

## Design decisions
- The parameter is deleted, not renamed: the body never reads it, so there is no behaviour to preserve.
- The docstring's parameter list and the "three config sections" wording are updated to two.

## Alternatives considered
- Keep the parameter for signature stability: rejected — an unused parameter that cannot be supplied is dead surface, and the Plan's scope is to remove the RAG section, not to keep a placeholder for it.

## Implementation
### Target file
`scripts/agent/services/config_service_sync.py`
### Procedure
- Remove `rag_cfg` from `sync_all()` (lines 34-49) and its docstring entry.
- Update the summary line "Sync all three config sections" to name the two sections it actually syncs.
- Keep `SyncResult` and the `services_required` guard behaviour unchanged.
### Method
- Signature and docstring change only; no change to the sync logic.
### Details
- Verified 2026-11-21: the body (lines 50-86) reads only `ctx.cfg.llm` and `ctx.cfg.tool`, which is why the parameter can be dropped without behaviour change.

## Compatibility considerations
- The single call site is `scripts/agent/services/config_reload.py` (Plan row 33), which must land in the same release unit.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -v` (affected test; no test file exists for this module)
- `uv run ruff check scripts/agent/services/config_service_sync.py`, `uv run mypy scripts/agent/services/config_service_sync.py`

## Completion criteria
- `sync_all()` takes the two sections it uses; no `rag_cfg` symbol remains in this module; the reported `applied`/`skipped` results are unchanged.

## Out of Scope
- The call site (Plan row 33), the dataclass removal (Plan row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test file exists for this module; covered by the affected test run. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared reload surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (amendment 2026-11-21, class fallout)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/config_service_sync.py`
