# Goal

Replace `cfg: dict` / `cfg: dict[str, Any]` parameters in all four stage classes
(`MqeStage`, `FusionStage`, `RerankStage`, `SearchStage`) with typed config DTOs,
and convert all `cfg.get("key", default)` to typed attribute access.

# Scope

- `scripts/rag/stages/mqe.py`
- `scripts/rag/stages/fusion.py`
- `scripts/rag/stages/rerank.py`
- `scripts/rag/stages/search.py`

# Assumptions

1. `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig` from `rag.models`
   (Step 2-3 prerequisite).
2. `cfg.get("use_mqe", True)` → `cfg.use_mqe`; `cfg.get("rrf_k", 60)` → `cfg.rrf_k`; etc.
3. Stage constructors change from `__init__(self, cfg: dict, ...)` to
   `__init__(self, cfg: MqeConfig, ...)` etc.
4. The pipeline builder (`pipeline.py`) constructs these config DTOs from the raw
   TOML dict — that conversion happens in Step 4-4 (pipeline.py refactor).
5. The `except Exception` in `search.py` is also removed in this step (Step 4-2
   is merged here for efficiency).
6. After this step, `cfg.get(...)` calls should be 0 in all four stage files.

# Implementation

## Target file

`scripts/rag/stages/mqe.py`, `fusion.py`, `rerank.py`, `search.py`

## Procedure

### mqe.py
1. Change `_run_mqe(query, context, cfg: dict, ...)` →
   `_run_mqe(query, context, cfg: MqeConfig, ...)`.
2. Replace `cfg.get("use_mqe", True)` → `cfg.use_mqe`, etc.
3. Change `MqeStage.__init__(cfg: dict, ...)` → `(cfg: MqeConfig, ...)`.

### fusion.py
1. Change `FusionStage.__init__(cfg: dict)` → `(cfg: FusionConfig)`.
2. Replace `cfg.get("rrf_k", 60)` → `cfg.rrf_k`.

### rerank.py
1. Change `_rerank(query, merged, cfg: dict, ...)` → `(cfg: RerankConfig, ...)`.
2. Replace `cfg.get("use_rerank", True)` → `cfg.use_rerank`, etc.
3. Change `RerankStage.__init__(cfg: dict, ...)` → `(cfg: RerankConfig, ...)`.

### search.py
1. Change `SearchStage.__init__(cfg: dict[str, Any], ...)` →
   `(cfg: SearchConfig, ...)`.
2. Replace all `cfg.get("key", default)` → `cfg.key`.
3. Replace `except Exception as e:` (line 53) with specific exception types:
   `except (httpx.RequestError, httpx.HTTPStatusError, orjson.JSONDecodeError) as e:`

## Method

Type signature change + `get()` → attribute substitution.

# Validation plan

- `grep -n "cfg\.get\|except Exception\|cfg: dict" scripts/rag/stages/mqe.py scripts/rag/stages/fusion.py scripts/rag/stages/rerank.py scripts/rag/stages/search.py` → 0 hits
- `uv run ruff check scripts/rag/stages/`
- `uv run mypy scripts/rag/stages/`
- `uv run pytest tests/test_rag_pipeline.py -v`
