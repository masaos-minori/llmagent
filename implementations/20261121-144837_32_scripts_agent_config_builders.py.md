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
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no assertion changes proven; run as affected test. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
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
- **Related target files**: `scripts/agent/config_builders.py`
