# Goal

Remove the backward-compatibility re-exports of `SemanticCache` and `cosine_sim`
from `rag/repository.py` and update any callers that import them from there.

# Scope

- `scripts/rag/repository.py` — remove two re-export lines
- Any callers that do `from rag.repository import SemanticCache` or
  `from rag.repository import cosine_sim`

# Assumptions

1. `SemanticCache` is defined in `rag/cache.py`; callers should import from there.
2. `cosine_sim` is defined in `rag/utils.py`; callers should import from there.
3. The `# noqa: F401` comments mark these as intentional re-exports.
4. Run `grep -rn "from rag.repository import.*SemanticCache\|from rag.repository import.*cosine_sim"
   scripts/` before editing to enumerate callers.

# Implementation

## Target file

`scripts/rag/repository.py`

## Procedure

1. Remove `from rag.cache import SemanticCache as SemanticCache  # noqa: F401`.
2. Remove `from rag.utils import cosine_sim as cosine_sim  # noqa: F401`.
3. For each caller found by grep:
   - `from rag.repository import SemanticCache` → `from rag.cache import SemanticCache`
   - `from rag.repository import cosine_sim` → `from rag.utils import cosine_sim`
4. Run ruff + mypy.

## Method

Line deletion + caller update.

# Validation plan

- `grep -n "cosine_sim as cosine_sim\|SemanticCache as SemanticCache" scripts/rag/repository.py`
  → 0 hits
- `uv run ruff check scripts/rag/repository.py`
- `uv run mypy scripts/rag/repository.py`
