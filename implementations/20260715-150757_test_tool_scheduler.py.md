# Implementation Procedure: tests/test_tool_scheduler.py

Source plan: `plans/20260715-133548_plan.md`

## Goal

Lock in the corrected `write_first` serialization behavior: update the one
existing assertion that encoded the old (unsafe) `serialize_flags=[False]`
behavior, and add regression tests proving (a) `write_first` batches are now
serialized and (b) that serialization does not leak into unrelated
concurrent batches.

## Scope

**In scope:**
- Update `TestConcurrentGroups.test_write_first_gets_own_sequential_batch` to
  additionally assert `serialize_flags == [True]` on the `write_first` batch.
- Add `test_write_first_group_is_serialized`: multiple no-scope write tools
  in one call → the batch containing them has `serialize_flags == [True]`.
- Add `test_fts_rebuild_does_not_serialize_unrelated_reads`: a
  `requires_serial=True` tool (e.g. `fts_rebuild`) alongside unrelated
  parallel read tools does not force those reads into a serialized batch
  (guards the plan's "Risks" item about `requires_serial` barrier scope).

**Out of scope:**
- No change to `TestSerialBarrier`, `TestResourceScope`, or any other test
  class in this file.
- No change to test helper functions (`_tc`, `_meta`) unless they lack a
  parameter needed by the new tests (check first; extend minimally only if
  required).

## Assumptions

- Depends on `implementations/20260715-150757_tool_scheduler.py.md` being
  applied first (`write_first` batch must actually have
  `serialize_flags=[True]` for these assertions to pass).
- The existing `_meta()` test helper already supports constructing a
  `ToolSpec`-shaped metadata dict with `is_write=True` and no
  `resource_scope`; reuse it as-is (confirmed by reading
  `test_write_first_gets_own_sequential_batch`, which already uses this
  shape).
- `requires_serial=True` tools already produce one-element `ScheduledBatch`
  entries via the `for tc in serial_barrier:` loop, each independent of the
  `has_concurrent` batch — this is existing, unmodified behavior; the new
  test only needs to assert this remains true after the `write_first` fix
  (it is unrelated to the one-line change but was flagged as an unmitigated
  assumption worth locking with a test in the plan's Risks section).

## Implementation

### Target file

`tests/test_tool_scheduler.py`

### Procedure

1. Locate `class TestConcurrentGroups` (currently starting at line 237).
2. Locate `test_write_first_gets_own_sequential_batch` (currently lines
   278-290).
3. Add one assertion line to that test (do not remove or alter the existing
   two assertions).
4. Add `test_write_first_group_is_serialized` as a new method in the same
   class, after `test_write_first_gets_own_sequential_batch`.
5. Add `test_fts_rebuild_does_not_serialize_unrelated_reads` as a new method
   in the same class (or `TestSerialBarrier` if that fits the file's existing
   grouping convention better — check the class docstring/grouping rationale
   before deciding; default to `TestConcurrentGroups` since it exercises
   `concurrent_groups` shape).

### Method

Additive test-only edit. Reuse the existing `_tc(name)` and
`_meta(resource_scope=..., is_write=..., requires_serial=...)` helper
functions already defined in this test module — do not duplicate their logic
inline.

### Details

Updated existing test (added line marked `# NEW`):

```python
def test_write_first_gets_own_sequential_batch(self) -> None:
    tc_write = _tc("write_file")
    tc_read = _tc("read_text_file")
    _groups, metadata = build_execution_groups(
        [tc_write, tc_read],
        {
            "write_file": _meta(resource_scope="", is_write=True),
            "read_text_file": _meta(),
        },
    )
    # write_first and parallel must be in separate batches
    assert len(metadata.concurrent_groups) == 2
    assert metadata.concurrent_groups[0].groups == [[tc_write]]
    assert metadata.concurrent_groups[0].serialize_flags == [True]  # NEW
```

New test — multiple write_first tools must serialize:

```python
def test_write_first_group_is_serialized(self) -> None:
    tc_write_a = _tc("write_file")
    tc_write_b = _tc("delete_file")
    _groups, metadata = build_execution_groups(
        [tc_write_a, tc_write_b],
        {
            "write_file": _meta(resource_scope="", is_write=True),
            "delete_file": _meta(resource_scope="", is_write=True),
        },
    )
    write_first_batch = metadata.concurrent_groups[0]
    assert write_first_batch.groups == [[tc_write_a, tc_write_b]]
    assert write_first_batch.serialize_flags == [True]
```

New test — serial barrier does not widen to unrelated reads:

```python
def test_fts_rebuild_does_not_serialize_unrelated_reads(self) -> None:
    tc_rebuild = _tc("fts_rebuild")
    tc_read_a = _tc("search_docs")
    tc_read_b = _tc("get_chunk")
    _groups, metadata = build_execution_groups(
        [tc_rebuild, tc_read_a, tc_read_b],
        {
            "fts_rebuild": _meta(requires_serial=True, is_write=True),
            "search_docs": _meta(),
            "get_chunk": _meta(),
        },
    )
    # fts_rebuild gets its own one-element sequential batch...
    barrier_batch = metadata.concurrent_groups[0]
    assert barrier_batch.groups == [[tc_rebuild]]
    # ...while the two read tools remain gathered together in a later,
    # non-serialized batch, unaffected by the barrier.
    read_batch = metadata.concurrent_groups[-1]
    assert tc_read_a in read_batch.groups[-1]
    assert tc_read_b in read_batch.groups[-1]
    assert read_batch.serialize_flags[-1] is False
```

If `_meta()` does not currently accept `requires_serial` as a keyword, check
its definition first and extend it minimally (single new optional parameter,
default preserving current behavior) rather than constructing `ToolSpec`
inline.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-150757_tool_scheduler.py.md` applied first | `write_first` batch actually has `serialize_flags=[True]` |
| Format/lint | `uv run ruff format tests/test_tool_scheduler.py && uv run ruff check tests/test_tool_scheduler.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_scheduler.py` (mypy also covers `tests/` per `pyproject.toml`) | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_scheduler.py -v` | All pass, including the 3 new/updated assertions |
| Full suite | `uv run pytest -v` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
