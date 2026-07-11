# Implementation: scripts/shared/config_validator.py — flat/nested shape normalization + max_size validation

## Goal

Make `RagConfigValidator.validate()` actually validate the flat config shape that the MCP
RAG service (`scripts/mcp_servers/rag_pipeline/service.py`) passes today — currently a
silent no-op for that path because `cfg.get("rag", {})` always returns `{}` for a flat
dict. Also add `semantic_cache_max_size` validation (reject negative values as an error;
`0` is accepted, no warning, per Design).

## Scope

**In:**
- `scripts/shared/config_validator.py::RagConfigValidator.validate()` — normalize input to
  accept both nested `{"rag": {...}}` (agent.toml / `ConfigLoader().load_all()` shape) and
  flat `{...}` (MCP `module_cfg` shape) before running any check
- Add a `semantic_cache_max_size` check: negative values append to `errors` (not
  `warnings` — the value is unusable, not merely suboptimal)

**Out:**
- No change to `validate()`'s public signature: `dict[str, Any] -> ConfigValidationResult`
- No change to the existing `embedding_dim`/`vec_dim` check's logic (only its input-shape
  resolution changes, via the new normalization line)
- No change to the existing `use_rrf` / `semantic_cache_threshold` checks' logic
- No change to `ConfigValidationResult` itself

## Assumptions

1. Current `validate()` (lines 19-43) does `rag = cfg.get("rag", {})` unconditionally —
   confirmed by direct read. `scripts/rag/pipeline.py` calls
   `validator.validate(_resolved_cfg)` where `_resolved_cfg` is either the MCP service's
   flat `module_cfg` or a nested dict from `ConfigLoader().load_all()`. For the flat shape,
   `cfg.get("rag", {})` always returns `{}`, so every check silently no-ops today — this is
   the exact bug being fixed.
2. Normalization rule: `rag = cfg["rag"] if "rag" in cfg else cfg`. A flat dict (MCP
   `module_cfg`) never nests its keys under a `"rag"` key by construction, so this
   condition correctly distinguishes the two shapes. This is a strict superset of the old
   `cfg.get("rag", {})` behavior for every already-tested nested-shape input (when `"rag"`
   is present, behavior is identical to before; when absent, the whole flat dict is now
   used instead of `{}`).
3. `max_size == 0` deliberately produces neither an error nor a warning (plan Assumption 2:
   it is a valid, if degenerate, "capacity zero" configuration — the actual cache-disable
   switch is the separate `use_semantic_cache` boolean, not this value).
4. Negative `max_size` is always invalid (plan Assumption 3) — append to `errors`, which
   makes `ConfigValidationResult.ok` become `False` (per the existing `ok` property:
   `len(self.errors) == 0`).

## Implementation

### Target file

`scripts/shared/config_validator.py`

### Procedure

1. Replace the line `rag = cfg.get("rag", {})` with the normalization:
   `rag = cfg["rag"] if "rag" in cfg else cfg`.
2. Leave the `embedding_dim`/`vec_dim` check, the `use_rrf` check, and the
   `semantic_cache_threshold` check unchanged — they continue to read from the now-
   correctly-resolved `rag` dict.
3. Add a new check after the existing `semantic_cache_threshold` check:
   - `max_size = rag.get("semantic_cache_max_size", 100)`
   - `if max_size < 0: errors.append(f"semantic_cache_max_size={max_size} is negative; must be >= 0")`
4. No change to the `return ConfigValidationResult(errors=errors, warnings=warnings)` line.

### Method

Single-line replacement (the `rag = ...` normalization) plus a 3-line addition (the new
`max_size` check block). No new imports, no signature changes.

### Details

- Default value `100` for `rag.get("semantic_cache_max_size", 100)` matches
  `SemanticCache.__init__`'s own default (`max_size: int = 100`), so an absent key is
  treated as "using the class default," not flagged.
- Comment inline (per `rules/coding.md` — English only) noting why the normalization
  handles both shapes, e.g.: `# Normalize: nested {"rag": {...}} (agent.toml) and flat
  {...} (MCP module_cfg) both supported.`
- Do not add a comment implying `max_size == 0` is an error — it explicitly is not one, per
  Assumption 3 above; a code comment should state this positively to avoid future
  confusion (e.g. `# max_size == 0 is a valid degenerate "capacity zero" config; only
  negative values are rejected.`).

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/config_validator.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/config_validator.py` | No new errors |
| Tests | `uv run pytest tests/test_config_validator.py -v` | All 9 pre-existing nested-shape tests still pass unmodified; new flat-shape and max_size tests pass (see companion test-file implementation doc) |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_mcp_rag_pipeline.py -q` | No new failures — confirms `validator.validate(_resolved_cfg)` call sites in `pipeline.py` are unaffected |
