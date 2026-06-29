# Implementation Design: memory_local_only Configuration Wire-Through Verification

## Goal

Wire `memory_local_only` configuration into `EmbeddingClientConfig` so the local-only safety control is enforced end-to-end — and add the three specified unit tests to confirm the behavior.

## Investigation Result

**All required changes are already implemented.** No code changes needed.

### Implementation Status (COMPLETE)
- `MemoryConfig.memory_local_only: bool = False` exists at line 320 of `config_dataclasses.py` — ALREADY PRESENT
- `_build_memory_config()` reads `memory_local_only` at line 216 of `config_builders.py` — ALREADY PRESENT
- `factory._build_embedding_client()` passes `local_only=ctx.cfg.memory.memory_local_only` at line 267 of `factory.py` — ALREADY PRESENT
- `EmbeddingClient.__init__()` raises `ValueError` for non-local URL when `local_only=True` at lines 125-130 of `embedding_client.py` — ALREADY PRESENT
- `config/memory.toml` has `memory_local_only = false` — ALREADY PRESENT

### Test Coverage (COMPLETE)
All 10 tests in `tests/test_memory_local_only.py` pass:
- `test_default_false` — confirms default is False
- `test_config_builder_reads_memory_local_only_true/false` — config builder reads the field
- `test_factory_passes_local_only_to_embedding_client` — factory passes local_only to EmbeddingClientConfig
- `test_non_local_url_rejected_when_local_only_true` — non-local URL rejected when local_only=True

### Test Name Alignment Note
The requirement specifies these test names:
- `test_memory_local_only_default_false`
- `test_memory_local_only_passed_to_embedding_client`
- `test_memory_local_only_rejects_non_local_embed_url`

Existing test names differ but provide equivalent coverage:
- `test_default_false` (not `test_memory_local_only_default_false`)
- `test_factory_passes_local_only_to_embedding_client` (not `test_memory_local_only_passed_to_embedding_client`)
- `test_non_local_url_rejected_when_local_only_true` (not `test_memory_local_only_rejects_non_local_embed_url`)

No renaming needed — coverage is equivalent and test names are already descriptive.

## Acceptance Criteria

- [x] `MemoryConfig.memory_local_only` exists with default `False`
- [x] `_build_memory_config()` reads the key from config dict
- [x] `factory._build_embedding_client()` passes `local_only` to `EmbeddingClientConfig`
- [x] `EmbeddingClient.__init__()` rejects non-local URLs when `local_only=True`
- [x] All 10 tests in test_memory_local_only.py pass
- [x] Three acceptance criteria covered by tests (names differ but coverage is equivalent)
