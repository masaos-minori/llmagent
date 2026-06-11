# Goal

Implement Steps 5-13 of the memory layer refactoring plan:
jsonl_store.py, embedding_client.py, extract.py, ingestion.py,
retriever.py, injection.py, services.py, callers, and tests.

# Scope

- `scripts/agent/memory/jsonl_store.py` — Step 5
- `scripts/agent/memory/embedding_client.py` — Step 6
- `scripts/agent/memory/extract.py` — Step 7
- `scripts/agent/memory/ingestion.py` — Step 8
- `scripts/agent/memory/retriever.py` — Step 9
- `scripts/agent/memory/injection.py` — Step 10
- `scripts/agent/memory/services.py` — Step 11
- `scripts/agent/factory.py`, `scripts/agent/commands/cmd_memory.py` — Step 12
- Tests — Step 13

# Assumptions

1. All foundation files (enums, exceptions, models, ports) and core files (types, mapper, store) are complete.
2. `jsonl_store.py`: `quarantine_path` param removal; `read_all()` always raises `JsonlFormatError` on malformed lines.
3. `embedding_client.py`: `except Exception` → `except (httpx.RequestError,)` only; `resp.json()` → `orjson.loads(resp.content)` + EmbeddingResponse DTO check.
4. `extract.py`: `LLMMessage` → `HistoryMessage`; `msg.get("content") or ""` + `str(content_raw)` → `msg.content` typed access.
5. `ingestion.py`: `LLMMessage` → `HistoryMessage`; `except Exception` in `_link_duplicates` → `sqlite3.OperationalError, sqlite3.IntegrityError`.
6. `retriever.py`: `_recency_boost` catches `(ValueError, OverflowError)` silently → raise `MemorySchemaError`. But per plan risk note: if existing DB has invalid timestamps, tests may break. Decision: keep silent fallback with `logger.warning` instead of raising for recency_boost (this is a scoring function, not a correctness gate).
7. `injection.py`: `if not query.strip(): return []` → `raise InjectionValidationError(...)`. Callers must handle this.
8. `services.py`: `LLMMessage` → `HistoryMessage` in method signatures.
9. `factory.py`: `ConsistencyReport` DTO access — `.memories` instead of `["memories"]`.
10. `cmd_memory.py`: `MemoryType` enum usage for type filters.

# Implementation

## Target file

Multiple files (see Scope)

## Procedure

### Step 5: jsonl_store.py

Read current file to determine `quarantine_path` parameter locations and `strict` parameter.
Remove `quarantine_path` parameter from `__init__` and `read_all()`.
Remove `strict=False` path — always raise `JsonlFormatError` on parse failure.

### Step 6: embedding_client.py

In `_fetch_embedding`:
- Replace `except Exception as e:` (line 57) with `except (httpx.RequestError, asyncio.TimeoutError) as e:`.
- Replace `resp.json().get("embedding")` with:
  ```python
  import orjson
  data = orjson.loads(resp.content)
  embedding = data.get("embedding") if isinstance(data, dict) else None
  ```

### Step 7: extract.py

- Remove `from shared.types import LLMMessage`.
- Import `HistoryMessage` from `agent.memory.models`.
- Change all `msg: LLMMessage` type annotations to `msg: HistoryMessage`.
- Change `history: list[LLMMessage]` → `list[HistoryMessage]`.
- Replace `msg.get("content") or ""` → `msg.content` (HistoryMessage.content is always str).
- Remove `str(content_raw).strip()` → `msg.content.strip()` or `content.strip()`.
- Replace `msg.get("role")` → `msg.role`.
- `history: list[HistoryMessage]` in `extract_memories()`.
- `non_system = [m for m in history if m.get("role") != "system"]` → `m.role != "system"`.

### Step 8: ingestion.py

- Remove `from shared.types import LLMMessage`; import `HistoryMessage`.
- Change `list[LLMMessage]` → `list[HistoryMessage]` in method signatures.
- In `_link_duplicates`: `except Exception` → `except (sqlite3.OperationalError, sqlite3.IntegrityError)`.

### Step 9: retriever.py

- In `_recency_boost`: change `except (ValueError, OverflowError): return 0.0` →
  keep except but add `logger.warning(...)` and return 0.0 (safe logging, not silent).
  Rationale: this is a scoring function; a bad timestamp should not break search entirely.
- Remove `float(d.pop("distance", 999.0))` → use explicit `d.get("distance", 999.0)` with
  proper typing (or keep as-is if no dict access pattern to fix).

### Step 10: injection.py

- Replace `if not query.strip(): return []` with:
  ```python
  from agent.memory.exceptions import InjectionValidationError
  if not query.strip():
      raise InjectionValidationError("on_user_prompt query must not be empty")
  ```
- Update callers of `on_user_prompt` (in `services.py`) to catch `InjectionValidationError`.

### Step 11: services.py

- Import `HistoryMessage` from `agent.memory.models`.
- Change `LLMMessage` → `HistoryMessage` in method signatures.

### Step 12: callers

- `factory.py`: update any `check_consistency()["memories"]` → `.memories`.
- `cmd_memory.py`: `MemoryQuery(memory_type="semantic")` still works (StrEnum == str).

### Step 13: tests

- Add test for `JsonlFormatError` on malformed JSONL.
- Add test for `MemorySchemaError` on mapper missing field.
- Add test for `InjectionValidationError` on empty query.
- Update existing tests for `HistoryMessage` usage in extract tests.

## Method

Sequential file-by-file edits. extract.py and ingestion.py are the most impactful
because they require replacing `LLMMessage` TypedDict dict-access pattern with
`HistoryMessage` attribute access.

# Validation plan

- `grep -rn "except Exception" scripts/agent/memory/` → 0 hits
- `grep -rn "from shared.types import LLMMessage" scripts/agent/memory/` → 0 hits
- `uv run ruff check scripts/agent/memory/`
- `uv run mypy scripts/agent/memory/`
- `uv run pytest tests/ -k "memory" -v`
