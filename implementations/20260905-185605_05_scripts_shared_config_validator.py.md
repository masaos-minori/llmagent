## Goal
Remove `_check_semantic_cache_threshold()`/`_check_semantic_cache_max_size()` from
`RagConfigValidator`, and add a new check that rejects any of the three removed keys
(`use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size`) with a
clear migration-error message (`scripts/shared/config_validator.py`) (`REQ-003`).

## Scope
- **In-Scope**: remove `_check_semantic_cache_threshold()` (lines 59-64) and
  `_check_semantic_cache_max_size()` (lines 67-72) in their entirety; remove their two
  call sites in `validate()` (lines 36-41: the `threshold_warning`/`max_size_error`
  blocks); add a new `_check_removed_semantic_cache_keys()` static method that returns
  an error message naming any of the three removed keys found in the `rag` section; add
  its call to `validate()`, appending to `errors` (not `warnings`, since a removed key
  is a hard configuration error per `AC-7`, not an advisory).
- **Out-of-Scope**: `_check_use_rrf()` and its call in `validate()` — confirmed
  unrelated by reading the full class; `_extract_rag_section()` — reused unchanged by
  the new check, per Design decisions; `ConfigValidationResult` — unchanged, already
  supports the `errors`/`warnings` split this document needs.

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`04`: this change must not
  be applied until `semcacherm` has landed — although this file's own change is
  low-risk in isolation (it only tightens validation, does not remove a field
  `RagPipeline` reads), landing it before `semcacherm` would cause
  `scripts/rag/pipeline.py`'s existing `RagConfigValidator().validate(_raw_cfg)` call
  (Reference Files) to start rejecting `semantic_cache_max_size`/
  `semantic_cache_threshold` values that `RagConfigImpl`/`SemanticCache` still expect
  pre-`semcacherm` — sequence this after `semcacherm` regardless.
- `RagPipelineConfig.load()`'s new `RagConfigValidator().validate()` call (that file's
  own procedure document, `REQ-004`) and `_build_rag_config()`'s new call (procedure
  document `04`, `REQ-002`) both depend on this document's new check existing to
  produce the migration-error behavior `AC-7` requires.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Add one new check function (`_check_removed_semantic_cache_keys`) covering all three
  removed keys, rather than three separate per-key checks — the three keys form one
  semantic unit (the removed cache feature), and a single combined error message naming
  every removed key present is more useful to an operator migrating a config file than
  three separate error entries for the same underlying cause.
- **Migration message wording** (resolves Plan Unknowns `UNK-02`, which stated "Resolve
  at implementation time"): `"Configuration key(s) {keys} are no longer supported —
  the semantic cache feature was removed (see issues/done/20260902-150339_semcacherm_...
  and issues/20260902-150341_semcachedocs_...); remove {keys} from your configuration."`
  — concise, names the removed key(s), and points to the originating issues per the
  Plan's own Design guidance ("pointing to the semcacherm/semcachedocs issues (or their
  resulting doc) is sufficient").
- Follow the existing `str | None`-returning static-method convention for consistency
  with `_check_use_rrf()`/the two removed checks, rather than introducing a
  list-returning convention that would require restructuring `validate()`'s existing
  append pattern.

## Alternatives considered
- Returning a `list[str]` (one entry per removed key found) instead of one combined
  `str | None` — rejected: none of this class's three existing check methods return a
  list; introducing a second return-type convention in the same small class adds
  inconsistency for no clear benefit, since `validate()`'s `errors: list[str]` already
  accommodates either shape via `.append()` vs. `.extend()`.

## Implementation
### Target file
`scripts/shared/config_validator.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. Remove the `threshold_warning = self._check_semantic_cache_threshold(rag)` /
   `if threshold_warning is not None: warnings.append(threshold_warning)` block (lines
   36-38) from `validate()`.
3. Remove the `max_size_error = self._check_semantic_cache_max_size(rag)` /
   `if max_size_error is not None: errors.append(max_size_error)` block (lines 40-42)
   from `validate()`.
4. Add a new block in `validate()`, in the same position (after the `use_rrf` check,
   before `return ConfigValidationResult(...)`):
   ```
   removed_key_error = self._check_removed_semantic_cache_keys(rag)
   if removed_key_error is not None:
       errors.append(removed_key_error)
   ```
5. Remove `_check_semantic_cache_threshold()` (lines 59-64) in its entirety.
6. Remove `_check_semantic_cache_max_size()` (lines 67-72) in its entirety.
7. Add a new static method `_check_removed_semantic_cache_keys(rag: Mapping[str, Any])
   -> str | None` (placed where the two removed methods were, preserving file
   structure) that checks `rag` for `"use_semantic_cache"`, `"semantic_cache_threshold"`,
   and `"semantic_cache_max_size"` (via `in rag`, not `.get()` with a default, since
   presence — not value — is what must be rejected), collects the names of any keys
   present, and returns the migration message (per Design decisions) naming them if
   one or more are present, else `None`.

### Method
Direct `Edit`: two method removals, one method addition, and `validate()`'s call-site
block replaced (two removed blocks → one new block).

### Details
- Use `key in rag` (membership test against the `Mapping`), not `rag.get(key)`, to
  detect presence — a key explicitly set to a falsy value (e.g.
  `use_semantic_cache = false`) must still be rejected, since the key's mere presence,
  not its value, indicates a config file that has not yet migrated.
- Confirm after editing: `rg -n
  "_check_semantic_cache_threshold|_check_semantic_cache_max_size"
  scripts/shared/config_validator.py` returns zero matches; `rg -n
  "_check_removed_semantic_cache_keys" scripts/shared/config_validator.py` returns
  exactly two matches (definition + call site).
- `_extract_rag_section()` is called once per `validate()` invocation (line 28) and
  its result (`rag`) is already passed to every check method, including the new one —
  no change needed to `_extract_rag_section()` itself.

## Compatibility considerations
- `validate()`'s return type (`ConfigValidationResult`) is unchanged — callers
  (`scripts/rag/pipeline.py`, and the two new callers added by procedure document `04`
  and `RagPipelineConfig.load()`'s own procedure document) need no signature-level
  change, only behavioral awareness that a removed key now produces an error, not a
  warning or silence.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  procedure document `04` (`scripts/agent/config_builders.py`) and
  `RagPipelineConfig.load()`'s own procedure document, since both add new calls to this
  class expecting the new check to exist.

## Validation plan
- `uv run pytest tests/shared/test_config_validator.py -v` (updated by its own
  procedure document) — passes; confirms the two removed checks are gone and the new
  rejection check fires for each of the three keys individually and in combination.
- `rg -n "_check_semantic_cache_threshold|_check_semantic_cache_max_size"
  scripts/shared/config_validator.py` — zero matches.

## Completion criteria
- `RagConfigValidator` no longer has `_check_semantic_cache_threshold()`/
  `_check_semantic_cache_max_size()` (Plan `AC-5`).
- `RagConfigValidator().validate()` returns an error containing a migration message
  when any of the three removed keys is present (Plan `AC-7`).
- `tests/shared/test_config_validator.py` passes.

## Out of scope
- `_check_use_rrf()` and its call.
- `scripts/rag/pipeline.py`'s existing call to `RagConfigValidator().validate()` — no
  change needed there (Reference Files: the new check propagates through the existing
  call automatically).
- Wiring this validator into new call sites (`scripts/agent/config_builders.py`,
  procedure document `04`; `RagPipelineConfig.load()`, its own procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/shared/test_config_validator.py` |
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
- **Requirement ID**: `REQ-003` (remove existing cache checks; add new removed-key rejection check)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/shared/config_validator.py
