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
- Finding (2026-11-22, execution): the Details statement is not accurate. The body also reads `ctx.cfg.approval.tool_safety_tiers` (the runtime-service sync), and it does not read the `llm_cfg` and `tool_cfg` parameters at all — it reads `ctx.cfg.*`. So the Assumption's justification for keeping those parameters ("the syncer reads `ctx.cfg.llm` and `ctx.cfg.tool` in its body") does not hold: after this row the two parameters are unused surface, which is the same condition the Alternatives section used to reject keeping `rag_cfg`. The row was implemented as written (only `rag_cfg` removed); whether the remaining unused parameters should be removed or made to be used is a separate decision, recorded here rather than decided in this row.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: sync_all() takes the remaining typed sections only. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | N/A: no test file for this module; covered by the affected tests, which are green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation rows are separate procedure documents. |

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
