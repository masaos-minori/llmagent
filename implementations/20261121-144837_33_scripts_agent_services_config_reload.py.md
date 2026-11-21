## Goal

Move Memory from the direct-section loop to the validated-section loop, so a Memory reload is validated before commit, and drop the RAG section from the reload path (REQ-001, REQ-002; fallout of Plan rows 1, 5, 6).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/services/test_config_reload.py` is not this row's companion: it is named by two rows, so it keeps its own document (Plan row 24); it is run here as an affected test.
- `mcp` stays in the direct path; only `memory` moves.

## Design decisions
- The section tuple becomes `("llm", "memory", "tool", "approval")` and the direct loop becomes `("mcp",)`: the routing decision lives here, while the helpers in Plan row 6 stay unchanged.
- The `ServiceSyncer.sync_all()` call drops the RAG argument, matching Plan row 34; nothing is passed in its place, because the syncer never used it.

## Alternatives considered
- Keep `memory` in the direct loop and call the validators inside `prepare_direct_section()`: rejected — the commit phase then applies `setattr` values that were validated against a different object, and the outcome report cannot be trusted.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`
### Procedure
- Change the candidate loop's section tuple from `("llm", "rag", "tool", "approval")` (line 111) to the validated sections without `rag` and with `memory`.
- Reduce the direct loop from `("memory", "mcp")` (line 126) to `("mcp",)`.
- Remove `self._ctx.cfg.rag` from the `sync_all()` call (line 207).
- Keep the `masked_fields` extra handling for `tool` and the commit-phase order (validate all, then apply).
### Method
- Routing change only; no change to the helpers, the outcome model, or the classification of startup-only fields.
### Details
- Verified 2026-11-21: `prepare_validated_section()` requires the section object to be a real dataclass, which `build_agent_config()` already guarantees for Memory; `memory_embed_url` (new) becomes a registry entry through Plan row 5, so `extra_changed_fields` is not needed here.

## Compatibility considerations
- The outcome report shape is unchanged; `memory_embed_enabled` keeps its startup-only classification, so the report content for that key is unchanged.
- This row must land with Plan rows 1, 5, 6, 34; alone it changes behaviour without the field being a registry entry.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v` (affected tests)
- `uv run ruff check scripts/agent/services/config_reload.py`, `uv run mypy scripts/agent/services/config_reload.py`

## Completion criteria
- A Memory change is validated through a typed candidate before commit; `rag` appears nowhere in this module; the direct path handles only `mcp`.

## Out of Scope
- The section helpers (Plan row 6), the registry entry (Plan row 5), the syncer signature (Plan row 34), test assertions (Plan row 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model REQ-002 validates through is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no assertion changes proven beyond REQ-002 scope; run as affected test. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified after that Issue lands |
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
- **Requirement ID**: REQ-002 (amendment 2026-11-21, class fallout)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/config_reload.py`
