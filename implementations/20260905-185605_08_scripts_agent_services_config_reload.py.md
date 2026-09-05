## Goal
Remove `FIELD_USE_SEMANTIC_CACHE`/`FIELD_SEMANTIC_CACHE_THRESHOLD`/
`FIELD_SEMANTIC_CACHE_MAX_SIZE` constants and every `if` block reading them, from
`scripts/agent/services/config_reload.py` (`REQ-006`).

## Scope
- **In-Scope**: remove the three constant definitions (`FIELD_USE_SEMANTIC_CACHE =
  "use_semantic_cache"`, line 49; `FIELD_SEMANTIC_CACHE_THRESHOLD =
  "semantic_cache_threshold"`, line 71; `FIELD_SEMANTIC_CACHE_MAX_SIZE =
  "semantic_cache_max_size"`, line 72); remove the three `if` blocks in
  `_collect_field_changes()`'s "# RAG fields" section that read these constants (lines
  256-257, 260-261, 262-263); remove the three `if` blocks in `_apply_rag_params()`
  that read the same three keys as literal strings (lines 503-504, 505-506, 507-508).
- **Out-of-Scope**: every other `FIELD_*` constant and `if` block in both methods
  (`FIELD_EMBED_URL`, `FIELD_WEB_SEARCH_URL`, `FIELD_USE_REFINER`, and all LLM/SSE
  fields) — confirmed unrelated by reading both methods in full; `_apply_rag_tool_params()`,
  `_apply_llm_context_params()`, `_apply_tool_params()`, `_sync_services()`, and every
  other method in this file — confirmed unrelated.

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`07`: this change must not
  be applied until `semcacherm` has landed.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- **Correction to the Plan's stated evidence**: the Plan's `Implementation Target
  Files` row for this file names only `_apply_rag_params()`'s three `if` blocks
  (Repository Evidence: "`rg -n \"SEMANTIC_CACHE\"` confirmed constants and usage in
  `_apply_rag_params()`"). Step 3a Adversarial Verification found a **second**,
  structurally identical set of three `if` blocks in `_collect_field_changes()`'s "#
  RAG fields" section (lines 256-263), using the same three constants — this is
  recorded here as the corrected, actual scope for this row, per
  `skills/plan-to-implementation-procedure/workflow.md` Step 3a (a stale/undercounted
  claim about the same row's target file is corrected in the generated document; the
  file path and Requirement linkage are unchanged, so no Plan amendment is required).
  Both call sites must be removed together — the three constants have exactly two
  readers (`_collect_field_changes()` and `_apply_rag_params()`), and removing the
  constants without removing both readers would raise `NameError` at import/call time.
- `_collect_field_changes()`'s docstring states it "Replaces `_collect_request_values()`
  and `_apply_llm_prompt_params()`" — this document does not investigate whether
  `_apply_rag_params()` is itself a partially-superseded duplicate of
  `_collect_field_changes()`'s RAG section, since that question is about a
  pre-existing structural duplication unrelated to this Plan's `use_semantic_cache`/
  `semantic_cache_threshold`/`semantic_cache_max_size` removal — both call sites are
  removed as-is, without further refactoring, per `AGENTS.md` Global Rule 5 scope
  discipline.

## Alternatives considered
- Removing only `_apply_rag_params()`'s three blocks (matching the Plan's literal
  evidence) and leaving `_collect_field_changes()`'s untouched — rejected: this would
  leave `NameError`s at the three now-undefined constant references in
  `_collect_field_changes()` once the constants are removed, which is not a viable
  partial state.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. In `_collect_field_changes()`'s "# RAG fields" section, remove: `if (vb :=
   _get_bool(new_cfg, FIELD_USE_SEMANTIC_CACHE)) is not None: rag_changes[FIELD_USE_SEMANTIC_CACHE]
   = vb` (lines 256-257); `if (vf := _get_float(new_cfg, FIELD_SEMANTIC_CACHE_THRESHOLD))
   is not None: rag_changes[FIELD_SEMANTIC_CACHE_THRESHOLD] = vf` (lines 260-261); `if
   (vi := _get_int(new_cfg, FIELD_SEMANTIC_CACHE_MAX_SIZE)) is not None:
   rag_changes[FIELD_SEMANTIC_CACHE_MAX_SIZE] = vi` (lines 262-263) — leaving
   `FIELD_EMBED_URL`, `FIELD_WEB_SEARCH_URL`, and `FIELD_USE_REFINER`'s blocks
   (interleaved with the removed ones) intact.
3. In `_apply_rag_params()`, remove: `if (vb := _get_bool(new_cfg,
   "use_semantic_cache")) is not None: changes["use_semantic_cache"] = vb` (lines
   503-504); `if (v := _get_float(new_cfg, "semantic_cache_threshold")) is not None:
   changes["semantic_cache_threshold"] = v` (lines 505-506); `if (v := _get_int(new_cfg,
   "semantic_cache_max_size")) is not None: changes["semantic_cache_max_size"] = v`
   (lines 507-508).
4. Remove `FIELD_USE_SEMANTIC_CACHE = "use_semantic_cache"` (line 49).
5. Remove `FIELD_SEMANTIC_CACHE_THRESHOLD = "semantic_cache_threshold"` (line 71).
6. Remove `FIELD_SEMANTIC_CACHE_MAX_SIZE = "semantic_cache_max_size"` (line 72).

### Method
Direct `Edit`: six `if`-block removals across two methods, followed by three
constant-definition removals — remove readers before their constants to avoid an
intermediate state where a constant is undefined while still referenced (apply in the
order listed: steps 2-3 before 4-6).

### Details
- `_collect_field_changes()`'s "# RAG fields" section interleaves the removed blocks
  with `FIELD_EMBED_URL`/`FIELD_WEB_SEARCH_URL`/`FIELD_USE_REFINER` blocks that must
  remain — edit line-by-line rather than deleting the whole section.
- Confirm after editing: `rg -n "SEMANTIC_CACHE|semantic_cache"
  scripts/agent/services/config_reload.py` returns zero matches.
- Do not touch `_collect_field_changes()`'s docstring or its LLM/SSE-fields sections —
  confirmed unrelated.

## Compatibility considerations
- A hot-reload payload (`ConfigReloadRequest`) that still sets one of the three removed
  keys will now have that key silently ignored by both `_collect_field_changes()` and
  `_apply_rag_params()` — consistent with this Plan's Unknowns `UNK-01` ("default to
  leaving hot-reload silent... unless a maintainer states otherwise"), not rejected
  like the full-restart config-loading path (`REQ-002`/`REQ-004`).

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document (hot-reload's silent-ignore behavior for removed keys does not depend on
  `RagConfigImpl`/`RAGConfig`/`RagPipelineConfig` having removed the fields, since this
  path never constructs those types with the collected `changes` dict directly — it
  only ignores unknown-to-this-file keys, per Plan Design's `ConfigLoader`
  "unknown keys are silently ignored" finding).

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/shared/test_config_hot_reload.py -v`
  (both updated by their own procedure documents) — pass.
- `rg -n "SEMANTIC_CACHE|semantic_cache" scripts/agent/services/config_reload.py` —
  zero matches.

## Completion criteria
- No `FIELD_*` constant or `if` block referencing any of the three removed keys
  remains in either `_collect_field_changes()` or `_apply_rag_params()` (Plan `AC-6`).
- `tests/agent/services/test_config_reload.py` and `tests/shared/test_config_hot_reload.py`
  pass.

## Out of scope
- Every other `FIELD_*` constant and `if` block in this file.
- Investigating whether `_apply_rag_params()` and `_collect_field_changes()`'s RAG
  sections are otherwise duplicative (pre-existing structural question, unrelated to
  this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure documents for the two dependent test files |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (remove the three keys' handling from the reload path)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/agent/services/config_reload.py
