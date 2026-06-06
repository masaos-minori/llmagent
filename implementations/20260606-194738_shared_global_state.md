# Implementation: Remove Module-Global State from shared/token_counter.py and shared/route_resolver.py

## Goal

1. Move `_warned_unavailable` from module-global to instance scope in `shared/token_counter.py`
2. Add optional `warn_on_fallback` mode to `ToolRouteResolver` in `shared/route_resolver.py`

## Scope

**In:**
- `token_counter.py`: move `_warned_unavailable: bool` from module level to `TokenCounter` class attribute (or caller-pass pattern)
- `route_resolver.py`: add `warn_on_fallback: bool = False` constructor parameter; emit `logger.warning()` when fallback routing is used

**Out:**
- Changing the default behavior of either module
- Strict mode that raises on fallback (deferred; too disruptive)

## Assumptions

- `scripts/shared/token_counter.py`: module-level `_warned_unavailable: bool = False` at line ~20; `TokenCounter` class uses it via `global _warned_unavailable`
- `scripts/shared/route_resolver.py`: `ToolRouteResolver.__init__()` takes `server_configs: dict[str, McpServerConfig]`; `_fallback_route()` is called when config map misses

## Implementation

### 1. `scripts/shared/token_counter.py`

Move `_warned_unavailable` to an instance variable:

```python
class TokenCounter:
    def __init__(self, tokenize_url: str = "") -> None:
        self._tokenize_url = tokenize_url
        self._warned_unavailable: bool = False   # was: module-global

    async def count(self, text: str) -> int:
        # ... existing logic ...
        if not self._tokenize_url and not self._warned_unavailable:
            logger.warning(
                "TokenCounter: tokenize_url not configured; falling back to char/4 estimate"
            )
            self._warned_unavailable = True
        # ... rest unchanged ...

    def reset_warned(self) -> None:
        """Reset warn-once flag; useful for testing."""
        self._warned_unavailable = False
```

Remove the module-level `_warned_unavailable` and the `global _warned_unavailable` statement. No `# noqa` needed since there is no more module-level mutable state.

Update callers: anywhere `TokenCounter()` is constructed, ensure it is an instance (not a module-level singleton). If there is currently a module-level `_counter` singleton, replace with instance construction at the appropriate scope (factory or context).

### 2. `scripts/shared/route_resolver.py`

```python
class ToolRouteResolver:
    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        warn_on_fallback: bool = False,
    ) -> None:
        self._config_map: dict[str, str] = {}
        for key, cfg in server_configs.items():
            for tool_name in cfg.tool_names:
                self._config_map[tool_name] = key
        self._warn_on_fallback = warn_on_fallback

    def resolve(self, tool_name: str) -> str:
        key = self._config_map.get(tool_name)
        if key is not None:
            return key
        if self._warn_on_fallback:
            logger.warning(
                "ToolRouteResolver: tool %r not in config map; using static fallback. "
                "Add tool_names to mcp_servers config to suppress this warning.",
                tool_name,
            )
        return self._fallback_route(tool_name)
```

Default `warn_on_fallback=False` preserves existing behavior. Callers that want visibility into unregistered tools can pass `warn_on_fallback=True`.

## Validation plan

```bash
uv run ruff check scripts/shared/token_counter.py scripts/shared/route_resolver.py
uv run mypy scripts/
uv run pytest tests/test_token_counter.py tests/test_route_resolver.py -v
```

Add to `tests/test_token_counter.py`:
```python
def test_warned_unavailable_is_per_instance():
    """Two TokenCounter instances have independent warn flags."""
    c1 = TokenCounter("")
    c2 = TokenCounter("")
    # trigger warn on c1
    asyncio.run(c1.count("hello"))
    assert c1._warned_unavailable is True
    assert c2._warned_unavailable is False  # not shared
```

Add to `tests/test_route_resolver.py`:
```python
def test_fallback_emits_warning_when_enabled(caplog):
    """warn_on_fallback=True emits a warning when static fallback is used."""
    resolver = ToolRouteResolver({}, warn_on_fallback=True)
    with caplog.at_level(logging.WARNING):
        resolver.resolve("search_web")
    assert "static fallback" in caplog.text

def test_fallback_silent_by_default(caplog):
    """Default resolver does not emit warnings on fallback."""
    resolver = ToolRouteResolver({})
    with caplog.at_level(logging.WARNING):
        resolver.resolve("search_web")
    assert "static fallback" not in caplog.text
```
