# Implementation: tests/test_tool_scheduler_serialization.py — DAG serialization tests

## Goal

Add tests covering all serialization cases: same-scope write calls are sequential, different-scope calls are concurrent, serial barrier tools are isolated, shell_run is treated as serial, write-first tools run before reads, and reads remain concurrent.

## Scope

**In**: Unit tests for `build_execution_groups()` output (`ScheduledBatch.serialize_flags`). Integration tests for `tool_runner.py` execution ordering.

**Out**: Changes to source files.

## Assumptions

1. `build_execution_groups()` returns `(groups, metadata)` where `metadata.concurrent_groups` is `list[ScheduledBatch]`.
2. `ScheduledBatch.serialize_flags[i]` is `True` when tools in `groups[i]` must run sequentially.
3. Test fixtures: `ToolSpec` instances with `resource_scope`, `is_write`, `requires_serial` set.
4. Integration tests can verify execution ordering by recording call timestamps or using `asyncio.Event`.

## Implementation

### Target file
`tests/test_tool_scheduler_serialization.py`

### Procedure
1. Write unit tests for `build_execution_groups()` output structure.
2. Write integration tests for `tool_runner.py` execution ordering.

### Method

**Unit tests (scheduler output structure):**

```python
def make_tool_call(name: str) -> dict:
    return {"function": {"name": name, "arguments": "{}"}, "id": name}

def make_spec(name, *, scope="", is_write=False, requires_serial=False):
    return ToolSpec(name=name, resource_scope=scope, is_write=is_write, requires_serial=requires_serial)

def test_same_scope_write_groups_have_serialize_true():
    tcs = [make_tool_call("write_a"), make_tool_call("write_b")]
    meta = {
        "write_a": make_spec("write_a", scope="file:/foo", is_write=True),
        "write_b": make_spec("write_b", scope="file:/foo", is_write=True),
    }
    groups, md = build_execution_groups(tcs, meta)
    # Find the batch containing the scope group
    scope_batch = next(b for b in md.concurrent_groups if b.groups and len(b.groups[0]) == 2)
    idx = scope_batch.groups.index([tcs[0], tcs[1]])  # or find by content
    assert scope_batch.serialize_flags[idx] is True

def test_read_only_group_has_serialize_false():
    tcs = [make_tool_call("read_a"), make_tool_call("read_b")]
    meta = {
        "read_a": make_spec("read_a"),
        "read_b": make_spec("read_b"),
    }
    groups, md = build_execution_groups(tcs, meta)
    read_batch = md.concurrent_groups[-1]
    assert all(not f for f in read_batch.serialize_flags)

def test_serial_barrier_runs_alone():
    tcs = [make_tool_call("shell_run")]
    meta = {"shell_run": make_spec("shell_run", requires_serial=True)}
    groups, md = build_execution_groups(tcs, meta)
    assert len(md.concurrent_groups) == 1
    assert md.concurrent_groups[0].groups == [[tcs[0]]]

def test_shell_run_treated_as_serial():
    # shell_run injected as requires_serial=True by tool_runner._build_tool_meta
    # Test via tool_runner helper or directly with requires_serial=True spec
    tcs = [make_tool_call("shell_run"), make_tool_call("read_a")]
    meta = {
        "shell_run": make_spec("shell_run", requires_serial=True),
        "read_a": make_spec("read_a"),
    }
    groups, md = build_execution_groups(tcs, meta)
    # shell_run in its own batch; read_a in parallel batch
    assert len(md.concurrent_groups) == 2

def test_write_first_runs_before_reads():
    tcs = [make_tool_call("write_x"), make_tool_call("read_a")]
    meta = {
        "write_x": make_spec("write_x", is_write=True),  # no scope
        "read_a": make_spec("read_a"),
    }
    groups, md = build_execution_groups(tcs, meta)
    # write_first batch comes before parallel batch
    assert len(md.concurrent_groups) == 2
    # First batch contains write_x
    assert tcs[0] in md.concurrent_groups[0].groups[0]

def test_different_scope_writes_run_concurrently():
    tcs = [make_tool_call("write_a"), make_tool_call("write_b")]
    meta = {
        "write_a": make_spec("write_a", scope="repo:A", is_write=True),
        "write_b": make_spec("write_b", scope="repo:B", is_write=True),
    }
    groups, md = build_execution_groups(tcs, meta)
    # Both scopes should be in the same concurrent batch
    last_batch = md.concurrent_groups[-1]
    assert len(last_batch.groups) == 2  # both scope groups in one batch

def test_serialization_event_fields():
    tcs = [make_tool_call("write_a"), make_tool_call("write_b")]
    meta = {
        "write_a": make_spec("write_a", scope="file:/foo", is_write=True),
        "write_b": make_spec("write_b", scope="file:/foo", is_write=True),
    }
    groups, md = build_execution_groups(tcs, meta)
    evt = next(e for e in md.serialization_events if e.reason == "resource_scope_conflict")
    assert evt.resource_scope == "file:/foo"
    assert evt.is_write is True
    assert evt.requires_serial is False
    assert evt.scheduling_decision == "resource_scope"
```

**Integration tests (execution order):**

Use `asyncio.Event` or `asyncio.Lock` to detect concurrent vs sequential execution:
```python
async def test_same_scope_writes_execute_sequentially(mock_ctx):
    order = []
    async def mock_execute(ctx, tc, turn):
        order.append(f"start:{tc['function']['name']}")
        await asyncio.sleep(0.01)
        order.append(f"end:{tc['function']['name']}")
        return mock_result()
    # Patch execute_one_tool_call and run tool_runner
    # Assert order is: start:write_a, end:write_a, start:write_b, end:write_b
```

## Validation plan

- `uv run pytest tests/test_tool_scheduler_serialization.py -v` — all pass.
- No external dependencies beyond `asyncio` and existing fixtures.
- `ruff check tests/test_tool_scheduler_serialization.py` — 0 errors.
- `mypy tests/test_tool_scheduler_serialization.py` — no errors.
