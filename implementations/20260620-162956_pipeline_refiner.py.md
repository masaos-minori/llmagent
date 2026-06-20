# Implementation: Add trigger-condition details to refine_context() docstring

## Goal
Extend the `refine_context()` docstring in `scripts/rag/pipeline_refiner.py` to explicitly
document the trigger conditions for `"refiner_returned_empty"` — namely that the LLM
response content field must be `""` or whitespace-only after `.strip()`.

## Scope
- File: `scripts/rag/pipeline_refiner.py`
- Docstring-only change: `refine_context()` function docstring
- No behavior change

## Assumptions
- The table row currently reads `"LLM returned empty/falsy output"` — correct but lacks detail
- `RagLLM.refine_context()` calls `_extract_chat_content()` which returns `content.strip()`
- Empty string is falsy → `if refined:` is False → `"refiner_returned_empty"` path
- `ValueError` from `_extract_chat_content()` on malformed response → always hits exception path,
  never the empty-output path
- Three concrete triggers: content policy enforcement, LLM empty generation, prompt format
  producing no extractable key points

## Implementation

### Target file
`scripts/rag/pipeline_refiner.py`

### Procedure
Extend the existing `refiner_returned_empty` row in the return-contract table.

### Method
Single docstring edit — replace one cell in the table.

### Details

**Current table row (lines 57-59):**
```
| ``RefineResult(text=None, reason=               `` | LLM returned empty/falsy output.  |
| ``"refiner_returned_empty")``                      | Caller falls back to raw chunks.  |
```

**Updated row:**
```
| ``RefineResult(text=None, reason=               `` | LLM returned empty/falsy output.  |
| ``"refiner_returned_empty")``                      | Specifically: ``_extract_chat_content()`` |
|                                                    | returns ``""`` or whitespace-only  |
|                                                    | content after ``.strip()``, causing |
|                                                    | ``if refined:`` to be ``False``.   |
|                                                    | Triggers: content-policy refusal,  |
|                                                    | empty LLM generation, or prompt    |
|                                                    | producing no extractable key points.|
|                                                    | Caller falls back to raw chunks.   |
```

If the multi-line cell approach is too verbose for the existing table style, an alternative is to
add a note paragraph after the table instead:

```rst
.. note::
    ``"refiner_returned_empty"`` is triggered when ``_extract_chat_content()`` returns ``""``
    or whitespace-only content after ``.strip()`` (the ``if refined:`` guard is falsy).
    Causes: content-policy refusal, empty LLM generation, prompt format producing no key points.
    ``ValueError`` from malformed responses always reaches the ``"refiner_exception: ..."`` path.
```

In practice, since the existing docstring is plain reStructuredText-ish within a triple-quoted
string, append a plain-English paragraph after the table block:

```python
    Note:
        ``"refiner_returned_empty"`` fires only when ``_extract_chat_content()`` returns
        ``""`` or whitespace-only after ``.strip()``.  Common causes: content-policy refusal,
        empty LLM generation, or a prompt format that extracts no key points.
        ``ValueError`` from malformed responses always reaches the
        ``"refiner_exception: ..."`` path instead.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Trigger note present | `grep -c "whitespace-only" scripts/rag/pipeline_refiner.py` | >= 1 |
| Lint | `uv run ruff check scripts/rag/pipeline_refiner.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/pipeline_refiner.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
