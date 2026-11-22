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
- Finding (adversarial verification, 2026-11-21): the "no assertion changes proven" claim did not hold for `tests/agent/test_repl_health.py`. It sets `ctx.cfg.rag.embed_url` on `MagicMock()` contexts; after the entry reads `ctx.cfg.memory.memory_embed_url`, the un-set attribute is an auto-created MagicMock (truthy), so the `if not url: continue` skip paths changed behavior — 11 tests failed. The fixture assignments were switched to `ctx.cfg.memory.memory_embed_url`; no assertion semantics changed. The affected test then passes unchanged (46 passed).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Implemented; no ctx.cfg.rag remains |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Affected-test claim disproved; fixture inputs adjusted (see Compatibility finding); 46 passed |
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
- **Requirement ID**: REQ-001 (the health entry reads the Memory-owned endpoint)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/services/mcp_health.py`
