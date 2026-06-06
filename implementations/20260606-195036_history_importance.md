# Implementation: Importance-Based History Compression

## Goal

Replace the fixed `compress_turns * 2` compression strategy in `HistoryManager` with importance-aware selection that protects high-importance messages (system prompts, tool errors, policy statements) from being compressed.

## Scope

**In:**
- Add optional `importance: float` and `pinned: bool` fields to `LLMMessage` (TypedDict with `total=False`, backward-compatible defaults)
- Add `_classify_importance(msg: LLMMessage) -> float` helper for rule-based scoring
- Update `HistoryManager.compress()` to use importance-based candidate selection
- Update `HistoryManager.force_compress()` to apply the same policy
- Return a `CompressResult` with a `protected_count` field indicating how many messages were kept

**Out:**
- Adding `importance` to the SQLite `messages` table (runtime-only; not persisted in Phase 1)
- LLM-based importance scoring (rule-based only in Phase 1)
- Changing the LLM summary call format

## Assumptions

- `scripts/agent/history.py`: `HistoryManager.compress()` extracts the oldest `compress_turns * 2` messages and summarizes them
- `scripts/shared/types.py`: `LLMMessage(TypedDict, total=False)` — adding optional fields with `total=False` is backward-compatible
- `compress_turns` config remains valid as the base window size
- `protect_turns` already skips the most recent N turns from compression

## Implementation

### 1. `scripts/shared/types.py` — add optional fields to `LLMMessage`

```python
class LLMMessage(TypedDict, total=False):
    role: str               # already present
    content: str | None     # already present
    tool_calls: list[dict]  # already present
    tool_call_id: str       # already present
    name: str               # already present
    importance: float       # NEW: 0.0–1.0; higher = less likely to be compressed
    pinned: bool            # NEW: True = never compress this message
```

Since `total=False`, all fields are optional and callers that don't set them get the intended default at access time via `.get()`.

### 2. `scripts/agent/history.py` — importance-based compression

Add a importance classifier:

```python
# Threshold: messages with importance >= this value are protected from compression
_DEFAULT_PROTECT_IMPORTANCE: float = 0.7

_POLICY_KEYWORDS = re.compile(
    r"\b(rule|policy|always|never|constraint|must|forbidden|required|invariant)\b",
    re.IGNORECASE,
)


def _classify_importance(msg: LLMMessage) -> float:
    """Return an importance score 0.0–1.0 based on message content/role.

    Used when the message does not carry an explicit 'importance' field.
    """
    role = msg.get("role", "")
    content = str(msg.get("content") or "")
    if role == "system":
        return 1.0  # system prompts always protected
    if role == "tool":
        # Tool error messages are important; results are less so
        if "error" in content.lower() or "failed" in content.lower():
            return 0.8
        return 0.3
    if role == "assistant" and _POLICY_KEYWORDS.search(content):
        return 0.8
    if role == "user" and _POLICY_KEYWORDS.search(content):
        return 0.9  # explicit user rules
    return 0.5  # default neutral importance
```

Update `compress()` to use importance:

```python
def _select_compress_candidates(
    self,
    compressible: list[LLMMessage],
) -> tuple[list[LLMMessage], list[LLMMessage]]:
    """Split compressible messages into (to_compress, to_protect) based on importance."""
    to_protect = []
    to_compress = []
    for msg in compressible:
        explicit = msg.get("importance")
        importance = explicit if explicit is not None else _classify_importance(msg)
        if msg.get("pinned") or importance >= _DEFAULT_PROTECT_IMPORTANCE:
            to_protect.append(msg)
        else:
            to_compress.append(msg)
    return to_compress, to_protect
```

In `compress()`, use `_select_compress_candidates()` instead of slicing `[:compress_turns * 2]`.

### 3. `CompressResult` — structured return value

```python
@dataclasses.dataclass
class CompressResult:
    compressed_count: int
    protected_count: int
    summary_added: bool
```

Return `CompressResult` from `compress()` and `force_compress()` instead of returning the history list alone. Callers that ignore the return value are unaffected; callers that need the metadata can inspect it.

## Validation plan

```bash
uv run ruff check scripts/agent/history.py scripts/shared/types.py
uv run mypy scripts/
uv run pytest tests/test_history.py -v
```

Add to `tests/test_history.py`:

```python
def test_system_message_not_compressed():
    """System messages are never compressed regardless of compress_turns."""
    history = [
        make_msg("system", "You are a helpful assistant."),
        *[make_msg("user", f"q{i}") + make_msg("assistant", f"a{i}") for i in range(10)],
    ]
    mgr = HistoryManager(http, ..., compress_turns=2)
    new_history, result = await mgr.compress(history)
    assert any(m["role"] == "system" for m in new_history)
    assert result.protected_count >= 1

def test_pinned_message_not_compressed():
    """Pinned messages survive compression."""
    pinned = make_msg("user", "Always use type annotations.", pinned=True)
    ...

def test_policy_keyword_message_protected():
    """User message with policy keyword gets importance >= 0.9."""
    msg = make_msg("user", "You must always use type annotations.")
    assert _classify_importance(msg) >= 0.9
```
