## Goal
Stop reading `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size`
in `_build_rag_config()` and stop passing them to the `RAGConfig` constructor, and add a
`RagConfigValidator().validate()` call so a removed key raises before construction
(`scripts/agent/config_builders.py`) (`REQ-002`).

## Scope
- **In-Scope**: remove the three key-reads (`use_semantic_cache = _get_bool_or_default(cfg,
  "use_semantic_cache", False)`, line 254; `semantic_cache_threshold =
  _get_float_or_default(cfg, "semantic_cache_threshold", 0.92)`, lines 255-257;
  `semantic_cache_max_size = _get_int_or_default(cfg, "semantic_cache_max_size", 100)`,
  line 258) and the three corresponding `RAGConfig(...)` constructor arguments (lines
  267-269) from `_build_rag_config()`; add a new
  `from shared.config_validator import RagConfigValidator` import; add a
  `RagConfigValidator().validate(cfg)` call at the start of `_build_rag_config()`,
  raising `ValueError` on `not validation_result.ok`, matching
  `scripts/rag/pipeline.py`'s existing pattern (Reference Files evidence).
- **Out-of-Scope**: `embed_url`/`use_refiner`/`refiner_max_tokens`/`refiner_timeout`/
  `refiner_max_chars_per_chunk` reads and constructor args in the same function —
  confirmed unrelated; every other `_build_*_config()` function in this file
  (`_build_tool_config`, `_build_llm_config`, `_build_memory_config`, etc.) — confirmed
  unrelated by their own field lists.

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`03`: this change must not
  be applied until `semcacherm` has landed.
- `scripts/shared/config_validator.py`'s new removed-key rejection check (procedure
  document for that file, `REQ-003`) is applied in the same implementation pass or
  before this document's validator call is wired in — otherwise `validate(cfg)` would
  not yet reject a removed key, silently defeating this document's `AC-7` purpose.
- `RagConfigValidator().validate()` accepts the same raw `cfg: dict[str, Any]` shape
  this function already receives — confirmed by `scripts/rag/pipeline.py`'s existing
  call passing its own `_raw_cfg` dict directly (Reference Files).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6/§9, narrow bullets only)
- Reuse `scripts/rag/pipeline.py`'s exact validation-and-raise pattern (log warnings,
  log errors, raise `ValueError` with the error list on `not ok`) rather than inventing
  a new error-handling convention for the Agent path — per this Plan's Design section,
  this is "the intended single point of enforcement."
- Call `RagConfigValidator().validate(cfg)` before the field-reads it would otherwise
  race with removal of — placing the validation call first means a removed key is
  rejected before any `_get_*_or_default()` call would otherwise (today) silently
  substitute a default and proceed.
- Raise only on `validation_result.errors` (not `.warnings`) — matching
  `scripts/rag/pipeline.py`'s existing pattern exactly, per this Plan's Risks
  mitigation ("raises only on `validation_result.errors` ... so no new failure mode is
  introduced for pre-existing warnings").

## Alternatives considered
- Adding the removed-key check directly inside `_build_rag_config()` instead of
  reusing `RagConfigValidator` — rejected: the originating issue and this Plan
  explicitly centralize rejection in `RagConfigValidator` (`REQ-003`) as "the intended
  single point of enforcement" (Plan Assumptions) so both the Agent and RAG MCP paths
  share one rejection rule, rather than duplicating it.

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding.
2. Add `from shared.config_validator import RagConfigValidator` to this file's import
   block (alongside the existing `from shared.config_errors import ConfigLoadError`
   and `from shared.config_loader import ConfigLoader` imports).
3. At the start of `_build_rag_config(cfg)`, before `embed_url = ...` (line 253), add:
   ```
   validator = RagConfigValidator()
   validation_result = validator.validate(cfg)
   for warning in validation_result.warnings:
       logger.warning("rag config warning: %s", warning)
   for error in validation_result.errors:
       logger.error("rag config error: %s", error)
   if not validation_result.ok:
       raise ValueError(f"RAG config validation failed: {validation_result.errors}")
   ```
4. Remove `use_semantic_cache = _get_bool_or_default(cfg, "use_semantic_cache", False)`
   (line 254).
5. Remove the `semantic_cache_threshold = _get_float_or_default(cfg,
   "semantic_cache_threshold", 0.92)` statement (lines 255-257).
6. Remove `semantic_cache_max_size = _get_int_or_default(cfg,
   "semantic_cache_max_size", 100)` (line 258).
7. Remove the three corresponding keyword arguments
   (`use_semantic_cache=use_semantic_cache`, `semantic_cache_threshold=semantic_cache_threshold`,
   `semantic_cache_max_size=semantic_cache_max_size`) from the `RAGConfig(...)`
   constructor call (lines 267-269).

### Method
Direct `Edit`: one insertion (validator call block) and two removals (key-reads,
constructor args) within the same function body.

### Details
- Confirm `logger` (module-level, line 47: `logger = logging.getLogger(__name__)`)
  is already available in this file — no new logger declaration is needed.
- After editing, `_build_rag_config()`'s remaining body must read, in order: validator
  call/raise block → `embed_url` read → `use_refiner`/`refiner_*` reads →
  `RAGConfig(...)` construction with only the surviving four keyword arguments
  (`embed_url`, `use_refiner`, `refiner_max_tokens`, `refiner_timeout`,
  `refiner_max_chars_per_chunk` — five, not four; re-count against the actual
  remaining field list before finalizing).
- Confirm after editing: `rg -n
  "use_semantic_cache|semantic_cache_threshold|semantic_cache_max_size"
  scripts/agent/config_builders.py` returns zero matches.

## Compatibility considerations
- `build_agent_config()` (this function's caller) now raises `ValueError` for any
  invalid RAG config, including a removed cache key — previously, an unknown key was
  silently ignored (per this Plan's Design section finding that `ConfigLoader`
  performs no per-key validation). This is the intended behavior change (`AC-7`).
- `config/agent.toml` is confirmed (Plan Reference Files) not to currently set any of
  the three removed keys — re-verify this immediately before wiring the call in, since
  the file could have changed since this Plan's authoring (Plan Risks).

## Security considerations
N/A: no security-sensitive code path is touched; this only adds fail-fast validation
of configuration input at a trust boundary (config-file loading), consistent with
`skills/DESIGN.md`'s "validate only at system boundaries" principle.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  `scripts/agent/config_dataclasses.py` (procedure document `03`, the `RAGConfig`
  constructor this function calls) and `scripts/shared/config_validator.py`'s new
  rejection check (that file's own procedure document) to avoid a partially-applied
  validation chain.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v` (updated by its own procedure
  document) — passes; confirms `_build_rag_config()` no longer reads or forwards the
  three keys and now validates via `RagConfigValidator`.
- `rg -n "use_semantic_cache|semantic_cache_threshold|semantic_cache_max_size"
  scripts/agent/config_builders.py` — zero matches.
- Manually confirm (per Plan Risks) `config/agent.toml` does not set any of the three
  keys before this change is deployed, to avoid rejecting a currently-working config.

## Completion criteria
- `_build_rag_config()` no longer reads, creates, or forwards any of the three removed
  keys (Plan `AC-3`).
- Supplying a removed key to the Agent configuration path raises with the
  `REQ-003` migration message (Plan `AC-7`), proven by the new regression test
  (`tests/agent/test_removed_config_keys_rejected.py`, its own procedure document).

## Out of scope
- `scripts/shared/config_validator.py`'s new rejection check itself (that file's own
  procedure document).
- `scripts/agent/config_dataclasses.py`'s `RAGConfig` (procedure document `03`).
- Every other `_build_*_config()` function in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/agent/test_config_builders.py` |
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
- **Requirement ID**: `REQ-002` (stop reading the three keys and forwarding them; add validator call)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/agent/config_builders.py
