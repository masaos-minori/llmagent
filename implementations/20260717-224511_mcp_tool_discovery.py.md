# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (consolidation extension)

Source plan: `plans/20260717-130506_plan.md` ("Consolidate tool startup validation into MCP discovery
service", requirement `requires/20260717_09_require.md`), Implementation steps 1-5.

**Relationship to the existing doc for this file**: `implementations/20260717-203830_mcp_tool_discovery.py.md`
(requirement 03's own design for this file) is a **filename match that does not genuinely cover this
plan's scope** — flagged explicitly, not silently skipped. That doc's own "Out of scope" section states
verbatim: *"`scripts/agent/repl_health.py` — no change (plan's Design section recommends keeping the
existing drift-check fetch independent; not this doc's concern either way)."* This plan (requirement 09)
is exactly the follow-up that supersedes that deferral. This doc does not repeat requirement 03's base
scope (fetch/normalize/build-registry/duplicate-detection, already fully specified there) — it specifies
the **additive** migration: porting `check_routing_drift_vs_live()`, `check_tool_definitions_startup()`,
and `_validate_tools_response()`'s remaining logic into the same service, plus the unified severity model.
Implement both docs together against the same file.

## Goal

Extend `McpToolDiscoveryService` (as designed in `implementations/20260717-203830_mcp_tool_discovery.py.md`)
so that, within the single `discover_all()` pass it already performs, it also: (a) validates the freshly
fetched live tool lists against the static `ToolRegistry` for drift (the logic currently in
`check_routing_drift_vs_live()`, `scripts/agent/repl_health.py:351-427`), (b) reuses/absorbs
`_validate_tools_response()`'s malformed-schema checks (`repl_health.py:130-158`) — already substantially
superseded by requirement 03's own richer `_validate_and_normalize_entry()`, confirm no duplication, and
(c) absorbs `check_tool_definitions_startup()`'s logic (`repl_health.py:345-348`, a thin wrapper over the
shared `_check_tool_definitions()` helper). All of this happens during the *same* fetch loop the service
already runs — no second HTTP round-trip to any server for a duplicate validation pass.

## Scope

**In scope**
- `scripts/agent/services/mcp_tool_discovery.py`: add drift validation (vs. static `ToolRegistry`) and
  tool-definitions-startup logic into `discover_all()`'s existing pass; unify severity (strict-flag +
  security-profile) into one FATAL/WARNING scheme expressed via `StartupCheckOutcome`.
- Resolution of both of the plan's Unknowns (folded in below, in Assumptions 1-2), since both directly
  determine this file's exact boundary.

**Out of scope**
- `scripts/shared/tool_routing_validation.py` — **no change**. See Assumption 3: its only production
  caller becomes `mcp_tool_discovery.py` (a same-or-lower layer import, already legal), and
  `tests/test_tool_registry.py` (lines 83-224) unit-tests `validate_routing_against_live()` directly as a
  public function across 13+ cases. There is no import-layer reason to privatize it (unlike the
  `apply_policy()`/`config_dataclasses` case from a sibling requirement, where privatization was forced by
  the `shared`-is-leaf contract) — `tool_routing_validation.py` already lives in `shared/`, and `agent` may
  import `shared` freely per `.importlinter`. Privatizing it would break the existing public-API test
  suite for no benefit. This corrects the plan's Affected-areas-table suggestion ("becomes internal to the
  discovery service") now that Unknown #2 is resolved with evidence.
- Any change to `check_routing_drift()` (`repl_health.py:496-524`, static config-vs-registry, not live) or
  `check_routing_safety_tiers()` (`repl_health.py:527-533`) — plan explicitly excludes these; confirmed
  distinct concerns, left untouched.
- `check_tool_definitions_runtime()`'s own logic path — see Assumption 1; it keeps calling the existing
  shared `_check_tool_definitions()` helper, which is untouched by this doc.

## Assumptions

1. **Resolves plan Unknown #1** (`check_tool_definitions_runtime()` caller check): confirmed via
   `rg -n "check_tool_definitions_runtime" scripts tests` — the **only** hit in the entire repo is the
   `def` line itself (`repl_health.py:340`). It has **zero callers** anywhere (no `/mcp status` handler, no
   periodic poll, no test). Resolution: `_check_tool_definitions()` (the shared helper both
   `check_tool_definitions_runtime()` and `check_tool_definitions_startup()` call) can be treated as
   dead-adjacent from the startup path's perspective, but must **remain importable** from
   `repl_health.py` for `check_tool_definitions_runtime()` to keep working (that function itself is
   out of this plan's scope — it is not named in the plan's migration list, and removing an unused-but-
   still-defined function is not part of this requirement). `mcp_tool_discovery.py` therefore **imports and
   calls the existing `agent.repl_health._check_tool_definitions(ctx, strict=...)` helper directly**
   rather than duplicating its logic — this is the one legal cross-import back into `repl_health.py`
   this doc introduces (agent-layer module importing another agent-layer module; no `.importlinter`
   concern). `check_tool_definitions_startup()` itself (the 2-line wrapper) is what gets removed from
   `repl_health.py` (see the paired `repl_health.py` doc), not `_check_tool_definitions()`.

2. **Resolves plan Unknown #2** (`validate_routing_against_live()` caller check): confirmed via
   `rg -n "validate_routing_against_live" scripts tests` — the only production call site is
   `scripts/agent/repl_health.py:395` (inside `check_routing_drift_vs_live()`); the only other non-test,
   non-docstring reference is `tool_routing_validation.py:76` itself (`validate_all_routing()`'s internal
   call, which itself has no confirmed caller in `scripts/`/`tests/`). All other hits are
   `tests/test_tool_registry.py`'s direct unit tests of the public function. Resolution: keep
   `validate_routing_against_live()` public and unchanged (see Scope/Out-of-scope above);
   `mcp_tool_discovery.py` becomes an additional caller, alongside the now-removed `repl_health.py:395`
   call site.

3. **Current `check_routing_drift_vs_live()` body** (`repl_health.py:351-427`, confirmed by direct read)
   does exactly this, once per call: fetch already done by caller (`_collect_server_tool_names_per_server`,
   not `discover_all()` — a *second*, independent fetch today); `build_discovery_map()` for duplicate
   detection; `validate_routing_against_live(live_tool_lists=per_server)` for drift; then, in order:
   duplicate-warning logging, `if duplicates and strict: raise RuntimeError`, drift-warning logging,
   `if drift and strict: raise RuntimeError`. Porting this means: reuse `discover_all()`'s own
   `(server_key, server_url, entry)` tuples (already collected once) to build the
   `{server_key: [tool_name, ...]}` shape `validate_routing_against_live()` expects, instead of a second
   `_collect_server_tool_names_per_server()` call — this satisfies "one fetch, one service."

4. **Current severity mechanism is exception-based and has an observed quirk worth documenting explicitly**
   (confirmed via direct read of `scripts/agent/startup.py:253-266`): today, `check_routing_drift_vs_live(ctx,
   strict=strict)` is called inside a `try` whose **outer** `except Exception` (line 263) catches *any*
   exception — including the `RuntimeError` that `strict=True` deliberately raises on drift — and converts
   it to `pipeline.add_skipped("routing_drift_live", f"Live routing check skipped: {exc}")`, **not**
   `pipeline.add_fatal(...)`. So today, "strict mode" drift detection, once wired through `_check_services()`,
   surfaces as a **skipped** startup-check outcome, not a fatal one, despite the function's own docstring
   promising "strict mode: any drift raises RuntimeError." (`tests/test_startup.py:781-792`'s
   `test_routing_drift_live_skipped_on_exception` name confirms this is the currently-tested, intentional-
   as-tested behavior, not an untested accident — but it is still surprising relative to the function's own
   docstring, and is exactly the kind of "strict×profile combination" ambiguity the plan's Risk section
   asks to be resolved deliberately, not left accidental.) This doc's unified design (below) removes the
   exception-based control flow entirely, which resolves this quirk by construction — see Design section.

5. `_validate_and_normalize_entry()` (already specified in the base req-03 doc, `implementations/
   20260717-203830_mcp_tool_discovery.py.md`, Procedure step 7) already validates `name`/`description`/
   `inputSchema` shape more richly than `_validate_tools_response()`'s name-only check
   (`repl_health.py:130-158`) — confirmed by direct read of both. No additional porting work is needed for
   malformed-schema checks beyond what req-03's doc already specifies; this doc's only addition here is
   the explicit confirmation (plan step 3 is satisfied by the existing design, not new code).

## Design: unified severity scheme (plan step 5)

Replace the two independent mechanisms — `strict: bool` (raises `RuntimeError`) and `security_profile ==
PRODUCTION` (drives `StartupCheckStatus.FATAL` for duplicates, per req-03's Assumption 5) — with **one**
rule, expressed as data (`StartupCheckOutcome.status`), never as a raised exception:

```
is_fatal = strict or (security_profile == SecurityProfile.PRODUCTION)
status = StartupCheckStatus.FATAL if is_fatal else StartupCheckStatus.WARNING
```

Enumerated per the plan's Risk-mitigation instruction (4 combinations, each decision explicit):

| strict | profile | resulting status | rationale |
|---|---|---|---|
| False | local | WARNING | matches old non-strict behavior and req-03's local=warning rule |
| False | production | **FATAL** | behavior change vs. old drift mechanism (old: drift only fataled on `strict`, ignored profile) — deliberately aligned with req-03's already-established rule that duplicate-name detection fatals in production regardless of `strict`; production should fail closed on drift too, for consistency across all findings this one service now emits |
| True | local | FATAL | preserves old "strict mode raises" behavior even outside production |
| True | production | FATAL | both mechanisms already agreed |

This also resolves Assumption 4's quirk: since findings are returned as `list[StartupCheckOutcome]` (data,
not a raised exception), `startup.py`'s `_check_services()` folds each outcome via
`pipeline.add_fatal`/`pipeline.add_warning` directly from `outcome.status`, with no `try/except Exception`
needed around this check at all (see the paired `startup.py` doc) — a fatal finding cannot be silently
downgraded to "skipped" by an unrelated exception handler.

**Flag for the plan/requirement owner**: the `False, production` cell is a genuine behavior change (drift
that used to only warn in production now fatals). This must be called out during implementation review,
not silently introduced — the plan's own Risk section anticipated exactly this kind of cross-mechanism
disagreement and asked for each combination to be a deliberate choice, which this table provides.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (extends the file already specified in
`implementations/20260717-203830_mcp_tool_discovery.py.md` — do not recreate the file from scratch;
apply this doc's additions on top of that doc's base design).

### Procedure

1. Update the module docstring (added to by req-03's own doc) with one more paragraph: this service now
   also performs live-vs-registry drift validation and duplicate/malformed/tool-definition consolidation
   migrated from `repl_health.py` per requirement 09; state the unified severity rule
   (`is_fatal = strict or security_profile == PRODUCTION`) verbatim so future readers don't reintroduce
   the two-mechanism split.
2. Import additionally: `validate_routing_against_live` from `shared.tool_routing_validation`;
   `get_registry` from `shared.tool_registry`; `_check_tool_definitions` from `agent.repl_health` (see
   Assumption 1); `StartupMode`/`SecurityProfile` already available via existing imports or add
   `SecurityProfile` from `shared.mcp_config` if not already imported by the base doc.
3. Extend `DiscoveryResult` (currently `registry`, `findings`, `unreachable`) — no new fields needed;
   drift/tool-definition findings are appended to the same `findings: list[StartupCheckOutcome]` list the
   base doc already returns.
4. In `discover_all()`, after the existing `_dedupe_and_build(entries)` call: build
   `per_server: dict[str, list[str]] = {}` from the same `entries` list already accumulated during the
   fetch loop (group `(server_key, server_url, entry)` tuples by `server_key`, collecting `entry["name"]`
   per server) — no second fetch. Call `validate_routing_against_live(live_tool_lists=per_server)` to get
   `drift: dict[str, list[str]]`. Reuse `_dedupe_and_build`'s already-computed duplicate map for the
   duplicate-ownership half (already covered by the base doc's Assumption 5 exclude-and-report design) —
   do not call `build_discovery_map()` a second time; the base doc's dedup step already produces an
   equivalent duplicate-name map.
5. Add `_check_tool_definitions_finding(self) -> StartupCheckOutcome | None`: calls
   `await _check_tool_definitions(self._ctx, strict=self._is_strict())` (imported per step 2), catches
   `RuntimeError` and converts it into a `StartupCheckOutcome` with the unified severity from the Design
   section rather than letting the plain `_check_tool_definitions()` helper's own exception propagate.
6. Add `_is_strict(self) -> bool`: `return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict",
   False))` — same source as today's `startup.py:254`.
7. Compute `is_fatal = self._is_strict() or self._ctx.cfg.mcp.security_profile ==
   SecurityProfile.PRODUCTION` once per `discover_all()` call; use it for both the drift findings and to
   confirm/align with the duplicate-detection findings' existing production/local branching from the base
   doc (both must now use this single `is_fatal` value — the base doc's own severity check
   (`SecurityProfile.PRODUCTION` only, no `strict`) is superseded by this unified value; update the base
   doc's `_dedupe_and_build()` severity line to use `is_fatal` instead of re-deriving profile alone).
8. For each `server_key, messages` in `drift.items()`: emit one `StartupCheckOutcome` per server with
   `status = FATAL if is_fatal else WARNING`, `source="mcp_tool_discovery"`,
   message text ported verbatim in spirit from `repl_health.py:416` (`f"Live routing drift [{server_key}]:
   {msg}"`).
9. Append the `_check_tool_definitions_finding()` result (if not `None`) to `discover_all()`'s
   `findings` list.

### Method

Same as the base doc: plain class, no `Protocol`/`ABC`. This doc adds private helper methods to the
existing `McpToolDiscoveryService`, not new public surface.

### Details

Pseudocode additions (no production code):

```
class McpToolDiscoveryService:
    # ... existing __init__, discover_all (extended), _fetch_server_tools,
    #     _validate_and_normalize_entry, _dedupe_and_build from the base doc ...

    def _is_strict(self) -> bool: ...
        # return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict", False))

    def _is_fatal_severity(self) -> bool: ...
        # return self._is_strict() or self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION

    def _build_drift_findings(
        self, entries: list[tuple[str, str, dict[str, object]]]
    ) -> list[StartupCheckOutcome]: ...
        # per_server: dict[str, list[str]] = {}
        # for server_key, _url, entry in entries:
        #     per_server.setdefault(server_key, []).append(entry["name"])
        # drift = validate_routing_against_live(live_tool_lists=per_server)
        # status = StartupCheckStatus.FATAL if self._is_fatal_severity() else StartupCheckStatus.WARNING
        # return [
        #     StartupCheckOutcome(source="mcp_tool_discovery", status=status,
        #                          message=f"Live routing drift [{sk}]: {msgs}")
        #     for sk, msgs in drift.items()
        # ]

    async def _check_tool_definitions_finding(self) -> StartupCheckOutcome | None: ...
        # from agent.repl_health import _check_tool_definitions
        # try:
        #     result = await _check_tool_definitions(self._ctx, strict=self._is_strict())
        #     if result.has_issues:
        #         status = StartupCheckStatus.FATAL if self._is_fatal_severity() else StartupCheckStatus.WARNING
        #         return StartupCheckOutcome(source="mcp_tool_discovery", status=status,
        #                                     message="; ".join(result.warning_messages()))
        #     return None
        # except RuntimeError as exc:
        #     status = StartupCheckStatus.FATAL if self._is_fatal_severity() else StartupCheckStatus.WARNING
        #     return StartupCheckOutcome(source="mcp_tool_discovery", status=status, message=str(exc))
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/agent/services/mcp_tool_discovery.py && uv run ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations — confirms the new `agent.repl_health._check_tool_definitions` import stays agent-to-agent (legal), and `shared.tool_routing_validation` import stays agent-to-shared (legal) |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass, including new migrated cases (see paired test doc) |
| No orphaned imports | `rg -n "check_routing_drift_vs_live\|check_tool_definitions_startup\|_validate_tools_response" scripts/ tests/` | 0 matches outside `repl_health.py`'s removal doc and any documented shim |
| 4-combination severity check | manual/unit test: construct one test per (strict, profile) pair from the Design table, assert `StartupCheckStatus` matches | all 4 match the table exactly, none accidental |
| Constraint | `ast-grep --pattern 'except: $$$' --lang python scripts/agent/services/mcp_tool_discovery.py` | no bare except |
