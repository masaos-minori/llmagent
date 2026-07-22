# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (core fix — `enabled_for_llm`)

Source plan: `plans/done/20260721-032809_plan.md` ("Fix `enabled_for_llm` never being set True
for discovered tools"), Implementation step 1.

**Filename check — not a duplicate of prior docs**: `implementations/done/` already contains 4
docs targeting this same file (`20260717-203830`, `20260717-224511`, `20260718-084109`,
`20260718-084819`), all from an earlier plan cycle that designed/built the module itself. None
of them pass `enabled_for_llm` to the `build_runtime_tool(...)` call in `_dedupe_and_build()` —
confirmed by reading each doc's Details/pseudocode section in full. Direct read of the current
real source (`scripts/agent/services/mcp_tool_discovery.py:311-322`) confirms the bug is still
present: the call has no `enabled_for_llm=` keyword argument at all, so every discovered tool
falls through to `build_runtime_tool()`'s documented default (`scripts/shared/runtime_tool.py:87,
102`: "`enabled_for_llm` defaults to `False`" when the caller omits it). This doc is not a
duplicate; it targets a fix the prior docs never covered.

## Goal

Every discovered tool that a server does not explicitly report as `enabled: false` in its
`/v1/tools` entry ends up with `RuntimeTool.enabled_for_llm == True`, so it is visible in
`RuntimeToolRegistry.llm_tool_definitions()` and therefore in the LLM's tool-calling payload.
A tool a server explicitly disables (`"enabled": false`) stays hidden (`enabled_for_llm ==
False`).

## Scope

**In scope**
- `scripts/agent/services/mcp_tool_discovery.py::_dedupe_and_build()` — the single
  `build_runtime_tool(...)` call site (currently at lines 311-322).

**Out of scope**
- `scripts/shared/runtime_tool.py::build_runtime_tool()`'s default-to-`False` behavior for
  *omitted* `enabled_for_llm` — correct and unchanged; the bug is that this call site never
  passes the keyword at all, not that the default itself is wrong.
- `RuntimeToolRegistry.apply_policy()` (`scripts/shared/runtime_tool_registry.py`) — only ANDs
  `enabled_for_llm` down at `/reload` time; not a source of truth, no change needed.
- `_validate_and_normalize_entry()`'s type-checked field tuple (the defensive `enabled`
  type-check, UNK-02 in the source plan) — tracked separately, see the paired doc
  `implementations/{later-ts}_mcp_tool_discovery.py.md` (defensive type-check for `enabled`).
- Test files — tracked separately (see `implementations/{ts}_test_mcp_tool_discovery.py.md` and
  `implementations/{ts}_test_runtime_tool_routing_integration.py.md`).

## Assumptions

1. `entry.get("enabled", True)` — defaulting to `True` when a server's discovery entry omits the
   `enabled` key entirely — is correct: a server that has not adopted the `enabled`/
   `disabled_reason` schema has no way to signal unavailability and must not have all of its
   tools silently hidden as a side effect of not implementing an unrelated schema. Verified: all
   6 servers without the schema (`shell`, `cicd`, `rag_pipeline`, `mdq`, `github`, `web_search`)
   omit the `enabled` key entirely from their `/v1/tools` entries; none emit a bare
   `"enabled": false` by accident (per the source plan's own Step-4 verification).
2. `entry["enabled"]`, when present, is a JSON boolean today (the 4 servers that emit it —
   `file/read`, `file/write`, `file/delete`, `git` — always send `true`/`false`). No current
   server sends a non-bool value, but `_validate_and_normalize_entry()` does not type-check
   `enabled` (confirmed: the type-checked tuple at lines 250-255 only covers `status`,
   `is_write`, `requires_serial`, `resource_scope`) — a defensive `bool(...)` wrapper at the call
   site costs nothing and prevents a non-bool value from poisoning `RuntimeTool.enabled_for_llm`'s
   declared `bool` type.
3. No other code path sets `enabled_for_llm=True` for a discovered tool between
   `build_runtime_tool()` construction and the LLM call: `apply_policy()`'s only call site is
   `scripts/agent/services/config_reload.py:187` (invoked on `/reload`, not at startup discovery
   time), and it only narrows (`enabled and tool.enabled_for_llm`), never widens.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (existing).

### Procedure

1. In `_dedupe_and_build()` (method starting at line 277), locate the `build_runtime_tool(...)`
   call inside the `for name, group in by_name.items():` loop (lines 311-322).
2. Add one keyword argument to the call: `enabled_for_llm=bool(entry.get("enabled", True))`.
3. No other lines in this method change. `by_name`, `is_fatal`, the duplicate-exclusion branch,
   and the `RuntimeToolRegistry(tools=built)` return are untouched.

### Method

One-line addition to an existing call expression; no new class, function, or control flow.

### Details

Current call (verbatim, `scripts/agent/services/mcp_tool_discovery.py:311-322`):

```python
built[name] = build_runtime_tool(
    name=name,
    server_key=server_key,
    server_url=server_url,
    description=str(entry.get("description", "")),
    input_schema=entry.get("inputSchema", entry.get("input_schema")),  # type: ignore[arg-type]
    raw_definition=entry,
    status=str(entry.get("status", "active")),
    is_write=entry.get("is_write"),  # type: ignore[arg-type]
    requires_serial=entry.get("requires_serial"),  # type: ignore[arg-type]
    capabilities=tuple(entry.get("capabilities", []) or []),  # type: ignore[arg-type]
)
```

Target call after the fix:

```python
built[name] = build_runtime_tool(
    name=name,
    server_key=server_key,
    server_url=server_url,
    description=str(entry.get("description", "")),
    input_schema=entry.get("inputSchema", entry.get("input_schema")),  # type: ignore[arg-type]
    raw_definition=entry,
    status=str(entry.get("status", "active")),
    is_write=entry.get("is_write"),  # type: ignore[arg-type]
    requires_serial=entry.get("requires_serial"),  # type: ignore[arg-type]
    capabilities=tuple(entry.get("capabilities", []) or []),  # type: ignore[arg-type]
    enabled_for_llm=bool(entry.get("enabled", True)),
)
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass, including new `enabled_for_llm` cases from the paired test doc |
| Integration/regression | `uv run pytest tests/test_tool_executor_routing.py tests/test_runtime_tool_routing_integration.py -v` | all pass; new end-to-end test (paired doc) fails against pre-fix code — verify by temporarily reverting this 1-line change and re-running |
| Full suite | `uv run pytest -q` | no new failures |
| Lint/format | `uv run ruff format scripts/ && uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors vs. pre-existing baseline |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/services/mcp_tool_discovery.py` | no bare except introduced |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
