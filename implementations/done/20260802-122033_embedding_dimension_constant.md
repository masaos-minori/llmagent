# Goal

Replace hardcoded `384` embedding dimension constant with a code-level invariant `QWEN3_EMBEDDING_DIMS = 1024`, eliminating TOML-driven configuration drift between DB layer and agent memory path.

# Scope

- Define `QWEN3_EMBEDDING_DIMS = 1024` as module-level constant in `scripts/db/store_protocols.py`
- Update `get_embedding_dims()` to return this constant unconditionally
- Remove `DbConfig.embedding_dims` field and its plumbing
- Remove `MemoryConfig.memory_embed_dim` field and its plumbing
- Remove `_check_embedding_dimensions()` from startup
- Remove `embedding_dims` / `memory_embed_dim` keys from TOML configs
- Clean up remaining references to 384 in affected modules

# Assumptions

- No runtime migration of existing vector data is required; operators will recreate databases after deployment
- The Qwen3 embedding model always produces 1024-dimensional vectors; no future model change is expected
- All consumers of `get_embedding_dims()` already work via `build_db_config()` or direct constant reference

# Design decisions

- Constant lives in DB layer (`store_protocols.py`) because that is the canonical source for schema creation and ingester validation
- Agent memory path imports `get_embedding_dims()` from DB layer instead of reading from `MemoryConfig`; eliminates duplicate config key
- No backward compatibility shim needed — TOML keys are removed atomically in same change set

# Alternatives considered

- Keep `embedding_dims` in `DbConfig` but make it read-only (no TOML override): adds unnecessary indirection when value is fixed
- Define constant in agent layer instead of DB layer: breaks single-source-of-truth principle since schema DDL generation is in DB layer
- Add migration script for old vector data: not justified; operators can recreate databases

# Implementation

## Target file

### scripts/db/store_protocols.py

**Procedure:**

1. Add module-level constant below the docstring block:
   ```python
   QWEN3_EMBEDDING_DIMS = 1024
   ```

2. Replace `get_embedding_dims()` body:
   - Before:
     ```python
     def get_embedding_dims() -> int:
         """Return embedding dimensions from DbConfig; raises on config error."""
         dims: int = build_db_config().embedding_dims
         return dims
     ```
   - After:
     ```python
     def get_embedding_dims() -> int:
         """Return the Qwen3 embedding dimension count (1024)."""
         return QWEN3_EMBEDDING_DIMS
     ```

3. Update module docstring line 13:
   - Before: `get_embedding_dims()     — return configured dimension count (default 384)`
   - After: `get_embedding_dims()     — return Qwen3 embedding dimension count (1024)`

4. Verify `get_embedding_bytes()` derives correctly:
   ```python
   def get_embedding_bytes() -> int:
       """Return expected float32 BLOB size in bytes."""
       return get_embedding_dims() * 4  # 1024 * 4 = 4096
   ```
   No change needed — behavior unchanged.

**Method:** Direct edit — add constant, replace function body, update docstring.

**Details:**
- Line 13: update docstring text
- After line 18 (end of module docstring): insert `QWEN3_EMBEDDING_DIMS = 1024`
- Lines 27-30: replace entire function body

---

### scripts/db/config.py

**Procedure:**

1. Remove `embedding_dims: int = 384` from `DbConfig` dataclass fields (line 32)

2. Remove `__post_init__` validation for `embedding_dims` (lines 46-47):
   ```python
   if self.embedding_dims < 1:
       raise ValueError(f"embedding_dims must be >= 1, got {self.embedding_dims}")
   ```

3. Remove `embedding_dims=int(cfg.get("embedding_dims", 384))` from `build_db_config()` (line 82)

**Method:** Delete lines — remove field, validation, and builder argument.

**Details:**
- Line 32: delete `    embedding_dims: int = 384`
- Lines 46-47: delete the two-line validation block
- Line 82: delete `, embedding_dims=int(cfg.get("embedding_dims", 384))`

---

### scripts/agent/startup.py

**Procedure:**

1. Delete entire `_check_embedding_dimensions()` method (lines 271-287):
   ```python
   def _check_embedding_dimensions(self) -> None:
       """Verify embedding dimension consistency between memory config and db config."""
       from db.config import build_db_config  # noqa: PLC0415 — lazy

       ctx = self._ctx
       memory_dim = ctx.cfg.memory.memory_embed_dim
       db_dim = build_db_config().embedding_dims
       if memory_dim != db_dim:
           logger.error(...)
           raise RuntimeError(...)
       logger.info("Embedding dimensions consistent: %d", memory_dim)
   ```

2. Remove its call site at line 310:
   ```python
   self._check_embedding_dimensions()
   ```

**Method:** Delete method definition and call site.

**Details:**
- Lines 271-287: delete entire method
- Line 310: delete `self._check_embedding_dimensions()` call

---

### scripts/agent/config_dataclasses.py

**Procedure:**

1. Remove `memory_embed_dim: int = 384` field from `MemoryConfig` dataclass (line 221)

**Method:** Delete field line.

**Details:**
- Line 221: delete `    memory_embed_dim: int = 384`

---

### scripts/agent/config_builders.py

**Procedure:**

1. Remove `memory_embed_dim` parsing logic (lines 339-344):
   ```python
   _mem_dim = _get_int(cfg, "memory_embed_dim")
   memory_embed_dim = _mem_dim if _mem_dim is not None else 384
   if memory_embed_dim < 1:
       raise ConfigReloadValidationError(
           f"memory_embed_dim must be >= 1, got {memory_embed_dim}"
       )
   ```

2. Remove `memory_embed_dim=memory_embed_dim` from `MemoryConfig()` constructor call (line 376)

**Method:** Delete parsing block and constructor argument.

**Details:**
- Lines 339-344: delete five-line parsing/validation block
- Line 376: delete `, memory_embed_dim=memory_embed_dim`

---

### scripts/agent/factory.py

**SUPERSeded by `20260802-122255_embedding_request_normalization.md`.**

This file removes `embed_dim` field entirely from `EmbeddingClientConfig`, so replacing `ctx.cfg.memory.memory_embed_dim` with `get_embedding_dims()` is unnecessary. The `embed_dim` argument must be deleted entirely.

The `MemoryStore(embed_dim=...)` at Line 371 is also out of scope for this procedure (see `Out of scope` section below).

---

### config/agent.toml

**Procedure:**

1. Remove `embedding_dims = 384` (line 17)
2. Remove `memory_embed_dim = 384` (line 88)

**Method:** Delete TOML key-value pairs.

**Details:**
- Line 17: delete `embedding_dims = 384`
- Line 88: delete `memory_embed_dim = 384`

---

### config/ingester.toml

**Handled by `20260802-122255_embedding_request_normalization.md` (Step 3).**

Do NOT remove `embedding_dims = 384` here — it is removed in the other file to avoid duplicate deletion.

---

### Various modules (Step 6: docstrings/comments)

**Procedure:**

1. Search for remaining `"384"` or "configured dimension" references in affected modules
2. Update any found references to reflect new constant-based approach

**Affected files to check:**
- `scripts/db/store_protocols.py` — already handled in Step 1
- `scripts/db/config.py` — already handled in Step 2
- `scripts/rag/ingestion/ingester.py` — verify no remaining `384` near embedding paths
- `scripts/rag/llm_client.py` — verify no remaining `384` near embedding paths
- `scripts/agent/memory/embedding_client.py` — verify no remaining `384` near embedding paths
- `tests/test_embedding_client.py` — verify test assertions use 1024

**Method:** grep + targeted edits.

**Details:**
- Run `grep -rn "384" scripts/db/ scripts/rag/ scripts/agent/memory/ tests/test_embedding_client.py` before editing
- Update only references that describe the embedding dimension value

---

### Database recreation note (Step 7)

**Procedure:**

1. Document that operators must recreate databases after deployment
2. This is a documentation note, not code change

**Out of scope for this implementation procedure.**

# Compatibility considerations

- **Breaking change**: Existing `rag.sqlite` / `session.sqlite` databases created with 384-dim vectors cannot be migrated. Operators must recreate them.
- **TOML removal**: Any external tooling that reads `config/agent.toml` for `embedding_dims` or `memory_embed_dim` will break. These keys no longer exist.
- **No rollback path**: Since dimension is now a compile-time invariant, there is no way to revert to 384 without reverting the entire change set.

# Security considerations

N/A — no security impact. Dimension change does not affect authentication, authorization, or data integrity.

# Rollback considerations

- Revert all changes in one commit (atomic rollback)
- If partial rollback needed: restore `embedding_dims` / `memory_embed_dim` TOML keys and re-add `DbConfig.embedding_dims` field
- Database recreation required after rollback — old 1024-dim vectors are incompatible with 384-dim schema

# Validation plan

1. **Unit test — `get_embedding_dims()` returns 1024**: Assert unconditionally regardless of TOML content
2. **Unit test — Schema DDL contains `float[1024]`**: Extend existing `create_schema` test to assert both `chunks_vec` and `memories_vec` use `float[1024]`
3. **Unit test — `DbConfig` has no `embedding_dims`**: Assert `hasattr(DbConfig(...), "embedding_dims")` is `False`
4. **Unit test — Startup succeeds**: New test confirming agent startup does not raise `AttributeError` after `DbConfig.embedding_dims` removal
5. **Lint/typecheck**: `ruff`, `mypy` pass on all modified files
6. **Full test suite**: `pytest` passes

# Out of scope

- Migration script for existing vector data
- Changes to `config/rag_pipeline_mcp_server.toml` (no `embedding_dims` key exists there)
- Documentation updates outside source files (e.g., ops runbooks)
- `scripts/agent/factory.py` — `embed_dim` argument removal is handled by `20260802-122255_embedding_request_normalization.md`; `MemoryStore(embed_dim=...)` is out of scope per requirement
- `config/ingester.toml` — `embedding_dims = 384` removal is handled by `20260802-122255_embedding_request_normalization.md`

# Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-070234_require.md
- Source plan: plans/20260802-102150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260802-122033
- Related target files: scripts/db/store_protocols.py, scripts/db/config.py, scripts/agent/startup.py, scripts/agent/config_dataclasses.py, scripts/agent/config_builders.py, scripts/agent/factory.py (superseded), config/agent.toml, config/ingester.toml (partial)
- Cross-reference: `20260802-122255_embedding_request_normalization.md` handles `factory.py` embed_dim removal and `config/ingester.toml` embedding_dims removal
