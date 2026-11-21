## Goal

Point the `embed-llm` health entry at the Memory-owned endpoint (REQ-001, AC-002).

## Scope
**Release unit**: RU-1

## Assumptions
- `tests/agent/test_repl_health.py` is run as an affected test only; it builds `MagicMock()` contexts, so it keeps passing without change while the field exists. It is not a target row.

## Design decisions
- Only the attribute path in the health-entry tuple changes; the optional-service posture semantics (`False` flag for `embed-llm`) are unchanged.

## Alternatives considered
- N/A: single-section read, no alternative.

## Implementation
### Target file
`scripts/agent/services/mcp_health.py`
### Procedure
- Change the `embed-llm` entry (line 306) from `ctx.cfg.rag.embed_url` to `ctx.cfg.memory.memory_embed_url`.
### Method
- One attribute path inside the existing entry list; flag and ordering unchanged.
### Details
- Verified 2026-11-21: the entry list is built in one place, and `embed-llm` is documented as optional/degraded-mode in the module docstring; nothing else in this module reads the endpoint.

## Compatibility considerations
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` mutates `cfg.rag_top_k`, not the endpoint, and is unaffected.

## Security considerations
- N/A: health reporting only; no new trust boundary.

## Rollback considerations
- N/A: revert the commit within release unit RU-1.

## Validation plan
- `uv run pytest tests/agent/test_repl_health.py -v` (affected test)
- `uv run ruff check scripts/agent/services/mcp_health.py`, `uv run mypy scripts/agent/services/mcp_health.py`

## Completion criteria
- The health check reports the endpoint value that Memory owns; no `ctx.cfg.rag` reference remains in this module.

## Out of Scope
- The field and its validation (Plan row 1); the runtime client construction (Plan row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model REQ-002 validates through is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no assertion changes proven; run as affected test. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared field-registry/validation surface must be re-verified |
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
- **Requirement ID**: REQ-001 (the health entry reads the Memory-owned endpoint)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/mcp_health.py`
