# Goal

Replace `_sd_tkn: Any` / `_split_c: Any` with a typed `SudachiTokenizerWrapper`
class, and change `except RuntimeError: continue with ""` to raise `TokenizationError`.

# Scope

- `scripts/rag/ingestion/chunk_japanese.py`

# Assumptions

1. `TokenizationError` from `rag.exceptions` (Step 2-1 prerequisite).
2. `_sd_tkn: Any` is a sudachipy `Tokenizer` instance; `_split_c: Any` is
   `sudachipy.SplitMode.C`.
3. The `SudachiTokenizerWrapper` can be defined inline in this file (not in
   `repository.py`) since this file is the primary user.
4. `except RuntimeError: continue with ""` (line 108) — the RuntimeError comes
   from sudachipy tokenization failure. After this change, raise `TokenizationError`
   so callers can decide whether to skip or abort.
5. Callers of the tokenization function must be updated to catch `TokenizationError`.

# Implementation

## Target file

`scripts/rag/ingestion/chunk_japanese.py`

## Procedure

1. Define `SudachiTokenizerWrapper` class:
   ```python
   class SudachiTokenizerWrapper:
       def __init__(self) -> None:
           import sudachipy  # noqa: PLC0415
           self._tkn = sudachipy.dictionary.Dictionary().create()
           self._mode = sudachipy.SplitMode.C
       def tokenize(self, text: str) -> list[str]:
           try:
               return [m.surface() for m in self._tkn.tokenize(text, self._mode)]
           except RuntimeError as e:
               raise TokenizationError(f"Sudachi tokenization failed: {e}") from e
   ```
2. Replace `_sd_tkn: Any` / `_split_c: Any` with `_tokenizer: SudachiTokenizerWrapper`.
3. Update `except RuntimeError: continue` to `except TokenizationError: raise`
   (or handle in caller).
4. Remove `from typing import Any` if no longer used.
5. Run ruff + mypy.

## Method

Typed wrapper class + exception promotion.

# Validation plan

- `grep -n "_sd_tkn\|_split_c\|: Any" scripts/rag/ingestion/chunk_japanese.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/chunk_japanese.py`
- `uv run mypy scripts/rag/ingestion/chunk_japanese.py`
