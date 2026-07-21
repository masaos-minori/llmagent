# `scripts/shared/tool_executor.py` crashes on import — `NameError: RuntimeToolRegistry` breaks agent startup

## Severity

Critical — importing `agent.factory` (and therefore starting the agent process at all) raises an
unhandled `NameError` at module load time. This is a currently-live regression on `master`, not a
hypothetical risk.

## Context

Commit `3c4fbe06` ("feat: make RuntimeToolRegistry sole routing authority; merge browser-mcp into
web-search-mcp") added a `TYPE_CHECKING`-only import of `RuntimeToolRegistry` to
`scripts/shared/tool_executor.py` and used the bare (non-string) type name as a runtime method
annotation:

```python
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry
...
class ToolExecutor(ToolTransportInvoker):
    ...
    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
```

Because `scripts/shared/tool_executor.py` has **no** `from __future__ import annotations` at the top
of the file, Python evaluates parameter annotations eagerly at class-body execution time. Since
`RuntimeToolRegistry` is only imported inside the `TYPE_CHECKING` guard (never imported at runtime),
the name is undefined the moment the class body executes, and the module raises `NameError` before it
can even finish loading.

Every other file in the codebase using the same `if TYPE_CHECKING:` guard pattern for a similar
purpose (`scripts/agent/tool_policy.py`, `scripts/agent/repository_gateway.py`, and others) has
`from __future__ import annotations` at the top, which defers all annotation evaluation and avoids
this failure mode. `scripts/shared/tool_executor.py` is missing that import — this is the one file in
the pattern that lacks it, confirmed by `grep -n "from __future__" scripts/shared/tool_executor.py`
returning nothing while the comparison files return a match.

## Evidence

Direct reproduction (2026-07-21, on current `master`):

```
$ PYTHONPATH=scripts .venv/bin/python3 -c "import shared.tool_executor"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import shared.tool_executor
  File ".../scripts/shared/tool_executor.py", line 45, in <module>
    class ToolExecutor(ToolTransportInvoker):
    ...
  File ".../scripts/shared/tool_executor.py", line 76, in ToolExecutor
    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
                                             ^^^^^^^^^^^^^^^^^^^
NameError: name 'RuntimeToolRegistry' is not defined
```

```
$ PYTHONPATH=scripts .venv/bin/python3 -c "from agent import factory"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from agent import factory
  File ".../scripts/agent/factory.py", line 23, in <module>
    from shared.tool_executor import ToolExecutor
  File ".../scripts/shared/tool_executor.py", line 45, in <module>
    class ToolExecutor(ToolTransportInvoker):
    ...
NameError: name 'RuntimeToolRegistry' is not defined
```

`grep -rln "from shared.tool_executor import\|import shared.tool_executor" scripts/ --include="*.py"`
shows three importers: `scripts/agent/factory.py`, `scripts/agent/context.py`,
`scripts/agent/repository_gateway.py` — all core agent-startup modules.

This is also the confirmed root cause of the test-suite-wide failures observed during unrelated
implementation work today: the full `pytest` suite currently reports 25 failed / 17 errors, and
re-running with an unrelated file temporarily removed produced the exact same failure/error count,
isolating the cause to this pre-existing import break rather than any change made today.

## Impact

Any code path that imports `agent.factory`, `agent.context`, or `agent.repository_gateway` —
including normal agent process startup — fails immediately with an unhandled `NameError`. This is not
a partial/cosmetic issue: it prevents the agent from starting at all via the normal import chain.

## Recommended action

Add `from __future__ import annotations` to the top of `scripts/shared/tool_executor.py`, matching the
pattern already used in every other file with a `TYPE_CHECKING`-only import used in a runtime
annotation (e.g. `scripts/agent/tool_policy.py`, `scripts/agent/repository_gateway.py`). This defers
all annotation evaluation and is the minimal, consistent fix — no behavior change beyond making the
module importable again.

After the fix:
1. Re-run `PYTHONPATH=scripts .venv/bin/python3 -c "from agent import factory"` and confirm it no
   longer raises.
2. Re-run the full test suite (`uv run pytest -q`) and confirm the 25 failed / 17 errors from this
   root cause clear (some may remain for unrelated reasons — isolate and re-triage any that persist).
3. Consider a lint rule / pre-commit check that flags a `TYPE_CHECKING`-only import used as a bare
   (non-string) runtime annotation without `from __future__ import annotations` present, to prevent
   this class of regression recurring.

## Status

Open, not yet fixed (2026-07-21). Discovered incidentally while implementing an unrelated set of
plans (`implementations/done/20260720-134152_agent.toml.md`,
`implementations/done/20260720-134218_test_mcp_server_cmd_paths.py.md`,
`implementations/done/20260720-134259_20260720-070458_mcp_server_agent_toml_cmd_points_to_deleted_files.md.md`)
— fixing it is out of scope for those plans and requires its own planning/implementation pass.
