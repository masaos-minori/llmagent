# Implementation: tests/test_mdq_index_serialization.py (new — proof that `_index_lock` serializes concurrent `index_paths`/`refresh_index` calls)

Source plan: `plans/20260716-131759_plan.md`

## Goal

Add a deterministic concurrency test proving `MdqService._index_lock`
actually prevents interleaved execution of overlapping `index_paths`/
`refresh_index` calls — no such test exists today.

## Scope

**In:**
- Create `tests/test_mdq_index_serialization.py` with at least one
  deterministic test that starts two overlapping `refresh_index` (or
  `index_paths`) calls via `asyncio.gather` and asserts they do not
  interleave — i.e., the second call's critical section does not begin
  before the first's ends.

**Out:**
- Any change to `MdqService.index_paths()`/`refresh_index()` themselves —
  this plan's Assumption 4 confirms both already correctly acquire
  `self._index_lock`; this is a test-only addition, no production code
  change.
- Testing `requires_serial` at the `tools.py`/`ToolScheduler` level — that
  is a distinct, already-existing mechanism (`scripts/agent/tool_scheduler.py`)
  operating across concurrent tool calls within one agent turn, not the
  in-process `MdqService._index_lock` this test targets. Per the source
  plan's Assumption 5, both are legitimate and complementary; this test
  covers only the `MdqService`-internal lock.

## Assumptions

1. `MdqService.index_paths()` and `refresh_index()` both acquire
   `self._index_lock` (lazily created `asyncio.Lock`) before running,
   confirmed by direct read of `service.py:319-342`:
   ```python
   async def index_paths(self, req: IndexPathsRequest) -> str:
       if self._index_lock is None:
           self._index_lock = asyncio.Lock()
       async with self._index_lock:
           self._is_indexing = True
           try:
               result: str = await _index_paths(self, req)
               return result
           finally:
               self._is_indexing = False

   async def refresh_index(self, req: RefreshIndexRequest) -> str:
       if self._index_lock is None:
           self._index_lock = asyncio.Lock()
       async with self._index_lock:
           self._is_indexing = True
           try:
               self._validate_paths(req.paths)
               summary = await _refresh_paths(self, req)
               return "\n".join(self._format_refresh_summary(summary))
           finally:
               self._is_indexing = False
   ```
2. A bare `asyncio.sleep`-based race would be flaky (per the source plan's
   own Risks section) — the test must use a deterministic hook (a
   monkeypatched delay inside the locked critical section, or an explicit
   order-tracking list combined with `asyncio.gather`) rather than relying
   on real-time scheduling timing.
3. The simplest deterministic approach: monkeypatch (or wrap) the
   underlying `_refresh_paths`/`_index_paths` call so it appends to a
   shared `order` list before and after an `await asyncio.sleep(0.05)` (a
   short, fixed delay only to force a scheduling yield point inside the
   lock, not to race against it) — since both calls share the same
   `_index_lock`, the second call cannot enter its own critical section
   until the first releases the lock, so the recorded order must be
   `["start", "end", "start", "end"]`, never
   `["start", "start", "end", "end"]`.

## Implementation

### Target file

`tests/test_mdq_index_serialization.py` (new file)

### Procedure

1. Create `tests/test_mdq_index_serialization.py` with a module docstring
   describing its purpose (proof that `MdqService._index_lock` serializes
   overlapping index/refresh operations).
2. Add imports:
   ```python
   from __future__ import annotations

   import asyncio
   from pathlib import Path

   import pytest
   from mcp_servers.mdq.mdq_models import RefreshIndexRequest
   from mcp_servers.mdq.mdq_service import MdqService
   ```
3. Reuse the `service`/`md_file` fixture pattern already established in
   `tests/test_mdq_service.py:36-55` (temp DB, `tmp_path` in
   `_allowed_dirs`, a small Markdown file) — duplicate the fixtures in this
   new file per this test suite's existing per-file fixture convention
   (confirmed in the other new-test docs for this batch of plans).
4. Add a deterministic serialization test, e.g.:
   ```python
   @pytest.mark.asyncio
   async def test_concurrent_refresh_calls_are_serialized(
       service: MdqService, md_file: Path, monkeypatch: pytest.MonkeyPatch
   ) -> None:
       order: list[str] = []
       original = service._index_lock  # noqa: SLF001 -- accessing internal lock is the point of this test

       async def tracked_refresh() -> str:
           order.append("start")
           try:
               result = await service.refresh_index(
                   RefreshIndexRequest(paths=[str(md_file.parent)])
               )
           finally:
               order.append("end")
           return result

       # Force a scheduling yield inside the locked section so two concurrent
       # calls would interleave if the lock did not actually serialize them.
       import mcp_servers.mdq.service as service_module  # noqa: PLC0415

       original_refresh_paths = service_module._refresh_paths

       async def slow_refresh_paths(svc, req):  # type: ignore[no-untyped-def]
           await asyncio.sleep(0.05)
           return await original_refresh_paths(svc, req)

       monkeypatch.setattr(service_module, "_refresh_paths", slow_refresh_paths)

       await asyncio.gather(tracked_refresh(), tracked_refresh())

       assert order == ["start", "end", "start", "end"]
   ```
   (Adjust the exact monkeypatch target/mechanism during implementation to
   match whatever import path `service.py` actually uses for
   `_refresh_paths` — verify via `grep -n "_refresh_paths"
   scripts/mcp_servers/mdq/service.py` before finalizing the patch target;
   the source plan's Design section explicitly leaves "exact assertion
   mechanics to be finalized during implementation.")
5. Add a return-type annotation (`-> None`) and module/function docstrings
   per this test suite's existing conventions.

### Method

New pytest module using a monkeypatched delay inside the critical section
plus an order-tracking list — deterministic (no real-time race), directly
exercising the production `_index_lock` (no mocking of the lock itself).

### Details

- Do not mock `self._index_lock` itself — the test must exercise the real
  lock object to prove actual serialization, only the slow inner call is
  monkeypatched to force a yield point.
- If `pytest-asyncio` is not already configured for this test suite, check
  `tests/test_mdq_service.py` (or `pyproject.toml`'s `[tool.pytest.ini_options]`)
  for the existing async-test convention (marker vs. `asyncio_mode`
  config) and follow it exactly rather than introducing a second
  convention.
- Keep the `# noqa: SLF001` (or equivalent) justification inline per
  `rules/coding.md`'s suppression-governance rule if accessing a
  privately-named attribute (`_index_lock`) triggers a lint rule.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New test passes | `uv run pytest tests/test_mdq_index_serialization.py -v` | passes, deterministically (run multiple times to rule out flakiness) |
| Flakiness check | `uv run pytest tests/test_mdq_index_serialization.py -v --count=10` (if `pytest-repeat` is available) or manual repeated runs | consistently passes |
| Lint | `uv run ruff check tests/test_mdq_index_serialization.py` | 0 errors (any `# noqa` has inline justification) |
| Type check | `uv run mypy tests/test_mdq_index_serialization.py` | no new errors |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass |
