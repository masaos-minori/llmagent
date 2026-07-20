# Implementation: tests/test_mdq_index_serialization.py (expand — index_paths serialization + _is_indexing visibility)

Source plan: `plans/20260719-212007_plan.md` ("Expand MDQ concurrency and boundary guardrail tests")

## Goal

Extend the existing `tests/test_mdq_index_serialization.py` (currently one test,
`test_concurrent_refresh_calls_are_serialized`, proving `refresh_index`×`refresh_index`
serialization) with three new test cases that prove:

1. `index_paths`×`index_paths` calls also serialize through `MdqService._index_lock`.
2. A mixed `index_paths`×`refresh_index` pair also serializes (no interleaving regardless
   of which side wins the race).
3. `search_docs()` surfaces the `_is_indexing` warning suffix while an `index_paths` call
   is still in flight (an existing behavior, `mdq_service.py` lines 129-136, that has no
   test today).

No production behavior changes — test-only additions, reusing the existing file's
fixtures and monkeypatch technique unchanged.

## Scope

**In:**
- Add `test_concurrent_index_paths_calls_are_serialized` to
  `tests/test_mdq_index_serialization.py`.
- Add `test_index_paths_and_refresh_index_are_serialized` to the same file.
- Add `test_is_indexing_warning_visible_during_active_index` to the same file.

**Out:**
- Any change to `MdqService._index_lock`, `index_paths`, `refresh_index`, or
  `_is_indexing` runtime logic.
- Any change to `service`/`md_file` fixtures — reused as-is.
- `tests/test_mdq_tool_layer_consistency.py` / `tests/test_tool_server_layer_consistency.py`
  — out of scope per the source plan's Scope/UNK-01.

## Assumptions

1. The live target module is `scripts/mcp_servers/mdq/mdq_service.py` (imports
   `index_paths as _index_paths` and `refresh_paths as _refresh_paths` from
   `mcp_servers.mdq.indexer` at lines 20-27 of `mdq_service.py`). The existing test in
   this file already monkeypatches `mcp_servers.mdq.mdq_service._refresh_paths` (see
   current file, line 56-68) — the new tests follow the identical import/monkeypatch
   target convention (`import mcp_servers.mdq.mdq_service as service_module`, then
   `monkeypatch.setattr(service_module, "_index_paths", ...)` and/or `"_refresh_paths"`).
2. `MdqService.index_paths()` (lines 253-263) and `refresh_index()` (lines 265-276) both
   lazily create `self._index_lock` (`asyncio.Lock | None`, line 91) and both set
   `self._is_indexing = True`/`False` around the call (lines 258/263, 270/276) — confirmed
   by direct read of the current file. Both hold the *same* lock instance, so any pairing
   of the two methods against one shared `service` fixture instance serializes correctly.
3. `search_docs()` (lines 129-136) appends the exact substring
   `"[WARNING: Index is being updated — results may be incomplete]"` to its result when
   `self._is_indexing` is `True` at the time it returns — confirmed by direct read.
4. `IndexPathsRequest` (imported from `mcp_servers.mdq.mdq_models`, confirmed at
   `mdq_models.py` line 122) takes a `paths: list[str]` field, matching the existing
   `RefreshIndexRequest` shape already imported and used in this file.
5. `asyncio.gather` + a monkeypatched `asyncio.sleep(0.05)` inside the protected section
   (the exact mechanism used by the existing `test_concurrent_refresh_calls_are_serialized`)
   is deterministic enough to avoid flakiness — no new fixture or timing pattern is
   introduced; the new tests are structural clones of the existing one.

## Implementation

### Target file

`tests/test_mdq_index_serialization.py` (existing file, currently 76 lines, one test
function plus the `service`/`md_file` fixtures — extend, do not rewrite).

### Procedure

1. Keep the existing module docstring, imports, and `service`/`md_file` fixtures
   unchanged. Do not duplicate fixture definitions.
2. Add `test_concurrent_index_paths_calls_are_serialized` directly after the existing
   `test_concurrent_refresh_calls_are_serialized` function.
3. Add `test_index_paths_and_refresh_index_are_serialized` after that.
4. Add `test_is_indexing_warning_visible_during_active_index` after that.
5. No changes to imports are required beyond what the existing file already imports
   (`asyncio`, `Path`, `pytest`, `RefreshIndexRequest`, `MdqService`) plus one new import:
   `IndexPathsRequest` from `mcp_servers.mdq.mdq_models` (add to the existing
   `from mcp_servers.mdq.mdq_models import RefreshIndexRequest` line, making it
   `import RefreshIndexRequest, IndexPathsRequest` — keep isort/ruff `I`-rule ordering,
   i.e. alphabetical: `IndexPathsRequest, RefreshIndexRequest`).

### Method

Structural clone of the existing `test_concurrent_refresh_calls_are_serialized`: an
`order: list[str]` accumulator, a monkeypatched wrapper around the protected indexer
function(s) that appends `"start"`/`"end"` around an `await asyncio.sleep(0.05)`, two
concurrent calls via `asyncio.gather` (driven through `asyncio.run(_run_both())` matching
the existing file's non-`pytest.mark.asyncio` style — this file does not use the
`pytest.mark.asyncio` decorator; it wraps the gather in a plain sync test function that
calls `asyncio.run(...)` internally, per the current `test_concurrent_refresh_calls_are_serialized`
body), then an assertion on the recorded order.

### Details

**`test_concurrent_index_paths_calls_are_serialized`:**
- Signature: `def test_concurrent_index_paths_calls_are_serialized(service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
- Define `tracked_index() -> str` (async) that calls
  `await service.index_paths(IndexPathsRequest(paths=[str(md_file.parent)]))`.
- Monkeypatch `mcp_servers.mdq.mdq_service._index_paths` (not `_refresh_paths`) with a
  `slow_index_paths` wrapper that appends `"start"`/`"end"` to `order` around
  `await asyncio.sleep(0.05)` then delegates to the original `_index_paths`.
- Run `asyncio.gather(tracked_index(), tracked_index())` inside a `_run_both()` helper
  invoked via `asyncio.run(...)`.
- Assert `order == ["start", "end", "start", "end"]`.

**`test_index_paths_and_refresh_index_are_serialized`:**
- Signature: `def test_index_paths_and_refresh_index_are_serialized(service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
- Monkeypatch *both* `_index_paths` and `_refresh_paths` on `mcp_servers.mdq.mdq_service`
  with slow wrappers appending to the same shared `order` list (each wrapper's own
  `asyncio.sleep(0.05)` before delegating to its captured original function), so either
  operation may legitimately run first.
- Define `tracked_index()` calling `service.index_paths(IndexPathsRequest(...))` and
  `tracked_refresh()` calling `service.refresh_index(RefreshIndexRequest(...))`, each using
  the same `md_file.parent` path.
- Run `asyncio.gather(tracked_index(), tracked_refresh())` via `asyncio.run(...)`.
- Do NOT assert a fixed op ordering (either may go first). Instead assert structurally
  that the two operations never interleaved:
  - `order.count("start") == 2` and `order.count("end") == 2`.
  - For each pair, `"end"` immediately follows its matching `"start"` at the next index —
    concretely: `assert order[0] == "start" and order[1] == "end" and order[2] == "start" and order[3] == "end"`,
    which is satisfiable regardless of which underlying function (`_index_paths` vs
    `_refresh_paths`) produced which pair, because both wrappers append to the same list
    under the same lock.

**`test_is_indexing_warning_visible_during_active_index`:**
- Signature: `async def test_is_indexing_warning_visible_during_active_index(service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  decorated with `@pytest.mark.asyncio` (this test needs to interleave a background task
  with a foreground `await`, unlike the two gather-based tests above, so it uses the
  async-test style rather than `asyncio.run` wrapping).
- Monkeypatch `mcp_servers.mdq.mdq_service._index_paths` with a wrapper that does
  `await asyncio.sleep(0.05)` before delegating to the original — long enough to
  guarantee `_is_indexing` is still `True` across the following single `await asyncio.sleep(0)` tick.
- `task = asyncio.create_task(service.index_paths(IndexPathsRequest(paths=[str(md_file.parent)])))`.
- `await asyncio.sleep(0)` (single event-loop tick, per the source plan's Design/Risks
  section) to let `index_paths` acquire the lock and set `self._is_indexing = True` before
  proceeding.
- `result = await service.search_docs(SearchDocsRequest(query="Title"))` (import
  `SearchDocsRequest` from `mcp_servers.mdq.mdq_models` — add to the same import line;
  check the actual required fields of `SearchDocsRequest` in `mdq_models.py` before
  finalizing, since this file does not currently import or use it).
- Assert `"[WARNING: Index is being updated" in result`.
- `await task` at the end to drain the background task and avoid an unawaited-task
  warning (per source plan's Risks section).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/test_mdq_index_serialization.py -v` | all pass (1 existing + 3 new) |
| Flakiness check | run the file 3 times locally: `for i in 1 2 3; do uv run pytest tests/test_mdq_index_serialization.py -v; done` | consistent pass every run |
| Lint | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` (tests/ covered by pre-commit's mypy run) | no new errors |
| Regression | `uv run pytest tests/test_mdq_tool_layer_consistency.py tests/test_tool_server_layer_consistency.py -v` | unchanged, all pass |
| Full suite | `uv run pytest -v` | no new failures |
