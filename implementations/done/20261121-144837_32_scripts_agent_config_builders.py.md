## Goal

Update the assembly call site so the Agent configuration no longer carries a RAG section, after the section builder is removed (REQ-001; fallout of Plan row 2).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/test_config_builders.py` is not this row's companion: it is named by two rows, so it keeps its own document (Plan row 22); it is run here as an affected test.
- The assembly order is preserved: validation happens before construction, as it does today.

## Design decisions
- `AgentConfig(...)` loses the `rag=` keyword; nothing replaces it, because `memory=` already carries the endpoint through the builder in Plan row 2.
- No alias is kept for the removed builder: the Current-Specification-Only policy rejects the old key location.

## Alternatives considered
- Keep `rag=_build_memory_config(cfg)` as a transitional mapping: rejected — it reintroduces the ownership mismatch this Plan removes.

## Implementation
### Target file
`scripts/agent/config_builders.py`
### Procedure
- Remove the `_build_rag_config` import (line 37) and the `rag=_build_rag_config(cfg)` keyword (line 125).
- Keep `_build_memory_config(cfg)` (line 127) as the only path that supplies the endpoint.
- Update the module docstring's assembly description if it lists the RAG section.
### Method
- Call-site deletion only; no change to the validation-then-assembly ordering.
### Details
- Verified 2026-11-21: the assembly builds `llm`, `tool`, `approval`, `memory`, `observability`, `diagnostics`, and `mcp` sections; removing `rag` leaves the other sections and the cross-field validation path defined by Plan row 1.
- Finding (2026-11-22, execution): Procedure 3 was not applicable — the module docstring does not enumerate the sections, so nothing there mentioned the RAG section.
- Finding (2026-11-22, execution): the section list above is incomplete for what the implementation needs. `build_agent_config()` also builds `db=build_db_config(cfg)` and `maintenance=DbMaintenanceConfig.from_mapping(cfg)`; this is the single ownership point for the Agent process, and it is required because every `db/` consumer now receives the typed objects rather than resolving a path itself, so `AgentConfig` has to carry them. Adding those two keywords is outside this row's Procedure (call-site deletion only) and is the consequence of the release unit's injected-configuration contract.

## Compatibility considerations
- This row must land in the same release unit as Plan rows 1, 2, and 19; on its own it breaks the assembly.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v` (affected test)
- `uv run ruff check scripts/agent/config_builders.py`, `uv run mypy scripts/agent/config_builders.py`

## Completion criteria
- No `_build_rag_config` import or call remains; `build_agent_config()` assembles a configuration with no RAG section and passes the existing tests.

## Out of Scope
- The builder itself (Plan row 2), the dataclass (Plan row 1), the config file (Plan row 19), test assertions (Plan row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-21 | 2026-11-21 | Implemented (import + kwarg removed) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | N/A: no assertion changes proven |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | N/A |

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
- **Related target files**: `scripts/agent/config_builders.py`
