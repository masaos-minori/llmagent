## Goal
Remove `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size`
references from `tests/agent/services/test_config_reload.py` — three `RAGConfig(...)`
fixture constructions, one multi-field reload assertion, and two `_collect_field_changes()`
unit tests — made obsolete by procedure documents `03`/`08` (`REQ-006`, `REQ-009`).

## Scope
- **In-Scope**:
  - Three `RAGConfig(...)` fixture constructions (lines 47-54, 101-108, 651-658, each
    identical): remove `use_semantic_cache=False,`, `semantic_cache_threshold=0.92,`,
    `semantic_cache_max_size=100,`.
  - `test_multi_field_reload_applies_all` (around line 200-215): remove
    `ctx.cfg.rag.use_semantic_cache = False` (setup), the `"use_semantic_cache": True,`
    entry in the `apply_config_dict({...})` call, and
    `assert ctx.cfg.rag.use_semantic_cache is True` — leaving the test's
    `llm_temperature`/`serial_tool_calls` setup and assertions intact (this test's
    purpose is multi-field reload; the cache field was one of three fields exercised,
    not the whole test's subject).
  - `test_consolidated_method_collects_all_rag_fields` (around line 719-746): remove
    `"use_semantic_cache": True,`, `"semantic_cache_threshold": 0.95,`,
    `"semantic_cache_max_size": 200,"` from the `new_cfg` dict; remove
    `assert "use_semantic_cache" in rag_changes`, `assert "semantic_cache_threshold" in
    rag_changes`, `assert "semantic_cache_max_size" in rag_changes`; change
    `assert len(rag_changes) == 9` to `assert len(rag_changes) == 6` (9 RAG fields
    minus the 3 removed).
  - `test_consolidated_method_handles_partial_updates` (around line 791-810): replace
    `"use_semantic_cache": False,` in `new_cfg` with a still-valid RAG field (e.g.
    `"embed_url": "http://localhost:8080/embed",`) so the test's "exactly one RAG
    field present → exactly one collected" assertion still has a subject; replace
    `assert "use_semantic_cache" in rag_changes` / `assert rag_changes["use_semantic_cache"]
    is False` with the equivalent assertions for the substituted field.
- **Out-of-Scope**: every other field in the three `RAGConfig(...)` fixtures
  (`embed_url`, `use_refiner`, `refiner_*`) — confirmed unrelated; every other test
  method in this file (LLM/SSE/tool field collection tests) — confirmed unrelated by
  reading the full file's test list.

## Assumptions
- Same downstream dependency as procedure document `03`: these `RAGConfig(...)`
  fixture constructions must not supply the three removed keyword arguments once that
  document lands, or they will raise `TypeError: unexpected keyword argument`.
- `test_consolidated_method_handles_partial_updates`'s substitute field
  (`embed_url`) is confirmed to be read by `_collect_field_changes()`'s "# RAG fields"
  section (`FIELD_EMBED_URL`, per procedure document `08`'s own investigation) and to
  remain untouched by this Plan — a safe, stable substitute.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- **Correction to the Plan's stated evidence**: the Plan's row for this file states
  "Directly tests `_apply_rag_params()` behavior REQ-006 removes" with evidence
  "`rg -c` match count 9" — Step 3a Adversarial Verification found the actual match
  count is 21 lines across three fixture constructions, one integration test, and two
  `_collect_field_changes()`-targeting unit tests (not `_apply_rag_params()`, which
  this file does not directly test — confirmed by `grep -n
  "_apply_rag_params\|_collect_field_changes"` showing only `_collect_field_changes`
  called here). This is recorded here as the corrected, actual scope for this row.
- For `test_consolidated_method_collects_all_rag_fields`, adjust the numeric assertion
  (`len(rag_changes) == 9` → `== 6`) rather than leaving a now-incorrect count — this
  test's entire purpose is verifying the exact count of collected RAG fields, so the
  count itself is not incidental and must track the field removal.
- For `test_consolidated_method_handles_partial_updates`, substitute rather than
  delete the RAG-field entry — this test's structure (`assert len(rag_changes) == 1`)
  requires exactly one RAG key present in `new_cfg`; deleting the key without a
  substitute would make `rag_changes` empty, breaking the test's own `== 1` assertion
  and its "partial updates" premise (one field present per config-type).

## Alternatives considered
- Deleting `test_consolidated_method_handles_partial_updates` outright instead of
  substituting its RAG field — rejected: the test's LLM (`llm_temperature`) and tool
  (`max_tool_turns`) assertions remain fully valid and independent of the cache
  removal; deleting the whole test would lose that unrelated coverage for no reason.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`

### Procedure
1. In the three identical `RAGConfig(...)` fixture blocks (lines 47-54, 101-108,
   651-658), remove `use_semantic_cache=False,`, `semantic_cache_threshold=0.92,`, and
   `semantic_cache_max_size=100,` from each.
2. In `test_multi_field_reload_applies_all`, remove `ctx.cfg.rag.use_semantic_cache =
   False`, the `"use_semantic_cache": True,` dict entry, and
   `assert ctx.cfg.rag.use_semantic_cache is True` — leave the `llm_temperature`/
   `serial_tool_calls` setup and assertions unchanged.
3. In `test_consolidated_method_collects_all_rag_fields`, remove the three
   `new_cfg` dict entries and their three corresponding `assert ... in rag_changes`
   lines; change `assert len(rag_changes) == 9` to `assert len(rag_changes) == 6`.
4. In `test_consolidated_method_handles_partial_updates`, replace
   `"use_semantic_cache": False,` with `"embed_url": "http://localhost:8080/embed",`;
   replace `assert "use_semantic_cache" in rag_changes` with
   `assert "embed_url" in rag_changes`; replace
   `assert rag_changes["use_semantic_cache"] is False` with
   `assert rag_changes["embed_url"] == "http://localhost:8080/embed"`.

### Method
Direct `Edit` across four locations: three mechanical fixture-arg removals, one
integration-test line removal (with unrelated assertions preserved), one numeric-count
test edit, one field-substitution edit.

### Details
- Confirm after step 3: the remaining six RAG fields
  `_collect_field_changes()` reads (`embed_url`, `web_search_url`, `use_refiner`,
  `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`) match exactly
  the `new_cfg` dict's remaining six keys and `rag_changes`'s expected six entries —
  recount rather than assume.
- Confirm after editing: `rg -n "semantic_cache"
  tests/agent/services/test_config_reload.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure documents `03` (`RAGConfig`) and `08` (`_collect_field_changes()`'s RAG
  fields).

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -v` — all tests pass,
  including the corrected count assertion and substituted-field assertions.
- `rg -n "semantic_cache" tests/agent/services/test_config_reload.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-6`,
  `AC-8`).
- `test_consolidated_method_collects_all_rag_fields`'s count assertion and
  `test_consolidated_method_handles_partial_updates`'s substituted assertion both pass.

## Out of scope
- `scripts/agent/config_dataclasses.py`'s `RAGConfig` (procedure document `03`).
- `scripts/agent/services/config_reload.py`'s `_collect_field_changes()`/
  `_apply_rag_params()` (procedure document `08`).
- Every LLM/SSE/tool-field test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Count/substitution edits are part of this document's own scope |
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
- **Requirement ID**: `REQ-006` (remove cache references from configuration reload paths); `REQ-009` (update obsolete tests)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/services/test_config_reload.py
