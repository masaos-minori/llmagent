## Goal
Remove `semantic_cache_max_size`, `semantic_cache_threshold`, and `use_semantic_cache`
fields from `RagConfigImpl` (`scripts/rag/models_config.py`), since no runtime
implementation reads them once `semcacherm` (`issues/done/20260902-150339_...md`) has
removed `SemanticCache` (`REQ-001`).

## Scope
- **In-Scope**: remove the three field declarations from `RagConfigImpl`
  (`semantic_cache_max_size: int`, line 16; `semantic_cache_threshold: float`, line 17;
  `use_semantic_cache: bool`, line 34).
- **Out-of-Scope**: every other field in `RagConfigImpl` — confirmed unrelated by
  reading the full dataclass; `embed_url` (line, unaffected) — remains required by
  non-cache retrieval and Agent memory embedding.

## Assumptions
- **Hard ordering dependency**: this document's change must not be applied until
  `semcacherm`'s implementation has landed in the working tree — while
  `RagPipeline.__init__` still reads `self._cfg.semantic_cache_max_size`/
  `semantic_cache_threshold` to construct `SemanticCache` (removed by `semcacherm`
  procedure document `01`, `scripts/rag/pipeline.py`), removing these fields here would
  break `RagConfigImpl(**_raw_cfg)` construction with an unexpected-keyword-argument
  `TypeError`. Confirm `issues/done/20260902-150339_semcacherm_...md` exists (i.e.
  `semcacherm` is archived as completed) and `scripts/rag/pipeline.py` no longer
  references `self.semantic_cache`/`SemanticCache` before applying this change (per
  this Plan's own Risks: "the implementer must confirm ... before starting Phase 2").

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §5, narrow bullet only)
- Remove all three fields together in one edit — they are semantically one unit (the
  cache's tuning parameters and its on/off switch), and `RagConfigImpl` is a frozen
  dataclass where field order matters for any positional construction elsewhere
  (confirmed none exists — all construction found in this Plan's evidence uses keyword
  arguments).

## Alternatives considered
N/A: straightforward field removal from a dataclass with no remaining reader.

## Implementation
### Target file
`scripts/rag/models_config.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. Remove `semantic_cache_max_size: int` (line 16).
3. Remove `semantic_cache_threshold: float` (line 17).
4. Remove `use_semantic_cache: bool` (line 34).

### Method
Direct removal via `Edit` on a frozen `@dataclass` field list — no constructor logic
exists to update since `dataclass` auto-generates `__init__`.

### Details
- Confirm after editing: `rg -n
  "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/rag/models_config.py` returns zero matches.
- This dataclass is constructed via `RagConfigImpl(**_raw_cfg)` in
  `scripts/rag/pipeline.py` (per `semcacherm`'s Plan) — removing these fields here is
  safe only because that call site's `_raw_cfg` no longer supplies them once
  `RagConfigValidator`'s new rejection check (procedure document `05`) is wired in
  ahead of construction, per this Plan's Design section.

## Compatibility considerations
- Any external caller still passing one of these three keys to `RagConfigImpl(...)`
  will raise `TypeError: unexpected keyword argument` — this is the intended fail-fast
  behavior this Plan's `REQ-003`/`AC-7` establish at the validator layer before
  construction is reached.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with any
  other file in this Plan that stops populating these three keys (procedure documents
  covering `scripts/agent/config_builders.py`,
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`) to avoid a mismatched
  partial state.

## Validation plan
- `uv run pytest tests/rag/test_augment_integration.py tests/rag/test_augment_refiner.py
  tests/agent/test_rag_get_cfg.py -v` (updated by their own procedure documents) — pass.
- `rg -n "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/rag/models_config.py` — zero matches.
- `uv run mypy scripts/rag/` — no new type errors.

## Completion criteria
- `RagConfigImpl` no longer declares any of the three removed fields (Plan `AC-1`).
- Dependent test files pass against the modified dataclass.

## Out of scope
- `scripts/shared/types.py`'s `RagConfig` protocol (procedure document `02`).
- Any test file (covered by their own procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by dependent procedure documents |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation landing first (removes `RagPipeline`'s reads of these fields) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (remove the three fields from `RagConfigImpl`)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/rag/models_config.py
