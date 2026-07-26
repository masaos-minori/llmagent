# Implementation Procedure: Optional Secondary Validation for Mode Classification

## Goal

Add optional secondary validation for LLM-based mode classification results to detect unreasonable classifications before system hint injection.

## Scope

**In-Scope:**
- Add heuristic consistency check between classification result and query content in `scripts/agent/mode_classification.py:36-38`

**Out-of-Scope:**
- Replacing the LLM-based classification entirely
- Any changes beyond the classification validation step

## Target Files

- `scripts/agent/mode_classification.py` — add validation step after classification

## Current Behavior Analysis

From `mode_classification.py`:
```python
def classify_and_inject_mode(query: str, ctx: AgentContext) -> None:
    config_mode = getattr(ctx.cfg, "mdq_rag_mode", None)
    mode = resolve_mode(query, config_mode)  # LLM-based classification
    ...
    hint = _mode_hint(mode)
    if hint:
        ctx.conv.append_message(...)  # Injects system hint without validation
```

Current behavior: The classification result (`resolve_mode`) is used directly without any secondary validation. If the LLM returns an incorrect classification, the wrong system hint is injected.

## Design

Add a heuristic consistency check after classification:

```python
def _validate_classification(query: str, mode: MdqRagMode) -> bool:
    """Heuristic check: verify classification makes sense for the query."""
    if mode == MdqRagMode.MDQ:
        # MDQ should be selected when query contains structural keywords
        mdq_keywords = ["structure", "outline", "schema", "definition", "reference"]
        query_lower = query.lower()
        has_mdq_signal = any(kw in query_lower for kw in mdq_keywords)
        if not has_mdq_signal:
            logger.warning("MDQ classification may be incorrect: no structural keywords found")
            return False
    elif mode == MdqRagMode.RAG:
        # RAG should be selected when query contains semantic keywords
        rag_keywords = ["explain", "summarize", "compare", "general", "overview"]
        query_lower = query.lower()
        has_rag_signal = any(kw in query_lower for kw in rag_keywords)
        if not has_rag_signal:
            logger.warning("RAG classification may be incorrect: no semantic keywords found")
            return False
    return True
```

Apply validation before injecting hint:
```python
hint = _mode_hint(mode)
if hint:
    if not _validate_classification(query, mode):
        logger.info("Classification validation failed; keeping default mode")
        mode = MdqRagMode.RAG  # Fallback to safe default
    ctx.conv.append_message(
        {"role": "system", "content": hint, "_ephemeral": True},
        source="cmd_handler",
    )
```

## Implementation Steps

### Step 1: Add `_validate_classification()` function

After `_mode_hint()` function in `mode_classification.py`, add:

```python
_MDQ_KEYWORDS = frozenset({"structure", "outline", "schema", "definition", "reference"})
_RAG_KEYWORDS = frozenset({"explain", "summarize", "compare", "general", "overview"})


def _validate_classification(query: str, mode: MdqRagMode) -> bool:
    """Heuristic check: verify classification makes sense for the query."""
    query_lower = query.lower()
    if mode == MdqRagMode.MDQ:
        if not any(kw in query_lower for kw in _MDQ_KEYWORDS):
            logger.warning("MDQ classification may be incorrect: no structural keywords found")
            return False
    elif mode == MdqRagMode.RAG:
        if not any(kw in query_lower for kw in _RAG_KEYWORDS):
            logger.warning("RAG classification may be incorrect: no semantic keywords found")
            return False
    return True
```

### Step 2: Apply validation before hint injection

In `classify_and_inject_mode()`, modify the hint injection section:

```python
hint = _mode_hint(mode)
if hint:
    if not _validate_classification(query, mode):
        logger.info("Classification validation failed; using fallback mode")
        mode = MdqRagMode.RAG
        hint = _mode_hint(mode)
    ctx.conv.append_message(
        {"role": "system", "content": hint, "_ephemeral": True},
        source="cmd_handler",
    )
```

### Step 3: Run lint and type check

```bash
uv run ruff check scripts/agent/mode_classification.py --fix
uv run mypy scripts/agent/mode_classification.py
```

### Step 4: Run tests

```bash
uv run pytest -q
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/mode_classification.py` | Heuristic validation catches known bad cases | Manual verification + existing tests | No regressions |

## Risks

- **Risk**: Heuristic introduces false positives → Mitigation: Start with conservative rules; log warnings rather than blocking
