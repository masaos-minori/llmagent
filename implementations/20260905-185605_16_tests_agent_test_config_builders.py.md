## Goal
Update `class TestBuildRAGConfig`'s three tests in `tests/agent/test_config_builders.py`
to assert `_build_rag_config()` no longer reads or forwards the three removed keys,
per procedure document `04` (`REQ-002`, `REQ-009`).

## Scope
- **In-Scope**:
  - `test_empty_dict_returns_defaults`: remove `assert cfg.use_semantic_cache is
    False`, `assert cfg.semantic_cache_threshold == 0.92`, `assert
    cfg.semantic_cache_max_size == 100` (lines 121-123).
  - `test_overrides_are_applied`: this test's sole subject is
    `{"use_semantic_cache": True}` → `cfg.use_semantic_cache is True` — since the
    field it exercises no longer exists, replace both the override dict and the
    assertion with a still-valid field (e.g. `{"use_refiner": True}` →
    `cfg.use_refiner is True`), preserving the test's purpose (proving a single-key
    override is applied) rather than deleting it.
  - `test_every_field_override_is_independently_reflected`: remove
    `"use_semantic_cache": True,`, `"semantic_cache_threshold": 0.5,`,
    `"semantic_cache_max_size": 9,` from the `overrides` dict (lines 136-138) — the
    surrounding `for key, value in overrides.items(): assert getattr(cfg, key) ==
    value` loop needs no other change, since it iterates whatever keys remain.
- **Out-of-Scope**: `embed_url`/`use_refiner`/`refiner_*` assertions in the same three
  tests — confirmed unrelated; `class TestBuildToolConfig` (`_TOOL_DEFAULTS`) and every
  other test class in this file — confirmed unrelated by reading the surrounding
  sections.

## Assumptions
- `_build_rag_config()` (procedure document `04`) no longer accepts or returns
  `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size` once that
  document lands — `getattr(cfg, "use_semantic_cache")` would raise `AttributeError`
  on the returned `RAGConfig` instance if this document's edit did not also remove the
  corresponding overrides/assertions.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Substitute (not delete) `test_overrides_are_applied`'s subject field — its entire
  purpose is verifying that a single-key override dict changes exactly the
  corresponding `RAGConfig` attribute; `use_refiner` is a boolean field with the same
  default-`False`/override-`True` shape, making it a direct, minimal-change substitute
  that preserves the test's original intent.
- For `test_every_field_override_is_independently_reflected`, rely on the existing
  generic `for key, value in overrides.items()` loop rather than adding new
  per-field assertions — removing the three dict entries is sufficient; the loop
  automatically stops checking removed fields once they are absent from `overrides`.

## Alternatives considered
- Deleting `test_overrides_are_applied` entirely instead of substituting its field —
  rejected: the test verifies a distinct, still-relevant behavior (single-key override
  application) independent of which field is used as the example; deleting it would
  lose that coverage for no reason.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
1. In `test_empty_dict_returns_defaults`, remove the three assertions for
   `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size` (lines
   121-123).
2. In `test_overrides_are_applied`, replace `_build_rag_config({"use_semantic_cache":
   True})` with `_build_rag_config({"use_refiner": True})`, and replace
   `assert cfg.use_semantic_cache is True` with `assert cfg.use_refiner is True`.
3. In `test_every_field_override_is_independently_reflected`'s `overrides` dict,
   remove `"use_semantic_cache": True,`, `"semantic_cache_threshold": 0.5,`, and
   `"semantic_cache_max_size": 9,` (lines 136-138).

### Method
Direct `Edit`: two assertion-block removals and one field-substitution.

### Details
- Confirm `test_empty_dict_returns_defaults`'s remaining assertions
  (`embed_url`, `use_refiner`, `refiner_max_tokens`, `refiner_timeout`,
  `refiner_max_chars_per_chunk`) still match `RAGConfig`'s post-procedure-document-`03`
  defaults exactly.
- Confirm after editing: `rg -n "semantic_cache" tests/agent/test_config_builders.py`
  returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure documents `03` (`RAGConfig`) and `04` (`_build_rag_config()`).

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v` — all tests pass, including
  the substituted `test_overrides_are_applied`.
- `rg -n "semantic_cache" tests/agent/test_config_builders.py` — zero matches.

## Completion criteria
- `class TestBuildRAGConfig`'s three tests pass against the modified
  `_build_rag_config()` with no reference to any of the three removed keys (Plan
  `AC-3`, `AC-8`).

## Out of scope
- `class TestBuildToolConfig` and every other test class in this file.
- `scripts/agent/config_builders.py`'s `_build_rag_config()` itself (procedure
  document `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Field substitution is part of this document's own scope |
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
- **Requirement ID**: `REQ-002` (assert `_build_rag_config()` no longer reads/forwards the three keys)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/test_config_builders.py
