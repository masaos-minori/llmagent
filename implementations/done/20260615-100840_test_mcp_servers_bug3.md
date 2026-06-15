# Implementation: BUG-3 — mcp_servers entry in test helpers

## Goal

Add `"mcp_servers"` to the defaults dict of `_cfg()` / `_make_cfg()` in 6 test files
so that `build_agent_config()` no longer raises `ValueError: mcp_servers config section
is missing or empty`.

## Scope

**In**:
- `tests/test_tool_policy.py`
- `tests/test_tool_policy_comprehensive.py`
- `tests/test_tool_loop_guard.py`
- `tests/test_tool_runner.py`
- `tests/test_tool_audit.py`
- `tests/test_tool_approval.py`

**Out**: No changes to production code. `test_tool_result_formatter.py` and
`test_llm_client.py` already have `mcp_servers` — skip them.

## Assumptions

1. All 6 files end their defaults dict with `"github_server_url": "http://127.0.0.1:8006"`.
2. The dummy value `{"_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}}`
   satisfies `_build_mcp_servers()` validation and is never actually connected to.
3. Each file has exactly one `_cfg()` or `_make_cfg()` function.

## Implementation

### Target files and insertion points

| File | Target line (github_server_url) | New line inserted after |
|---|---|---|
| `tests/test_tool_policy.py` | L56 | L56 |
| `tests/test_tool_policy_comprehensive.py` | L58 | L58 |
| `tests/test_tool_loop_guard.py` | L50 | L50 |
| `tests/test_tool_runner.py` | L58 | L58 |
| `tests/test_tool_audit.py` | L58 | L58 |
| `tests/test_tool_approval.py` | L67 | L67 |

### Method

One Edit per file. Replace the `"github_server_url"` line to append the new entry:

```python
# Before
        "github_server_url": "http://127.0.0.1:8006",
    }

# After
        "github_server_url": "http://127.0.0.1:8006",
        "mcp_servers": {"_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}},
    }
```

Note: the surrounding `}` closure is used as context anchor to ensure uniqueness
of each Edit operation.

## Validation plan

1. `uv run pytest tests/test_tool_policy.py -x -v` — no ValueError on mcp_servers
2. `uv run pytest tests/test_tool_audit.py tests/test_tool_approval.py -x -v` — pass
3. `uv run pytest tests/test_tool_loop_guard.py tests/test_tool_policy_comprehensive.py -x -v` — pass
