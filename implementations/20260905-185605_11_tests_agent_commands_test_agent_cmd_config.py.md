## Goal
Remove `ctx.cfg.rag.use_semantic_cache`/`semantic_cache_threshold`/
`semantic_cache_max_size` fixture-attribute assignments from
`tests/agent/commands/test_agent_cmd_config.py`, made obsolete by procedure document
`03`'s removal of these `RAGConfig` fields (`REQ-009`).

## Scope
- **In-Scope**: remove `ctx.cfg.rag.use_semantic_cache = False` (line 199),
  `ctx.cfg.rag.semantic_cache_threshold = 0.92` (line 200), and
  `ctx.cfg.rag.semantic_cache_max_size = 100` (line 201).
- **Out-of-Scope**: every other `ctx.cfg.*` attribute assignment in the same fixture
  setup — confirmed unrelated by reading the surrounding lines; every other test in
  this file.

## Assumptions
- These three lines set attributes on an already-constructed `AgentConfig`/`RAGConfig`
  instance (`ctx.cfg.rag.*`) directly, not via constructor keyword arguments — once
  procedure document `03` removes the three `RAGConfig` fields, this pattern would
  raise `AttributeError` (a regular, non-frozen `@dataclass` still rejects assignment
  to an attribute it never declared, since Python does not silently create new
  instance attributes for a class using `__slots__`-free plain assignment only if the
  class permits arbitrary attributes — confirm `RAGConfig` has no `__slots__`
  restriction before assuming this would error vs. silently succeed as a stray
  attribute; regardless, the assignment is meaningless once `RagPipeline` reads
  nothing from these fields).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove all three lines together as one contiguous block, since they set the same
  fixture's cache-related sub-attributes and were discovered together by this Plan's
  repository-wide search.

## Alternatives considered
N/A: straightforward removal of three now-meaningless attribute assignments.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_config.py`

### Procedure
1. Remove `ctx.cfg.rag.use_semantic_cache = False` (line 199).
2. Remove `ctx.cfg.rag.semantic_cache_threshold = 0.92` (line 200).
3. Remove `ctx.cfg.rag.semantic_cache_max_size = 100` (line 201).

### Method
Direct removal via `Edit`.

### Details
- Confirm after editing: `rg -n "semantic_cache"
  tests/agent/commands/test_agent_cmd_config.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `03` (`scripts/agent/config_dataclasses.py`) if `RAGConfig`
  rejects assignment to an undeclared attribute.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` — all tests pass.
- `rg -n "semantic_cache" tests/agent/commands/test_agent_cmd_config.py` — zero
  matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-8`).

## Out of scope
- `scripts/agent/config_dataclasses.py`'s `RAGConfig` (procedure document `03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (remove cache references from mocks and fixtures)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/commands/test_agent_cmd_config.py
