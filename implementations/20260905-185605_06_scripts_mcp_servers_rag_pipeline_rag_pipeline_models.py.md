## Goal
Remove the three fields from `RagPipelineConfig`, stop reading them in `from_dict()`,
stop forwarding them in `build_rag_cfg_adapter()`, and call
`RagConfigValidator().validate()` from `RagPipelineConfig.load()` so `REQ-003`'s
rejection applies to the RAG MCP loading path
(`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`) (`REQ-004`).

## Scope
- **In-Scope**: remove the three field declarations from `RagPipelineConfig` (lines
  59-61: `semantic_cache_max_size: int = 100`, `semantic_cache_threshold: float =
  0.92`, `use_semantic_cache: bool = False`); remove the three corresponding reads in
  `from_dict()` (lines 90-92); remove the three corresponding forwards in
  `build_rag_cfg_adapter()`'s `SimpleNamespace(...)` construction (lines 129-131); add
  a new `from shared.config_validator import RagConfigValidator` import; add a
  `RagConfigValidator().validate()` call in `load()` (lines 100-102), raising before
  `from_dict()` is reached on a validation failure.
- **Out-of-Scope**: every other field in `RagPipelineConfig`/`from_dict()`/
  `build_rag_cfg_adapter()` (`llm_url`, `embed_url`, `use_mqe`, `use_rrf`,
  `use_refiner`, etc.) — confirmed unrelated by reading the full file;
  `RagPipelineServiceError` — confirmed unrelated (a different exception class in the
  same file).

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`05`: this change must not
  be applied until `semcacherm` has landed and `scripts/shared/config_validator.py`'s
  new rejection check (procedure document `05`) exists.
- `ConfigLoader().load("rag_pipeline_mcp_server.toml")` (called inside `load()`)
  returns a flat `dict[str, Any]` matching the shape `RagConfigValidator.validate()`'s
  `_extract_rag_section()` already normalizes for the MCP "flat `{...}`" case (per that
  file's docstring, confirmed by procedure document `05`'s Design decisions).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Validate the raw dict inside `load()` (before `from_dict()` constructs the typed
  DTO), not inside `from_dict()` itself — `from_dict()` is a pure conversion function
  used elsewhere in tests with hand-built dicts that may intentionally omit unrelated
  fields (confirmed by this Plan's own test-file list, e.g.
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` constructing
  `RagPipelineConfig.from_dict()` directly); adding validation there would force every
  such test fixture through the validator too. `load()` is the single production entry
  point reading the actual TOML file, matching the Plan's intent ("call
  `RagConfigValidator().validate()` from `RagPipelineConfig.load()` so REQ-003's
  rejection applies to the RAG MCP loading path").

## Alternatives considered
- Adding the validation call inside `from_dict()` instead of `load()` — rejected per
  Design decisions above: it would validate every `from_dict()` call site, including
  test fixtures not meant to exercise this rejection path, contradicting this Plan's
  own Testing Expectations, which name specific new tests
  (`test_removed_config_keys_rejected.py`) as the place this behavior is proven, not
  every existing `from_dict()`-based test.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`

### Procedure
1. Re-verify `semcacherm` has landed and procedure document `05`'s
   `RagConfigValidator` change has landed (Assumptions) before proceeding.
2. Add `from shared.config_validator import RagConfigValidator` to this file's import
   block (alongside the existing `from shared.config_loader import ConfigLoader` and
   `from shared.types import RagConfig` imports).
3. Remove `semantic_cache_max_size: int = 100` (line 59).
4. Remove `semantic_cache_threshold: float = 0.92` (line 60).
5. Remove `use_semantic_cache: bool = False` (line 61).
6. Remove `semantic_cache_max_size=int(d.get("semantic_cache_max_size", 100))` (line
   90) from `from_dict()`.
7. Remove `semantic_cache_threshold=float(d.get("semantic_cache_threshold", 0.92))`
   (line 91) from `from_dict()`.
8. Remove `use_semantic_cache=bool(d.get("use_semantic_cache", False))` (line 92) from
   `from_dict()`.
9. Remove `semantic_cache_max_size=int(cfg.semantic_cache_max_size)` (line 129) from
   `build_rag_cfg_adapter()`.
10. Remove `semantic_cache_threshold=float(cfg.semantic_cache_threshold)` (line 130)
    from `build_rag_cfg_adapter()`.
11. Remove `use_semantic_cache=bool(cfg.use_semantic_cache)` (line 131) from
    `build_rag_cfg_adapter()`.
12. Update `load()` (lines 100-102) to:
    ```python
    @classmethod
    def load(cls) -> RagPipelineConfig:
        """Load from rag_pipeline_mcp_server.toml; raises on failure (fail-fast)."""
        raw_cfg = ConfigLoader().load("rag_pipeline_mcp_server.toml")
        validator = RagConfigValidator()
        validation_result = validator.validate(raw_cfg)
        for warning in validation_result.warnings:
            logger.warning("rag_pipeline_mcp_server config warning: %s", warning)
        for error in validation_result.errors:
            logger.error("rag_pipeline_mcp_server config error: %s", error)
        if not validation_result.ok:
            raise ValueError(
                f"RAG pipeline MCP config validation failed: {validation_result.errors}"
            )
        return cls.from_dict(raw_cfg)
    ```

### Method
Direct `Edit`: three field removals in the dataclass, three read removals in
`from_dict()`, three forward removals in `build_rag_cfg_adapter()`, and `load()`'s body
rewritten to validate before constructing.

### Details
- Confirm `logger` (module-level, line 19: `logger = logging.getLogger(__name__)`) is
  already available in this file for the new warning/error logs.
- After step 9-11, `build_rag_cfg_adapter()`'s `SimpleNamespace(...)` must still
  satisfy the `RagConfig` `Protocol` (procedure document `02` removes the same three
  attributes from that protocol) — confirm the adapter's remaining fields match the
  protocol's remaining fields one-for-one after both files' changes land.
- Confirm after editing: `rg -n "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` returns zero matches.

## Compatibility considerations
- `RagPipelineConfig.load()` now raises `ValueError` for a `config/rag_pipeline_mcp_server.toml`
  file that still sets one of the three removed keys — this is the intended
  fail-closed behavior (`AC-7`); procedure document `08` (`config/rag_pipeline_mcp_server.toml`)
  must remove the three keys from the deployed file in the same pass to avoid a
  startup failure.
- `build_rag_cfg_adapter()`'s output is consumed by `RagPipelineMCPService._build_module_cfg()`
  (that file's own procedure document, `REQ-005`) — confirm that document's removal of
  the same two keys from its own translation layer is consistent with this file's
  adapter no longer producing them.

## Security considerations
N/A: no security-sensitive code path is touched; this adds fail-fast validation at a
configuration-loading trust boundary.

## Rollback considerations
- Revert via `git checkout` on this single file; should be reverted together with
  `config/rag_pipeline_mcp_server.toml` (procedure document `08`) and
  `scripts/shared/config_validator.py` (procedure document `05`) to avoid a
  startup-time rejection of an unmigrated deployed config file.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py -v`
  (updated by its own procedure document) — passes; confirms `RagPipelineConfig`,
  `from_dict()`, and `build_rag_cfg_adapter()` no longer carry the three fields, and
  `load()` now validates.
- `rg -n "semantic_cache_max_size|semantic_cache_threshold|use_semantic_cache"
  scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` — zero matches.

## Completion criteria
- `RagPipelineConfig`/`from_dict()`/`build_rag_cfg_adapter()` no longer contain any of
  the three removed fields (Plan `AC-1`, `AC-3`).
- `RagPipelineConfig.load()` raises the `REQ-003` migration error for a removed key
  (Plan `AC-7`).
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` passes.

## Out of scope
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`'s `_build_module_cfg()`
  (that file's own procedure document).
- `config/rag_pipeline_mcp_server.toml` (procedure document `08`).
- `scripts/shared/config_validator.py`'s check logic itself (procedure document `05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands and procedure document `05` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation and this Plan's `scripts/shared/config_validator.py` change landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (remove the three fields from `RagPipelineConfig`; stop reading/forwarding them; call the validator from `load()`)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py
