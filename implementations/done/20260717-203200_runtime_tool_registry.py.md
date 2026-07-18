# Implementation procedure: `scripts/shared/runtime_tool_registry.py`

Source plan: `plans/done/20260717-124020_plan.md` (requirement `requires/20260717_02_require.md`), Implementation step 3.

## Goal

Create `scripts/shared/runtime_tool_registry.py`, a new `RuntimeToolRegistry` class holding an in-memory
`{name: RuntimeTool}` map and exposing the 9 methods listed in the requirement: `resolve`, `get`,
`all_tools`, `llm_tool_definitions`, `tool_spec_map`, `tool_spec_for_call`, `is_side_effect`,
`classify_operation_type`, `apply_policy`. Depends on `scripts/shared/runtime_tool.py`'s `RuntimeTool`
(separate implementation doc) and reuses the existing, unmodified `scripts/shared/tool_spec.py`'s
`ToolSpec`. Unpopulated/unused until requirement 03 (MCP discovery) and requirements 04-08 (wiring).

## Scope

**In scope**
- New file `scripts/shared/runtime_tool_registry.py` only.
- `RuntimeToolRegistry` class + the 9 methods, operating on hand-constructed `RuntimeTool` fixtures.

**Out of scope**
- Populating the registry from live MCP discovery (requirement 03).
- Wiring any existing call site (`route_resolver.py`, `tool_executor_helpers.py`, `tool_policy.py`,
  `tool_runner.py`) to actually call into this registry (requirements 04-07).
- Modifying `scripts/shared/tool_spec.py`, `scripts/shared/tool_registry.py`,
  `scripts/agent/tool_policy.py`, `scripts/agent/tool_enums.py`, `scripts/agent/config_dataclasses.py`.

## Assumptions

1. **`classify_operation_type()` cannot return `scripts/agent/tool_enums.OperationType`.** The plan's
   Design section assumes this method "derive[s] an `OperationType`," and the Risks section discusses
   whether `DELETE`/`API_WRITE` granularity is achievable — but direct investigation confirms
   `OperationType` (values: `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`, `READ`; `scripts/agent/tool_enums.py:17-21`)
   lives in the **agent** layer. Per `.importlinter`'s `shared-is-leaf` contract, `scripts/shared/runtime_tool_registry.py`
   must not import `agent.tool_enums`. Resolution: `classify_operation_type()` returns a **plain string**
   restricted to a locally-declared `Literal["read", "write"]` (matching what `RuntimeTool`'s single
   `is_write: bool` field can actually distinguish today — confirmed no `is_delete`/`is_execute`/
   `is_api_write` field exists per the requirement's 13-field list). Any agent-layer caller wanting a
   real `OperationType` enum member wraps the returned string itself (`OperationType(result)`) — that
   wrapping happens in agent-layer code in a later requirement, not here. This satisfies the plan's own
   Risk #4 ("flag this explicitly ... if the requirement's field list is insufficient") — it is
   insufficient for `DELETE`/`API_WRITE`/`EXECUTE` granularity; this is a documented gap, not silently
   collapsed.

2. **`apply_policy(cfg)`'s `cfg` parameter cannot be `scripts/agent/config_dataclasses.ToolConfig`/
   `ApprovalConfig`.** Those dataclasses live in the **agent** layer
   (`scripts/agent/config_dataclasses.py:157` `ToolConfig`, `:269` `ApprovalConfig`) — importing either
   into `scripts/shared/runtime_tool_registry.py` would violate the same `shared-is-leaf` contract.
   Additionally, the plan's Design section references `cfg.approval.tool_safety_tiers`, which does
   **not exist** as a field name on `ApprovalConfig` (confirmed: `ApprovalConfig` has
   `approval_risk_rules: dict[str, str]` at line 272, not `tool_safety_tiers`). The tier-name → tier-value
   mapping the plan actually means lives in `config/agent.toml`'s separate `[tool_safety_tiers]` TOML
   table (`config/agent.toml:211-224`, e.g. `delete_file = "WRITE_DANGEROUS"`), consumed today only by
   `scripts/agent/tool_policy.py`'s `_TIER_TO_RISK` (agent-layer code, lines 42-47). Resolution:
   `apply_policy()`'s signature takes plain, duck-typed primitives instead of an agent config object —
   `tier_map: Mapping[str, AgentSafetyTier]` (tool name -> tier string) and
   `allowed_tools: Sequence[str] = ()` (empty = all allowed, mirroring `ToolConfig.allowed_tools`'s own
   documented convention at `config_dataclasses.py:196-197`). Whichever later requirement wires this to
   real config is responsible for extracting these primitives from `ToolConfig`/`agent.toml` and passing
   them in — `runtime_tool_registry.py` itself stays agent-agnostic.

3. `tool_spec_map()`/`tool_spec_for_call()` build `shared.tool_spec.ToolSpec` instances (6 fields,
   confirmed unchanged at `tool_spec.py:12-30`) by copying `RuntimeTool.is_write`/`.requires_serial`/
   `.resource_scope`, mirroring the *shape* (not the code, which is agent-layer) of
   `scripts/agent/tool_runner.py:54-73`'s `_build_tool_meta()` — that function is referenced here only
   as a behavioral model already reviewed in this codebase, not imported.

4. `is_side_effect(tool_name)` mirrors `scripts/shared/tool_executor_helpers.py:47-50`'s existing
   `is_side_effect()` contract (`tool_name: str -> bool`) but sources the answer from
   `self.get(tool_name).is_write` instead of the `_SIDE_EFFECT_TOOLS` frozenset — both live in `shared/`,
   so no layer-contract concern here; this is intentionally parallel, temporary duplication (per the
   plan's Assumption 1 / Risk #1), not a replacement — the module docstring must say so explicitly.

5. `resolve()`/`get()` unknown-name handling: `resolve()` mirrors
   `scripts/shared/tool_registry.py:75-78`'s `ToolRegistry.get_server_for_tool()` (`return None` on
   unknown name — direct quote: `td = self._tools.get(tool_name); return td.server_key if td else None`).
   `get()` raises (`KeyError` or a small custom exception) on a truly unregistered name, per the plan's
   Design section distinguishing "registered-but-under-annotated" (safe defaults apply, no raise) from
   "zero registry entry" (raise, don't paper over).

6. `llm_tool_definitions()` re-keys `RuntimeTool.input_schema` to `parameters` to match the shape LLM
   clients expect (`{"name", "description", "parameters"}`), confirmed against
   `config/agent.toml`'s `[[tool_definitions.function.parameters]]` blocks (e.g. lines 393-407) and
   `ToolConfig.tool_definitions: list[dict]` (`config_dataclasses.py:193`) — only tools with
   `enabled_for_llm=True` are included.

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py` (new).

### Procedure

1. Module docstring: state the registry is additive/unused until requirement 03 populates it and
   requirements 04-08 wire it in; state explicitly that `scripts/shared/tool_registry.py`'s `ToolRegistry`
   remains the sole routing authority for now (per that module's own docstring, `tool_registry.py:22-25`);
   state the two import-layer-driven design decisions from Assumptions 1 and 2 (no `agent.tool_enums`,
   no `agent.config_dataclasses` imports) so future contributors don't "fix" this by adding those imports.
2. Import only from `scripts/shared/runtime_tool.py` (`RuntimeTool`, `AgentSafetyTier`) and
   `scripts/shared/tool_spec.py` (`ToolSpec`) plus stdlib `typing`/`collections.abc`.
3. Define `RuntimeToolRegistry.__init__(self, tools: dict[str, RuntimeTool] | None = None) -> None`
   storing an internal mutable `dict[str, RuntimeTool]` (empty by default — per the plan's Assumption 2,
   population is requirement 03's job).
4. Implement the 9 methods per Details below.

### Method

Plain mutable class wrapping a `dict[str, RuntimeTool]`. No `Protocol`/`ABC` — single concrete
implementation, no polymorphism need identified at this step.

### Details

Method signatures (pseudocode — no production code):

```
class RuntimeToolRegistry:
    def __init__(self, tools: dict[str, RuntimeTool] | None = None) -> None: ...
        # self._tools: dict[str, RuntimeTool] = dict(tools) if tools else {}

    def resolve(self, tool_name: str) -> str | None:
        # entry = self._tools.get(tool_name)
        # return entry.server_key if entry else None

    def get(self, tool_name: str) -> RuntimeTool:
        # entry = self._tools.get(tool_name)
        # if entry is None: raise KeyError(f"unregistered tool: {tool_name}")
        # return entry

    def all_tools(self) -> list[RuntimeTool]:
        # return list(self._tools.values())

    def llm_tool_definitions(self) -> list[dict[str, object]]:
        # return [
        #     {"name": t.name, "description": t.description, "parameters": t.input_schema}
        #     for t in self._tools.values() if t.enabled_for_llm
        # ]

    def tool_spec_map(self) -> dict[str, ToolSpec]:
        # return {
        #     name: ToolSpec(call_id="", name=name, resource_scope=t.resource_scope,
        #                    requires_serial=t.requires_serial, is_write=t.is_write)
        #     for name, t in self._tools.items()
        # }

    def tool_spec_for_call(self, call_id: str, name: str, args: dict[str, object]) -> ToolSpec:
        # t = self.get(name)
        # return ToolSpec(call_id=call_id, name=name, args=args, resource_scope=t.resource_scope,
        #                  requires_serial=t.requires_serial, is_write=t.is_write)

    def is_side_effect(self, tool_name: str) -> bool:
        # return self.get(tool_name).is_write

    def classify_operation_type(self, tool_name: str) -> Literal["read", "write"]:
        # NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from RuntimeTool's fields alone (Assumption 1)
        # return "write" if self.get(tool_name).is_write else "read"

    def apply_policy(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        # for name, tool in list(self._tools.items()):
        #     tier = tier_map.get(name, tool.agent_safety_tier)
        #     enabled = (not allowed_tools) or (name in allowed_tools)
        #     requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
        #     self._tools[name] = dataclasses.replace(
        #         tool, agent_safety_tier=tier, requires_approval=requires_approval,
        #         enabled_for_llm=enabled and tool.enabled_for_llm,
        #     )
```

Note: `apply_policy()`'s exact re-derivation rule for `requires_approval`/`enabled_for_llm` above is a
reasonable default consistent with the plan's "Safe defaults" (dangerous/admin tiers require approval)
but is explicitly a judgment call for this step — requirement 08 (the actual `/reload` consumer) may
refine it; leave a comment noting this is provisional.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/shared/runtime_tool_registry.py && uv run ruff check scripts/shared/runtime_tool_registry.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/runtime_tool_registry.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — confirms no `agent`/`db`/`rag`/`mcp_servers` import (Assumptions 1-2) |
| Security | `uv run bandit -r scripts/shared/runtime_tool_registry.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | all pass (see paired test-doc) |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/shared/runtime_tool_registry.py` | no bare except |
