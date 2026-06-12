# Implementation: agent/memory/models.py + injection.py + services.py + orchestrator.py + repl.py (Step 6)

## Goal

Add `MemorySnippet` frozen dataclass to `agent/memory/models.py`. Change
`injection.py:on_session_start()` and `on_user_prompt()` to return `list[MemorySnippet]`.
Update `services.py` Protocol signatures. Update `orchestrator.py` and `repl.py` callers
to access `.text` attribute.

## Scope

- Modified: `scripts/agent/memory/models.py`
- Modified: `scripts/agent/memory/injection.py`
- Modified: `scripts/agent/memory/services.py`
- Modified: `scripts/agent/orchestrator.py`
- Modified: `scripts/agent/repl.py`
- Modified: `tests/test_memory_layer.py`

## Assumptions

- `memory/models.py` currently defines `HistoryMessage`, `JsonlRecord`, `ConsistencyReport`,
  `EmbeddingRequest`, `EmbeddingResponse`, `InjectionSnippet` — `MemorySnippet` is absent.
- `injection.py:on_session_start()` currently returns `list[str]` built with
  `f"{self._policy.format_prefix_semantic} {e.summary...}"` expressions.
- `injection.py:on_user_prompt()` builds `snippets: list[str]` with `.append(f"...")`.
- `orchestrator.py:_handle_memory_injection()` joins with `f"- {s}"`.
- `repl.py:_initialize_session()` joins with `f"- {s}"` (line ~280).
- LLM-delivered text is identical before and after — only the container type changes.

## Implementation

### Target file

`scripts/agent/memory/models.py` (primary), 4 additional files

### Procedure

1. Add `MemorySnippet` dataclass to `memory/models.py` (append after `InjectionSnippet`).
2. In `injection.py`: add import; change `on_session_start()` and `on_user_prompt()` return
   types and list construction.
3. In `services.py`: update Protocol / concrete class signatures.
4. In `orchestrator.py:_handle_memory_injection()`: change `f"- {s}"` → `f"- {snippet.text}"`.
5. In `repl.py:_initialize_session()`: same change.
6. Update tests per Risk 1 table.

### Method

DTO wrapping — existing string content moved into `.text` field. LLM context output unchanged.

### Details

**`memory/models.py` addition:**
```python
@dataclass(frozen=True)
class MemorySnippet:
    """One memory snippet ready for LLM context injection."""
    text: str           # formatted string (includes prefix like "[Semantic memory]")
    source: str = ""    # "semantic" or "episodic"
    score: float = 0.0
```

**`injection.py:on_session_start()` change:**
```python
def on_session_start(self) -> list[MemorySnippet]:
    ...
    return [
        MemorySnippet(
            text=f"{self._policy.format_prefix_semantic} {e.summary if e.summary else e.content[:100]}",
            source="semantic",
        )
        for e in entries
    ]
```

**`injection.py:on_user_prompt()` change:**
```python
# Before: snippets: list[str] = []
# After:  snippets: list[MemorySnippet] = []
# Change each .append(f"...") to .append(MemorySnippet(text=f"...", source="semantic"/"episodic"))
```

**`services.py` Protocol changes:**
```python
def on_session_start(self, session_id: int | None) -> list[MemorySnippet]: ...
async def on_user_prompt(self, query: str, session_id: int | None) -> list[MemorySnippet]: ...
```

**`orchestrator.py:_handle_memory_injection()` (line ~117):**
```python
# Before: "\n".join(f"- {s}" for s in memory_snippets)
# After:  "\n".join(f"- {snippet.text}" for snippet in memory_snippets)
```

**`repl.py:_initialize_session()` (line ~280):**
```python
# Before: "\n".join(f"- {s}" for s in memory_snippets)
# After:  "\n".join(f"- {snippet.text}" for snippet in memory_snippets)
```

**Test changes:**
- `test_memory_layer.py:94-95` — `snippets[0].text`
- `test_memory_layer.py:134-135` — `s.text for s in snippets`
- `test_memory_layer.py:533,549` — `return_value=[MemorySnippet(text="snippet")]`

## Validation plan

| Check | Command | Expected |
|---|---|---|
| list[str] removed | `grep "-> list\[str\]" scripts/agent/memory/injection.py scripts/agent/memory/services.py` | 0 matches |
| Type check | `uv run mypy scripts/agent/memory/` | No new errors |
| Tests | `uv run pytest tests/test_memory_layer.py -v` | No new failures |
| Arch | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
