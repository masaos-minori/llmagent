## Goal
Remove assertions on `RAGConfig`'s three removed fields and delete
`test_semantic_cache_without_embed_url_raises()`, since it tests
`_validate_semantic_cache_url()` (procedure document `03`) directly, in
`tests/agent/test_config_dataclasses.py` (`REQ-001`, `REQ-009`).

## Scope
- **In-Scope**:
  - `TestRAGConfigValidation.test_defaults_are_valid`: remove `assert
    cfg.use_semantic_cache is False`, `assert cfg.semantic_cache_threshold == 0.92`,
    `assert cfg.semantic_cache_max_size == 100` (lines 134-136).
  - Remove `test_semantic_cache_without_embed_url_raises()` (lines 262-265) in its
    entirety — its sole purpose is asserting
    `AgentConfig(rag=RAGConfig(use_semantic_cache=True, embed_url=""))` raises
    `ValueError` via `_validate_semantic_cache_url()`, a method procedure document `03`
    removes entirely.
- **Out-of-Scope**: `test_agent_config_has_no_workflow_require_approval_field`
  (immediately preceding the removed test) and `test_memory_embed_without_embed_url_raises`/
  `test_memory_layer_without_jsonl_dir_raises` (immediately following) — confirmed
  unrelated by reading their bodies, each testing a different `_validate_cross_field()`
  sub-check (`_validate_memory_embed_url()`/`_validate_memory_jsonl_dir()`, both
  Out-of-Scope for procedure document `03`); the remaining assertions in
  `test_defaults_are_valid` (`embed_url`, `use_refiner`, `refiner_*`) — confirmed
  unrelated.

## Assumptions
- `RAGConfig(use_semantic_cache=True, embed_url="")` (line 263) will raise
  `TypeError: unexpected keyword argument 'use_semantic_cache'` once procedure
  document `03` lands, making this test unrunnable as-is even before considering that
  its assertion subject (`_validate_semantic_cache_url()`) no longer exists — both
  reasons independently require deleting this test.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Delete `test_semantic_cache_without_embed_url_raises()` outright rather than
  adapting it — no replacement behavior exists to test (the cross-field validation
  rule it checks is removed, not changed, by procedure document `03`).
- Leave the two neighboring `_validate_cross_field()` tests
  (`test_memory_embed_without_embed_url_raises`, `test_memory_layer_without_jsonl_dir_raises`)
  untouched — they test different, still-active sub-checks
  (`_validate_memory_embed_url()`, `_validate_memory_jsonl_dir()`) that procedure
  document `03` explicitly does not remove.

## Alternatives considered
N/A: the test's sole subject (a validator method) is removed by another procedure
document with no replacement; no adaptation is possible.

## Implementation
### Target file
`tests/agent/test_config_dataclasses.py`

### Procedure
1. In `TestRAGConfigValidation.test_defaults_are_valid`, remove the three assertions
   for `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size`
   (lines 134-136).
2. Delete `test_semantic_cache_without_embed_url_raises()` (lines 262-265) in its
   entirety, including its blank-line separation from the surrounding tests
   (confirm one blank line remains between
   `test_agent_config_has_no_workflow_require_approval_field` and
   `test_memory_embed_without_embed_url_raises` after deletion).

### Method
Direct `Edit`: one assertion-block removal, one whole-test-method removal.

### Details
- Confirm `test_defaults_are_valid`'s remaining assertions
  (`embed_url`, `use_refiner`, `refiner_max_tokens`, `refiner_timeout`,
  `refiner_max_chars_per_chunk`) still match `RAGConfig`'s post-procedure-document-`03`
  defaults exactly.
- Confirm after editing: `rg -n "semantic_cache"
  tests/agent/test_config_dataclasses.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `03` (`scripts/agent/config_dataclasses.py`'s `RAGConfig` and
  `_validate_semantic_cache_url()` removal).

## Validation plan
- `uv run pytest tests/agent/test_config_dataclasses.py -v` — all remaining tests
  pass; no collection error from the deleted test method.
- `rg -n "semantic_cache" tests/agent/test_config_dataclasses.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys or
  `_validate_semantic_cache_url()`'s behavior remains in this file (Plan `AC-1`,
  `AC-5`, `AC-8`).

## Out of scope
- `test_memory_embed_without_embed_url_raises`/`test_memory_layer_without_jsonl_dir_raises`
  and every other test in this file.
- `scripts/agent/config_dataclasses.py`'s `RAGConfig`/`_validate_semantic_cache_url()`
  (procedure document `03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation IS the test removal |
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
- **Requirement ID**: `REQ-001` (remove assertions on removed fields/validator)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/test_config_dataclasses.py
