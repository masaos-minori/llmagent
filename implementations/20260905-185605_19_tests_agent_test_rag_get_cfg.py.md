## Goal
Remove `semantic_cache_max_size`/`semantic_cache_threshold`/`use_semantic_cache`
keyword arguments from `tests/agent/test_rag_get_cfg.py`'s module-level
`_RAG_CFG_BASE = RagConfigImpl(...)` fixture, made obsolete by procedure document `01`
(`REQ-001`, `REQ-009`).

## Scope
- **In-Scope**: remove `semantic_cache_max_size=0,` (line 16),
  `semantic_cache_threshold=0.0,` (line 17), and `use_semantic_cache=False,` (line 18)
  from the `_RAG_CFG_BASE` constructor call.
- **Out-of-Scope**: every other keyword argument in `_RAG_CFG_BASE` — confirmed
  unrelated by reading the full constructor call; every test in this file that uses
  `_RAG_CFG_BASE` via `dc_replace(_RAG_CFG_BASE, ...)` — confirmed unaffected, since
  `dataclasses.replace()` only overrides the fields a caller names, and no test in
  this file is confirmed (by this Plan's evidence, "`RagConfigImpl(...)` fixture keys")
  to override any of the three removed fields specifically.

## Assumptions
- `RagConfigImpl` (procedure document `01`) is a frozen `@dataclass` requiring every
  field as a constructor argument (no defaults, confirmed by reading
  `scripts/rag/models_config.py`) — once the three fields are removed there, this
  module-level fixture must not pass them, or construction raises
  `TypeError: unexpected keyword argument`.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove all three keyword arguments together — they are the fixture's cache-tuning
  parameters, contiguous at the top of the constructor call.

## Alternatives considered
N/A: straightforward removal of three now-invalid constructor arguments from a
module-level fixture.

## Implementation
### Target file
`tests/agent/test_rag_get_cfg.py`

### Procedure
1. Remove `semantic_cache_max_size=0,` (line 16).
2. Remove `semantic_cache_threshold=0.0,` (line 17).
3. Remove `use_semantic_cache=False,` (line 18).

### Method
Direct removal via `Edit` on three keyword-argument lines in a module-level
constructor call.

### Details
- This fixture is module-level (`_RAG_CFG_BASE`, defined once at import time) — every
  test in this file using it (via direct reference or `dc_replace()`) is affected by
  this single edit; confirm no test overrides one of the three removed fields via
  `dc_replace(_RAG_CFG_BASE, use_semantic_cache=...)` or similar before finalizing
  (none found by this Plan's evidence, but re-check at implementation time per Step 3a
  Adversarial Verification).
- Confirm after editing: `rg -n "semantic_cache" tests/agent/test_rag_get_cfg.py`
  returns zero matches.

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `01` (`RagConfigImpl`).

## Validation plan
- `uv run pytest tests/agent/test_rag_get_cfg.py -v` — all tests pass; no collection
  error from the module-level fixture construction.
- `rg -n "semantic_cache" tests/agent/test_rag_get_cfg.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-1`,
  `AC-8`).

## Out of scope
- `scripts/rag/models_config.py`'s `RagConfigImpl` (procedure document `01`).
- Every test method's own logic in this file beyond the shared fixture.

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
- **Requirement ID**: `REQ-001` (fixture constructs `RagConfigImpl` directly with the removed fields)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/test_rag_get_cfg.py
