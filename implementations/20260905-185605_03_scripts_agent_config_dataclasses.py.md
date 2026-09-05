## Goal
Remove `use_semantic_cache`, `semantic_cache_threshold`, and `semantic_cache_max_size`
from `RAGConfig`, and remove `AgentConfig._validate_semantic_cache_url()` and its call
in `_validate_cross_field()`, in `scripts/agent/config_dataclasses.py` (`REQ-001`).

## Scope
- **In-Scope**: remove the three field declarations from `RAGConfig` (lines 154-156:
  `use_semantic_cache: bool = False`, `semantic_cache_threshold: float = 0.92`,
  `semantic_cache_max_size: int = 100`); remove `_validate_semantic_cache_url()`'s
  call in `_validate_cross_field()` (line 454); remove
  `_validate_semantic_cache_url()`'s definition in its entirety (lines 458-463);
  correct the stale docstring example on `AgentConfig` (line 434: "Access fields via
  nested paths: `cfg.llm.llm_url`, `cfg.rag.use_semantic_cache`, etc." — replace the
  removed-field example with a still-valid one, e.g. `cfg.rag.embed_url`).
- **Out-of-Scope**: `_validate_memory_jsonl_dir()`/`_validate_memory_embed_url()` and
  their calls in `_validate_cross_field()` — confirmed unrelated by reading the full
  method; every other field in `RAGConfig` (`embed_url`, `use_refiner`,
  `refiner_max_tokens`, etc.) — confirmed unrelated.

## Assumptions
- Same hard ordering dependency as procedure documents `01`/`02`: this change must not
  be applied until `semcacherm` has landed.
- `_validate_semantic_cache_url()`'s sole caller is `_validate_cross_field()` (line
  454) — confirmed by `grep -n "_validate_semantic_cache_url"
  scripts/agent/config_dataclasses.py`, matching only the definition and this one call
  site.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove the validator method and its call together — `_validate_semantic_cache_url()`
  exists solely to enforce a cross-field rule (`use_semantic_cache=True requires
  embed_url`) that becomes vacuous once `use_semantic_cache` no longer exists; leaving
  the call without the field it reads would raise `AttributeError` at
  `AgentConfig.__post_init__` time.
- Correct the docstring example (an adversarial-verification finding not itemized in
  the Plan's Repository Evidence for this row) rather than leaving it referencing a
  field this document removes two lines below it — per Step 3a Adversarial
  Verification, a stale in-file cross-reference discovered while editing the named
  target is corrected in the same document, not deferred.

## Alternatives considered
- Leaving `_validate_semantic_cache_url()` as a no-op — rejected: a validator method
  with nothing to validate is dead code, inconsistent with the originating issue's
  explicit instruction to remove it.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. Remove `use_semantic_cache: bool = False` (line 154).
3. Remove `semantic_cache_threshold: float = 0.92` (line 155).
4. Remove `semantic_cache_max_size: int = 100` (line 156).
5. In `AgentConfig`'s class docstring (line 434), replace
   `"...cfg.rag.use_semantic_cache, etc."` with a still-valid field reference (e.g.
   `"...cfg.rag.embed_url, etc."`).
6. Remove the `self._validate_semantic_cache_url()` call from `_validate_cross_field()`
   (line 454).
7. Remove the `_validate_semantic_cache_url()` method definition in its entirety
   (lines 458-463: signature, docstring, `if` check, and `raise ValueError(...)`).

### Method
Direct removal via `Edit` — no replacement validation logic is introduced; the
cross-field rule this method enforced no longer applies once its subject field is
gone.

### Details
- After step 6, `_validate_cross_field()` must retain its two other calls
  (`self._validate_memory_jsonl_dir()`, `self._validate_memory_embed_url()`) unchanged.
- Confirm after editing: `rg -n
  "use_semantic_cache|semantic_cache_threshold|semantic_cache_max_size|_validate_semantic_cache_url"
  scripts/agent/config_dataclasses.py` returns zero matches.

## Compatibility considerations
- `AgentConfig.__post_init__` no longer raises `ValueError` for the
  `use_semantic_cache=True, embed_url=""` combination — this is an intended behavior
  change, since the field being validated no longer exists.
- Any external caller constructing `RAGConfig(use_semantic_cache=..., ...)` will raise
  `TypeError: unexpected keyword argument`.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  `scripts/agent/config_builders.py` (procedure document `04`), the sole builder that
  constructs `RAGConfig`.

## Validation plan
- `uv run pytest tests/agent/test_config_dataclasses.py -v` (updated by its own
  procedure document) — passes; confirms `RAGConfig` no longer has the three fields
  and `_validate_semantic_cache_url()` is gone.
- `rg -n
  "use_semantic_cache|semantic_cache_threshold|semantic_cache_max_size|_validate_semantic_cache_url"
  scripts/agent/config_dataclasses.py` — zero matches.

## Completion criteria
- `RAGConfig` no longer declares any of the three removed fields; `AgentConfig` no
  longer has `_validate_semantic_cache_url()` or calls it (Plan `AC-1`, `AC-5`).
- `tests/agent/test_config_dataclasses.py` passes.

## Out of scope
- `scripts/agent/config_builders.py`'s `_build_rag_config()` (procedure document `04`).
- `_validate_memory_jsonl_dir()`/`_validate_memory_embed_url()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/agent/test_config_dataclasses.py` |
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
- **Requirement ID**: `REQ-001` (remove the three fields from `RAGConfig`; remove `_validate_semantic_cache_url()` and its call)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/agent/config_dataclasses.py
