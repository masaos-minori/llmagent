# Remove the ToolExecutor tool-result TTL cache

## Priority
Medium

## Summary
Remove `ToolExecutor`'s internal TTL+LRU tool-result cache (`_cache`, `_execute_with_cache`,
`_store_and_evict`, `stat_cache_hits`, `clear_cache()`, the `cache_ttl`/`cache_max_size`
constructor parameters, and `apply_config(cache_ttl=...)`), so that `execute()` always
re-executes non-side-effecting tools instead of returning a cached result.

## Background
Three follow-up issues already exist that assume this removal has landed, but no issue or
plan proposing the removal itself was ever filed — this is that missing prerequisite issue:

- `issues/done/20260825_cfgreload_toolexecutor_cache_wiring_issue.md` — remove
  `ConfigReloadService`'s dead `tools.apply_config(cache_ttl=...)` wiring once this cache is
  gone (its corresponding Plan, `plans/done/20260825-142436_plan.md`, is `Blocked` pending
  this issue).
- `issues/done/20260825_config_validators_dead_cache_validator_issue.md` — remove
  `validate_tool_cache_max_size` once `ToolConfig.tool_cache_max_size` is gone (its Plan,
  `plans/done/20260825-142646_plan.md`, is also `Blocked` pending this issue).
- `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md` — update 14 docs that
  describe this cache once it is removed (its Plan, `plans/done/20260825-142943_plan.md`,
  is also `Blocked` pending this issue).

Separately, `issues/done/20260821_09_issue.md` flagged that `ToolResultCache`
(`scripts/shared/tool_cache.py`, LRU+TTL) sits unused alongside `ToolExecutor`'s own
internal cache — two coexisting cache implementations, only one of which is wired in. That
issue proposed *unifying or documenting* the two, not removing either; it is a separate,
narrower issue and is not superseded by this one (see Out of Scope).

## Problem
Confirmed by direct reading of `scripts/shared/tool_executor.py` (2026-08-27):
- `__init__` takes `cache_ttl: float` and `cache_max_size: int = 0`, and sets
  `self._cache: OrderedDict[str, CacheEntry] = OrderedDict()`,
  `self._cache_ttl`, `self._cache_max_size`, `self.stat_cache_hits: int = 0`.
- `_execute_with_cache()` checks `self._cache` for a fresh (non-expired) entry, returns it as
  a `source="cache"` result and increments `stat_cache_hits` on hit; on miss it calls
  `_execute_with_stampede_protection()` and then `_store_and_evict()` stores the result and
  evicts the LRU entry if `_cache_max_size` is exceeded.
- `execute()` routes every non-side-effecting tool call through `_execute_with_cache()`
  (side-effecting tools already bypass it via `is_side_effect()`).
- `apply_config(self, *, cache_ttl: float | None = None)` lets `/reload` update the TTL live.
- `clear_cache()` clears `self._cache`.
- `from shared.tool_cache import CacheEntry` is imported only for this cache's own storage
  shape.
- `scripts/agent/commands/cmd_config_stats.py:84` reads `stat_cache_hits` off the tools
  service to print a `Cache hits` line in `/stats` output — a caller of this cache outside
  `tool_executor.py` itself that the three follow-up issues do not name.
- `_execute_with_stampede_protection()` (shares an inflight `asyncio.Future` per `cache_key`
  across concurrent callers) is called *from inside* `_execute_with_cache()`, but does not
  itself read or write `self._cache` — it only tracks in-flight execution via a separate
  `self._inflight` dict. It is invoked with a `cache_key` string derived the same way the
  cache does (`f"{tool_name}:{_json_dumps(args)}"`), but is structurally independent of the
  cache's storage/TTL/eviction logic. See Unresolved Questions — whether this stampede
  protection should be removed alongside the cache, or kept as an independent mechanism, is
  not resolved by this issue.

## Reason for Change
Three already-filed follow-up issues (and their corresponding Plans, all currently `Blocked`)
depend on this cache no longer existing before they can proceed. Landing this removal unblocks
all three. Separately, per `issues/done/20260821_09_issue.md`, removing this cache also
resolves the two-cache-implementations ambiguity in the cache's own favor (nothing consumes
`ToolResultCache` either way, but at least one fewer implementation exists to reason about).

This issue does not independently establish a functional/performance reason to remove tool
result caching — no such evidence was found during investigation. The removal is driven by
the three already-approved follow-up issues' shared assumption; if that assumption is
reconsidered, this issue and its three dependents should be reconsidered together (see
Unresolved Questions).

## Implementation Intent
Remove the cache storage, lookup, and eviction logic from `ToolExecutor` entirely — do not
replace it with a different cache implementation (e.g. do not redirect to `ToolResultCache`;
that is the separate, narrower unification-or-documentation issue,
`issues/done/20260821_09_issue.md`, not this one). `execute()` should call the tool's
execution path directly for every non-side-effecting tool, the same way it already does for
side-effecting tools, preserving whatever concurrency-safety behavior (stampede protection)
is decided to be in scope (see Unresolved Questions). Remove the now-dead `cache_ttl`/
`cache_max_size` configuration surface and the `Cache hits` stat output end-to-end, not just
at the `ToolExecutor` boundary.

## Target Files or Areas
- `scripts/shared/tool_executor.py` — primary removal target (see Required Changes).
- `scripts/agent/config_dataclasses.py` — `ToolConfig.tool_cache_ttl` / `tool_cache_max_size`
  fields (the config-side counterpart of the constructor parameters being removed; distinct
  from `validate_tool_cache_max_size`'s own removal, which
  `issues/done/20260825_config_validators_dead_cache_validator_issue.md` already covers).
- `scripts/agent/commands/cmd_config_stats.py` — the `Cache hits` stat line (line 84).
- `scripts/agent/factory.py` (or wherever `ToolExecutor` is constructed) — the
  `cache_ttl=`/`cache_max_size=` call-site arguments.
- Test files constructing `ToolExecutor` with `cache_ttl=`/asserting `stat_cache_hits`:
  `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`,
  `tests/shared/test_tool_executor_order.py`, `tests/shared/test_tool_executor_stampede.py`,
  `tests/shared/test_stampede_protection_cascade.py` — confirm this list with a fresh
  `rg -n "cache_ttl|cache_max_size|stat_cache_hits|clear_cache" tests/` at implementation
  time, since it may have drifted since 2026-08-27.

## Required Changes
- Remove `self._cache`, `self._cache_ttl`, `self._cache_max_size`, `self.stat_cache_hits`
  from `ToolExecutor.__init__`, and the `cache_ttl`/`cache_max_size` parameters themselves.
- Remove `_execute_with_cache()` and `_store_and_evict()`.
- Remove the `CacheEntry` import (`from shared.tool_cache import CacheEntry`) — confirm no
  other symbol from `shared.tool_cache` is still used in this file before removing the whole
  import line.
- Remove `clear_cache()`.
- Remove the `cache_ttl` parameter from `apply_config()` — if `apply_config()` has no other
  parameters left afterward, decide whether to remove the method entirely or keep it as a
  no-op for callers (see `issues/done/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`,
  which already anticipates this exact question for its own `ConfigReloadService` call site).
- Update `execute()` so non-side-effecting tools call the tool's execution path directly
  (preserving the decision from Unresolved Questions about stampede protection), instead of
  routing through `_execute_with_cache()`.
- Remove `ToolConfig.tool_cache_ttl` / `tool_cache_max_size` from `config_dataclasses.py`
  (coordinate with `issues/done/20260825_config_validators_dead_cache_validator_issue.md`,
  which removes the validator that reads `tool_cache_max_size` — that issue's Constraints
  section already states it "must land together with" this cache-removal change).
- Remove the `Cache hits` line from `cmd_config_stats.py`'s `/stats` output.
- Remove the `cache_ttl=`/`cache_max_size=` arguments wherever `ToolExecutor` is constructed
  in production code.
- Update or remove the cache-specific tests in the files listed under Target Files, per
  Testing Expectations.

## Constraints
- Must not change `is_side_effect()`-based routing — side-effecting tools already bypass the
  cache and must continue to always re-execute.
- Whatever concurrency-safety guarantee `_execute_with_stampede_protection()` currently
  provides for non-side-effecting tools must either be explicitly preserved or explicitly
  and consciously dropped — not silently lost as a side effect of deleting
  `_execute_with_cache()` (see Unresolved Questions).
- Must land together with, or immediately unblock, the three already-filed follow-up issues'
  Plans (`plans/done/20260825-142436_plan.md`, `plans/done/20260825-142646_plan.md`,
  `plans/done/20260825-142943_plan.md`) — do not implement this issue and leave those three
  Blocked Plans stale; re-run their own `rg` preconditions once this lands.

## Acceptance Criteria
- `rg -n "cache_ttl|cache_max_size|stat_cache_hits|CacheEntry" scripts/shared/tool_executor.py`
  returns no matches.
- `rg -n "tool_cache_ttl|tool_cache_max_size" scripts/agent/config_dataclasses.py` returns no
  matches.
- `cmd_config_stats.py`'s `/stats` output no longer includes a `Cache hits` line.
- `ToolExecutor.execute()` still bypasses re-execution correctly for side-effecting tools
  (`is_side_effect()` routing unchanged) and no longer returns a `source="cache"` result for
  any tool.
- The concurrency-safety decision from Unresolved Questions (keep or remove stampede
  protection) is implemented consistently — not partially removed.
- All three follow-up issues' Blocked Plans can proceed past their own precondition checks
  (`rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns nothing, etc.).

## Testing Expectations
- Full regression run of `tests/shared/test_tool_executor*.py` and
  `tests/shared/test_stampede_protection_cascade.py` — cache-hit/eviction/TTL-specific test
  cases must be removed (they test behavior that no longer exists), not left failing.
- If stampede protection is kept, add or retain a regression test proving concurrent calls to
  the same tool+args still share one execution (not one per caller) — do not lose this
  coverage silently if `_execute_with_cache()`'s removal also removes its only test coverage.
- `uv run pytest tests/shared/ tests/agent/commands/test_cmd_config_stats*.py -v` (adjust the
  exact `cmd_config_stats` test file name — confirm it at implementation time) with no new
  failures.
- Full `rules/toolchain.md` Standard validation sequence (ruff, mypy, lint-imports, ast-grep
  constraint checks, bandit, full pytest, diff-cover ≥ 90%, pre-commit).

## Documentation Impact
Covered entirely by `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md` (14
files) — no additional doc work is created by this issue beyond what that issue already
scopes, except: that issue's file list should be re-verified against
`cmd_config_stats.py`'s `Cache hits` removal (Required Changes above) in case any doc
describes that specific `/stats` line and was missed by that issue's original grep sweep.

## Out of Scope
- Unifying with or wiring in `ToolResultCache` (`scripts/shared/tool_cache.py`) — that is
  `issues/done/20260821_09_issue.md`'s separate, narrower scope (unify or document, not
  remove); this issue removes `ToolExecutor`'s own cache outright and does not touch
  `ToolResultCache`.
- Any change to `is_side_effect()` or the side-effecting-tool bypass logic itself.
- Implementing the three follow-up issues themselves
  (`cfgreload_toolexecutor_cache_wiring`, `config_validators_dead_cache_validator`,
  `docs_tool_cache_removal_stale_docs`) — this issue only removes the prerequisite cache;
  their own Plans (already drafted and `Blocked`) cover their specific follow-up work.
- Any change to `_raw_execute()`'s own execution/transport logic beyond how it is reached
  (i.e., no change to how a tool call actually dispatches to its MCP server).

## Dependencies
- Blocks (once filed and a Plan is generated from it): the three already-`Blocked` Plans
  `plans/done/20260825-142436_plan.md`, `plans/done/20260825-142646_plan.md`,
  `plans/done/20260825-142943_plan.md` — all three were generated from issues that assume
  this cache is already gone.
- Related, not blocking: `issues/done/20260821_09_issue.md` (separate `ToolResultCache`
  unification/documentation question — becomes largely moot for the `ToolExecutor` side once
  this issue lands, since there will be no second cache to unify with).

## Unresolved Questions
- **Stampede protection disposition (blocking for implementation, not for filing this
  issue)**: `_execute_with_stampede_protection()` is structurally separable from the cache
  itself (it never reads/writes `self._cache`), but is only ever invoked from inside
  `_execute_with_cache()` today, and the already-filed
  `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md` explicitly describes
  the target end state as "identical concurrent calls now each hit the MCP server (stampede
  protection removed)" — i.e., that issue assumes stampede protection is removed together
  with the cache. This issue does not resolve which is correct: keeping
  `_execute_with_stampede_protection()` as an independent concurrency guard (contradicting
  the docs issue's assumption), or removing it too (matching that issue, but removing a
  currently-tested concurrency-safety property with no cache-specific justification). A
  maintainer decision is needed before implementation proceeds; whichever is chosen,
  `issues/done/20260825_docs_tool_cache_removal_stale_docs_issue.md`'s wording may need a
  one-line correction if the decision contradicts its stated assumption.
- No functional/performance motivation for removing tool-result caching itself (as opposed to
  the three follow-up issues' shared precondition) was found during investigation — if such a
  motivation exists, it was not discovered in `issues/`, `requires/`, or `plans/` (including
  `done/` subdirectories) as of 2026-08-27. Recorded here rather than invented in Reason for
  Change.

## AI Implementation Instruction
Read `scripts/shared/tool_executor.py` in full before starting, and re-run every `rg` search
cited in this issue (line numbers and file lists may have drifted since 2026-08-27). Resolve
the stampede-protection Unresolved Question explicitly (state the decision and its rationale
in the implementation procedure) before touching `execute()` — do not silently drop or
silently keep the concurrency guard without recording the choice. Do not implement the three
follow-up issues' own scopes as part of this one; only remove the cache they depend on being
gone. Keep the change confined to the files listed under Target Files; do not perform
unrelated cleanup in `tool_executor.py` while here.
