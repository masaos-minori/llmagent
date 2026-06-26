# Implementation: Add local_only enforcement to EmbeddingClient

Steps covered: Plan 20260626-100121 — Steps 1-6

---

## Goal

Add `local_only: bool = False` to `EmbeddingClientConfig`, validate that `embed_url` is a loopback address when `local_only=True`, surface `local_only` state in `EmbeddingClientStatus`, and add it to `/memory status` output.

---

## Scope

- **In scope**:
  - `scripts/agent/memory/embedding_client.py`: `EmbeddingClientConfig.local_only`, URL validation, `EmbeddingClientStatus.local_only`
  - `config/memory.toml`: `memory_local_only` field
  - `/memory status` handler: display `local_only` state
  - docs: `05_agent_08_configuration.md`, `05_agent_10_operations-and-observability.md`, `05_agent_12_memory.md`
- **Out of scope**: embedding model changes

---

## Assumptions

- `EmbeddingClientConfig` has `embed_url: str`.
- Local prefixes: `http://localhost`, `http://127.0.0.1`, `http://[::1]`, `https://localhost`, `https://127.0.0.1`.
- `memory_local_only=True` + non-local `embed_url` → `ValueError` at init time.
- `memory_local_only=False` (default) → no change.

---

## Implementation

### Target file
`scripts/agent/memory/embedding_client.py`

### Procedure
1. Read `scripts/agent/memory/embedding_client.py` lines 30-60.
2. Step 1: Add `local_only: bool = False` to `EmbeddingClientConfig`.
3. Step 2: In `EmbeddingClient.__init__` or `__post_init__`, add URL validation:
   ```python
   _LOCAL_PREFIXES = (
       "http://localhost", "http://127.0.0.1", "http://[::1]",
       "https://localhost", "https://127.0.0.1",
   )
   if self._config.local_only and self._config.embed_url:
       if not any(self._config.embed_url.startswith(p) for p in _LOCAL_PREFIXES):
           raise ValueError(
               f"memory_local_only=True but embed_url is not a local address: "
               f"{self._config.embed_url!r}. Use http://localhost:PORT."
           )
   ```
4. Step 3: In `config/memory.toml`, add: `memory_local_only = false`.
5. Step 4: Add `local_only: bool` to `EmbeddingClientStatus` and set it in `get_status()`.
6. Step 5: In the `/memory status` handler, add: `local-only: enabled/disabled`.
7. Step 6: Update 3 docs with local-only guarantee description.

### Method
Config field addition + startup validation. Default `False` ensures no breaking change.

---

## Validation plan

- Run: `uv run pytest tests/agent/memory/test_embedding_client.py -x -v` — pass.
- Add test: `local_only=True` + non-local URL → `ValueError`.
- Add test: `local_only=True` + `http://localhost:8080` → no error.
- Add test: `local_only=False` + any URL → no error.
- Pre-commit: `pre-commit run --all-files` — pass.
