# Implementation: Wire memory_local_only configuration into EmbeddingClientConfig

## Goal

Wire `memory_local_only` configuration into `EmbeddingClientConfig` so the local-only safety control is enforced end-to-end — and add the three specified unit tests to confirm the behavior.

## Scope

- **In-Scope**:
  - Verification that `MemoryConfig.memory_local_only` exists with default `False`
  - Verification that `_build_memory_config()` reads the key from the config dict
  - Verification that `factory._build_embedding_client()` passes `local_only` to `EmbeddingClientConfig`
  - Verification that `EmbeddingClient.__init__()` rejects non-local URLs when `local_only=True`
  - Three unit tests: `test_memory_local_only_default_false`, `test_memory_local_only_passed_to_embedding_client`, `test_memory_local_only_rejects_non_local_embed_url`
- **Out-of-Scope**:
  - Changes to DB schema
  - RAG-layer embedding client
  - `/memory status` display logic (already reads `EmbeddingClientStatus.local_only`)

## Assumptions

- All code changes described in the requirement are already implemented (confirmed by code audit).
- The three required test names exist in `tests/test_memory_local_only.py` under equivalent test IDs.
- `config/memory.toml` already contains `memory_local_only = false`.
- No new modules or packages need to be created.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Requirement says "add memory_local_only to MemoryConfig" but the field already exists at line 320 — possible the requirement was written before the implementation landed | Confirmed: `memory_local_only: bool = False` exists at `config_dataclasses.py:320` |
| UNK-02 | Test names in requirement (`test_memory_local_only_default_false` etc.) do not exactly match method names in existing file | Existing names are `test_default_false`, `test_factory_passes_local_only_to_embedding_client`, `test_non_local_url_rejected_when_local_only_true` — functionally equivalent, no rename needed unless exact names required by acceptance criteria |

## Verification Results

### 1. MemoryConfig.memory_local_only (VERIFIED COMPLETE)
- **File**: `scripts/agent/config_dataclasses.py:320`
- **Code**: `memory_local_only: bool = False`

### 2. _build_memory_config() reads the key (VERIFIED COMPLETE)
- **File**: `scripts/agent/config_builders.py:216`
- **Code**: `memory_local_only=bool(cfg.get("memory_local_only", False))`

### 3. factory._build_embedding_client() passes local_only (VERIFIED COMPLETE)
- **File**: `scripts/agent/factory.py:267`
- **Code**: `local_only=ctx.cfg.memory.memory_local_only`

### 4. EmbeddingClient rejects non-local URL when local_only=True (VERIFIED COMPLETE)
- **File**: `scripts/agent/memory/embedding_client.py:125-130`
- **Code**: Checks `config.local_only and config.embed_url`, raises `ValueError` if URL doesn't start with `_LOCAL_PREFIXES`

### 5. Config file has memory_local_only (VERIFIED COMPLETE)
- **File**: `config/memory.toml:26`
- **Content**: `memory_local_only = false`

### 6. Tests exist (VERIFIED COMPLETE)
- **File**: `tests/test_memory_local_only.py`
- **Tests**: 10 test methods covering all three acceptance criteria:
  - `test_default_false` — verifies default is False
  - `test_config_builder_reads_memory_local_only_true` — verifies config builder reads True
  - `test_config_builder_reads_memory_local_only_false` — verifies config builder reads False
  - `test_factory_passes_local_only_to_embedding_client` — verifies factory passes local_only=True
  - `test_factory_passes_local_only_false` — verifies factory passes local_only=False
  - `test_non_local_url_rejected_when_local_only_true` — verifies ValueError on non-local URL
  - `test_localhost_url_allowed_when_local_only_true` — verifies localhost URL allowed
  - `test_127_url_allowed_when_local_only_true` — verifies 127.0.0.x URL allowed

### 7. Config reload support (VERIFIED COMPLETE)
- **File**: `scripts/agent/services/config_reload.py:536-537`
- **Code**: Reloads `memory_local_only` from new config on hot-reload

## Remaining Actions

If exact test method names are required by acceptance criteria, rename the three test methods to match:

1. **Phase 2: Test naming alignment**
   - [ ] Rename `test_default_false` → `test_memory_local_only_default_false`
   - [ ] Rename `test_factory_passes_local_only_to_embedding_client` → `test_memory_local_only_passed_to_embedding_client`
   - [ ] Rename `test_non_local_url_rejected_when_local_only_true` → `test_memory_local_only_rejects_non_local_embed_url`

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `MemoryConfig` | Unit: default value | `uv run pytest tests/test_memory_local_only.py::TestMemoryLocalOnlyConfig::test_default_false -v` | `memory_local_only is False` |
| `_build_memory_config()` | Unit: reads from config dict | `uv run pytest tests/test_memory_local_only.py::TestMemoryLocalOnlyConfig -v` | All 4 builder tests pass |
| `factory._build_embedding_client()` | Unit: passthrough verified via captured kwargs | `uv run pytest tests/test_memory_local_only.py::TestFactoryLocalOnlyPassthrough -v` | `local_only=True` passed |
| `EmbeddingClient` | Unit: ValueError on non-local URL | `uv run pytest tests/test_memory_local_only.py::TestLocalOnlyRejectsNonLocalUrl -v` | `ValueError` raised with `memory_local_only=True` in message |
| Full regression | All test files | `uv run pytest` | No failures introduced |

## Risks & Mitigations

- **Risk**: Requirement test names differ from existing test method names, causing confusion in CI filtering → **Mitigation**: Rename existing test methods to match the requirement-specified names during Phase 2 if exact names are required.
- **Risk**: `uv run radon` and `uv run bandit` are not runnable in this environment (SSL error) → **Mitigation**: Accept static analysis unavailability; rely on existing test suite and manual review.
- **Risk**: Implementation was already merged but requirement was not updated as "done" — could cause duplicate work → **Mitigation**: This plan records the as-found state; no code duplication will occur.
