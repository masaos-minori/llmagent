# Goal

Normalize all embedding HTTP request paths to send raw text with no prefix, removing E5-era `"query: "` and `"passage: "` conventions. Eliminate dimension-mismatch validation since dimension is now a fixed code constant. Fix active bug in `config/ingester.toml` where `embed_url` double-appends `/embedding`.

# Scope

- Remove `"passage: "` prefix from `RagIngester._get_embedding()` payload
- Remove `"query: "` prefix from `rag.llm_client.get_embedding()` payload
- Remove `query_prefix` field from `EmbeddingClientConfig` and its usage in `_fetch_embedding()`
- Remove `embed_dim` field from `EmbeddingClientConfig` and its dimension validation logic
- Remove `EmbeddingErrorKind.DIMENSION_MISMATCH` enum member
- Fix `config/ingester.toml` `embed_url` double-suffix bug
- Update docstrings/comments referencing E5, prefixes, or dimension validation

**Cross-file coordination**: `scripts/agent/factory.py` `embed_dim` argument removal and `config/ingester.toml` `embedding_dims = 384` removal are handled by `20260802-122033_embedding_dimension_constant.md`. Do NOT apply these changes again here.

# Assumptions

- The Qwen3 embedding model accepts raw text without any prefix — confirmed by existing `rag.llm_client.py` docstring noting E5-specific requirements
- Dimension mismatch detection is unnecessary because dimension is now a compile-time invariant (`QWEN3_EMBEDDING_DIMS = 1024`)
- All three embedding paths converge to the same API endpoint via `build_embed_url()`

# Design decisions

- Raw text payload: `{text}` — no prefix at all, simplest possible contract
- Dimension validation removal: since `get_embedding_dims()` always returns 1024, runtime dimension checks are meaningless
- Bug fix included in same change set: `embed_url` double-suffix in `config/ingester.toml` is an active bug affecting ingester; must be fixed atomically

# Alternatives considered

- Keep `query_prefix` field but hardcode to empty string: adds unnecessary indirection when prefix is never used
- Keep dimension validation but make it configurable: contradicts single-source-of-truth design from Plan 1
- Fix `embed_url` separately: would leave ingester broken until next deployment cycle

# Implementation

## Target file

### scripts/rag/ingestion/ingester.py

**Procedure:**

1. Remove `self._expected_dims` assignment in `__init__` (line 70):
   ```python
   self._expected_dims: int = int(cfg.get("embedding_dims", 384))
   ```

2. Change payload at line 238:
   - Before: `json={"content": f"passage: {text}"}`
   - After: `json={"content": text}`

3. Remove dimension mismatch check at lines 245-248:
   ```python
   if len(embedding) != self._expected_dims:
       raise ValueError(
           f"embedding dimension mismatch: expected {self._expected_dims}, got {len(embedding)}"
       )
   ```

4. Update docstring at lines 226-229:
   - Before:
     ```
     Return embedding vector for text; validates dimension against embedding_dims config.
     
     Returns None on empty input, network failure, or dimension mismatch.
     Expected dimension is read from common.toml::embedding_dims (default 384).
     ```
   - After:
     ```
     Return embedding vector for text.
     
     Returns None on empty input or network failure.
     ```

5. Remove comment at line 237:
   - Delete: `# E5 passage prefix is mandatory for document-side embedding`

**Method:** Delete lines, replace payload, update docstring.

**Details:**
- Line 70: delete `        self._expected_dims: int = int(cfg.get("embedding_dims", 384))`
- Line 237: delete `        # E5 passage prefix is mandatory for document-side embedding`
- Line 238: replace `json={"content": f"passage: {text}"}` → `json={"content": text}`
- Lines 245-248: delete dimension mismatch block
- Lines 226-229: rewrite docstring

---

### scripts/rag/llm_client.py

**Procedure:**

1. Change payload at line 260:
   - Before: `json={"content": f"query: {text}"}`
   - After: `json={"content": text}`

2. Update docstring at lines 253-256:
   - Before:
     ```
     Convert text to a 384-dimensional float embedding vector.
     
     E5 model requires "query: " prefix for query input.
     (Ingestion uses "passage: " prefix)
     ```
   - After:
     ```
     Convert text to a float embedding vector.
     ```

**Method:** Replace payload, update docstring.

**Details:**
- Line 253: replace `Convert text to a 384-dimensional float embedding vector.` → `Convert text to a float embedding vector.`
- Lines 255-256: delete both lines about E5 prefix
- Line 260: replace `json={"content": f"query: {text}"}` → `json={"content": text}`

---

### scripts/agent/memory/embedding_client.py

**Procedure:**

1. Remove `query_prefix` field from `EmbeddingClientConfig` (lines 39-41):
   ```python
   query_prefix: str = (
       "query: "  # prepended to input text before sending to embedding API
   )
   ```

2. Remove `embed_dim` field from `EmbeddingClientConfig` (line 42):
   ```python
   embed_dim: int = 384  # expected output dimension; 0 disables validation
   ```

3. In `_fetch_embedding()` function signature:
   - Remove `query_prefix: str` parameter (line 61)
   - Remove `embed_dim: int = 0` parameter (line 62)

4. Change payload at line 66:
   - Before: `json={"content": f"{query_prefix}{text}"}`
   - After: `json={"content": text}`

5. Remove dimension mismatch block at lines 71-81:
   ```python
   if embed_dim > 0 and len(embedding) != embed_dim:
       logger.error(...)
       return EmbeddingResult(
           success=False,
           error_kind=EmbeddingErrorKind.DIMENSION_MISMATCH,
       )
   ```

6. Update `EmbeddingClient.fetch()` call site at lines 209-210:
   - Before:
     ```python
     _fetch_embedding(
         text,
         self._http,
         self._config.embed_url,
         self._config.query_prefix,
         self._config.embed_dim,
     ),
     ```
   - After:
     ```python
     _fetch_embedding(
         text,
         self._http,
         self._config.embed_url,
     ),
     ```

**Method:** Delete fields, remove parameters, replace payload, remove validation block.

**Details:**
- Lines 39-41: delete `query_prefix` field
- Line 42: delete `embed_dim` field
- Line 61: delete `, query_prefix: str` from function signature
- Line 62: delete `, embed_dim: int = 0` from function signature
- Line 66: replace `json={"content": f"{query_prefix}{text}"}` → `json={"content": text}`
- Lines 71-81: delete dimension mismatch block
- Lines 209-210: delete `self._config.query_prefix,` and `self._config.embed_dim,` arguments

---

### scripts/agent/factory.py

**Procedure:**

1. Remove `embed_dim=ctx.cfg.memory.memory_embed_dim` from `EmbeddingClientConfig` construction at line 424:
   - Before:
     ```python
     cfg = config_cls(
         embed_url=build_embed_url(ctx.cfg.rag.embed_url),
         timeout=ctx.cfg.memory.memory_embed_timeout_sec,
         embed_dim=ctx.cfg.memory.memory_embed_dim,
         local_only=ctx.cfg.memory.memory_local_only,
     )
     ```
   - After:
     ```python
     cfg = config_cls(
         embed_url=build_embed_url(ctx.cfg.rag.embed_url),
         timeout=ctx.cfg.memory.memory_embed_timeout_sec,
         local_only=ctx.cfg.memory.memory_local_only,
     )
     ```

**Method:** Delete keyword argument.

**Details:**
- Line 424: delete `, embed_dim=ctx.cfg.memory.memory_embed_dim`

---

### scripts/agent/memory/types.py

**Procedure:**

1. Remove `DIMENSION_MISMATCH = "dimension_mismatch"` enum member (line 80):
   ```python
   DIMENSION_MISMATCH = "dimension_mismatch"
   ```

**Method:** Delete enum member.

**Details:**
- Line 80: delete `    DIMENSION_MISMATCH = "dimension_mismatch"`

---

### tests/test_embedding_client.py

**Procedure:**

1. Update/remove test case asserting `DIMENSION_MISMATCH` behavior (lines 877-899):
    - Test class `TestDimensionValidation`:
      - `test_rejects_wrong_dimension` (lines 877-899): DELETE entire test — dimension validation no longer exists
      - `test_accepts_correct_dimension` (lines 901-...): DELETE entire test — `embed_dim` parameter removed from `EmbeddingClientConfig`, test is meaningless without it

2. Update test cases that construct `EmbeddingClientConfig` with `embed_dim=` or `query_prefix=`:
    - Line 29: `embed_dim=0,` — REMOVE this argument (field deleted)
    - Line 887: `embed_dim=384,` — REMOVE this argument (field deleted)
    - Line 908: `embed_dim=384,` — REMOVE this argument (field deleted)
    - Line 924: `embed_dim=0,` — REMOVE this argument (field deleted)

**Method:** Delete tests, update remaining test constructions.

**Details:**
- Lines 877-899: delete `test_rejects_wrong_dimension` entirely
- Lines 901-...: delete `test_accepts_correct_dimension` entirely (entire `TestDimensionValidation` class)
- Line 29: delete `, embed_dim=0` from EmbeddingClientConfig construction
- Line 887: delete `, embed_dim=384` from EmbeddingClientConfig construction
- Line 908: delete `, embed_dim=384` from EmbeddingClientConfig construction
- Line 924: delete `, embed_dim=0` from EmbeddingClientConfig construction

---

### config/ingester.toml

**Procedure:**

1. **CRITICAL FIX:** Change `embed_url` at line 17:
    - Before: `embed_url = "http://192.168.11.238:8081/embedding"`
    - After: `embed_url = "http://192.168.11.238:8081"`
    - Rationale: `build_embed_url()` already appends `/embedding`; this is a pre-existing bug confirmed by comparing with `config/agent.toml` and `config/rag_pipeline_mcp_server.toml`

2. Change `embed_workers` at line 21:
    - Before: `embed_workers = 4`
    - After: `embed_workers = 1`

3. Remove `embedding_dims = 384` at line 18 — **HANDLED by `20260802-122033_embedding_dimension_constant.md`**:
    - Do NOT delete here; it is removed in the other file to avoid duplicate deletion

**Method:** Edit TOML values.

**Details:**
- Line 17: change value (remove `/embedding` suffix)
- Line 18: no action needed (handled by `20260802-122033_embedding_dimension_constant.md`)
- Line 21: change `4` → `1`

---

### config/agent.toml, config/rag_pipeline_mcp_server.toml (Step 7: verification only)

**Procedure:**

1. Confirm both files hold bare base URLs without `/embedding` suffix:
   - `config/agent.toml` line 10: `embed_url = "http://192.168.11.238:8081"` — correct, no change needed
   - `config/rag_pipeline_mcp_server.toml` line 10: `embed_url = "http://192.168.11.238:8081"` — correct, no change needed

**Method:** Verification only — no edits.

**Details:**
- No changes required — confirm current state matches target

---

### Various modules (Step 8: docstrings/comments)

**Procedure:**

1. Remove any remaining references to E5, passage/query prefixes, or dimension validation in affected modules
2. Confirm no hardcoded `384` remains near embedding call sites

**Affected files to check:**
- `scripts/db/store_protocols.py` — already handled in Plan 1
- `scripts/db/config.py` — already handled in Plan 1
- `scripts/rag/ingestion/ingester.py` — already handled above
- `scripts/rag/llm_client.py` — already handled above
- `scripts/agent/memory/embedding_client.py` — already handled above
- `tests/test_embedding_client.py` — handle during test updates

**Method:** grep + targeted edits.

**Details:**
- Run `grep -rn "384\|E5\|passage:\|query:" scripts/rag/ scripts/agent/memory/ tests/test_embedding_client.py` before editing
- Update only references that describe the old E5 conventions

# Compatibility considerations

- **Breaking change**: All three embedding HTTP paths now send raw text instead of prefixed text. If the embedding service expects E5-style prefixes, it will break.
- **Breaking change**: `EmbeddingClientConfig` loses `query_prefix` and `embed_dim` fields — any code constructing this dataclass with these fields will get TypeError.
- **Breaking change**: `EmbeddingErrorKind.DIMENSION_MISMATCH` removed — any match on this error kind will fail.
- **No regression**: `config/agent.toml` and `config/rag_pipeline_mcp_server.toml` already use bare base URLs — no change needed.

# Security considerations

N/A — removing request prefixes does not affect authentication, authorization, or data integrity.

# Rollback considerations

- Revert all changes in one commit (atomic rollback)
- Restore `query_prefix` and `embed_dim` fields in `EmbeddingClientConfig` if rolling back agent memory path changes
- Restore `"query: "` / `"passage: "` prefixes in payloads if embedding service requires them
- Restore `embed_url` with `/embedding` suffix in `config/ingester.toml` if rolling back ingester changes

# Validation plan

1. **Unit test — RagIngester sends raw text**: Assert payload is `{"content": text}` without prefix, no dimension mismatch exception raised
2. **Unit test — rag.llm_client.get_embedding() sends raw text**: Assert payload is `{"content": text}` without prefix
3. **Unit test — _fetch_embedding() sends raw text**: Assert payload is `{"content": text}` without prefix, no dimension mismatch result under any input
4. **Unit test — EmbeddingClientConfig has no query_prefix or embed_dim**: Assert these attributes do not exist
5. **Unit test — config/ingester.toml values**: Update existing tests that assert literal `embed_url` or `embed_workers` values
6. **Lint/typecheck**: `ruff`, `mypy` pass on all modified files
7. **Full test suite**: `pytest` passes

# Out of scope

- Changes to `MemoryStore(embed_dim=...)` in factory.py — out of scope per requirement (handled by separate requirement)
- `scripts/agent/factory.py` `embed_dim` argument removal — handled by `20260802-122033_embedding_dimension_constant.md`
- `config/ingester.toml` `embedding_dims = 384` removal — handled by `20260802-122033_embedding_dimension_constant.md`
- Migration of existing vector data
- Documentation updates outside source files (e.g., ops runbooks)

# Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-070538_require.md
- Source plan: plans/20260802-102821_plan.md
- Source implementation procedure: N/A
- Generated at: 20260802-122255
- Related target files: scripts/rag/ingestion/ingester.py, scripts/rag/llm_client.py, scripts/agent/memory/embedding_client.py, scripts/agent/factory.py, scripts/agent/memory/types.py, tests/test_embedding_client.py, config/ingester.toml, config/agent.toml, config/rag_pipeline_mcp_server.toml
