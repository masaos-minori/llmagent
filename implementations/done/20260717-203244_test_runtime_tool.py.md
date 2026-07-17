# Implementation procedure: `tests/shared/test_runtime_tool.py`

Source plan: `plans/done/20260717-124020_plan.md` (requirement `requires/20260717_02_require.md`), Implementation step 5.

## Goal

Create `tests/shared/test_runtime_tool.py` covering `scripts/shared/runtime_tool.py`'s `RuntimeTool`
dataclass and its `build_runtime_tool()` factory: field normalization, safe-default application, and
immutability. Confirmed via `ls tests/shared/ | grep runtime_tool` (no output) that this file does not
yet exist — it is a wholly new test file, not an extension.

## Scope

**In scope**: new file `tests/shared/test_runtime_tool.py` only, testing `runtime_tool.py` in isolation
(no registry, no MCP server, no live config).

**Out of scope**: `tests/shared/test_runtime_tool_registry.py` (separate doc), any integration test
against a running MCP server.

## Assumptions

1. Follows the conventions of the existing `tests/shared/` directory (confirmed by reading
   `tests/shared/test_tool_result_cache.py` in full, 103 lines, testing `shared/tool_cache.py`):
   - Plain absolute imports off the `shared` package, e.g. `from shared.tool_cache import ToolResultCache`
     — no `sys.path` hacks.
   - Class-based style: `class TestToolResultCache:` with plain `def test_xxx(self) -> None:` methods
     (not bare module-level functions).
   - No shared fixtures pulled from `tests/conftest.py` for `shared/`-layer tests — that conftest only
     defines generic `pytest_runtest_setup/teardown/sessionfinish` timing/logging hooks, nothing
     `shared/`-specific. Tests build their own local helper functions instead (e.g. `_ok_result`,
     `_err_result` in the reference file).
   - Assertion style: plain `assert` statements, often several per test, checking specific attributes,
     with short inline comments explaining intent where the assertion isn't self-evident.
2. `RuntimeTool` is `frozen=True` (per the paired `runtime_tool.py` doc) — mutation must raise
   `dataclasses.FrozenInstanceError` (a subclass of `AttributeError`).
3. Safe defaults under test (per `runtime_tool.py` doc's Assumption 5 / the plan's "Safe defaults"
   section): when annotation params are omitted from `build_runtime_tool()`:
   `agent_safety_tier == "WRITE_DANGEROUS"`, `requires_approval is True`, `enabled_for_llm is False`,
   `requires_serial is True` (because `is_write` was also omitted).

## Implementation

### Target file

`tests/shared/test_runtime_tool.py` (new).

### Procedure

1. Import `from shared.runtime_tool import RuntimeTool, build_runtime_tool`.
2. Add a local helper `_minimal_kwargs() -> dict[str, object]` returning the minimum required
   positional/keyword args for `build_runtime_tool()` (`name`, `server_key`), to avoid repeating
   boilerplate across tests.
3. Write `class TestRuntimeTool:` with the test methods listed in Details.

### Method

Pytest class-based tests, plain `assert`, local helper functions — matching
`tests/shared/test_tool_result_cache.py`'s established style exactly (no new pattern introduced).

### Details

Test methods (pseudocode — no production code):

```
class TestRuntimeTool:
    def test_construct_with_full_annotation(self) -> None:
        # tool = build_runtime_tool(
        #     name="delete_file", server_key="fs", server_url="http://x",
        #     description="...", input_schema={"type": "object"}, raw_definition={...},
        #     status="active", is_write=True, requires_serial=True, resource_scope="delete_file",
        #     agent_safety_tier="WRITE_DANGEROUS", requires_approval=True, enabled_for_llm=True,
        # )
        # assert tool.name == "delete_file"
        # assert tool.is_write is True
        # assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        # assert tool.enabled_for_llm is True

    def test_safe_defaults_when_unannotated(self) -> None:
        # tool = build_runtime_tool(name="unknown_tool", server_key="srv")
        # assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        # assert tool.requires_approval is True
        # assert tool.enabled_for_llm is False
        # assert tool.requires_serial is True   # because is_write was also unannotated
        # assert tool.is_write is False          # default per this doc's stated decision

    def test_requires_serial_false_when_is_write_explicitly_false(self) -> None:
        # tool = build_runtime_tool(name="read_text_file", server_key="fs", is_write=False)
        # assert tool.is_write is False
        # assert tool.requires_serial is False  # explicit is_write=False, no uncertainty

    def test_requires_serial_explicit_override_wins(self) -> None:
        # tool = build_runtime_tool(name="t", server_key="s", is_write=False, requires_serial=True)
        # assert tool.requires_serial is True  # explicit value always wins over derived default

    def test_is_frozen(self) -> None:
        # tool = build_runtime_tool(name="t", server_key="s")
        # with pytest.raises(dataclasses.FrozenInstanceError):
        #     tool.name = "changed"

    def test_input_schema_and_raw_definition_default_to_empty_dict_not_shared_object(self) -> None:
        # a = build_runtime_tool(name="a", server_key="s")
        # b = build_runtime_tool(name="b", server_key="s")
        # assert a.input_schema == {} and b.input_schema == {}
        # assert a.input_schema is not b.input_schema  # no shared mutable default
```

Do not add a runtime-validation test for invalid `agent_safety_tier` string values (e.g.
`agent_safety_tier="BOGUS"`) — per the paired `runtime_tool.py` doc's Details, the `Literal` type is
enforced statically (mypy) only, not at runtime by the dataclass; a test asserting a raise there would
fail against the intended implementation. If a runtime guard is added later, add the test then.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Run tests | `uv run pytest tests/shared/test_runtime_tool.py -v` | all pass |
| Lint | `uv run ruff check tests/shared/test_runtime_tool.py` | 0 errors |
| Type check | `uv run mypy tests/shared/test_runtime_tool.py` | 0 errors (tests/ is covered by pre-commit's mypy run per `rules/coding.md`) |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥90% on changed lines |
