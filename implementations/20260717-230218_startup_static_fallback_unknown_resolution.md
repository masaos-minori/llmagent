# Implementation procedure: resolve the "empty RuntimeToolRegistry fallback" Unknown (plan step 6)

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 6, resolving the plan's single Unknown row.

## Goal

Resolve this plan's Unknown — whether the main runtime execution path has (or should have) a
fallback-to-static-`tool_definitions` behavior when `RuntimeToolRegistry` is empty/unavailable at
startup — by cross-referencing requirement 03/09's already-designed startup-failure severity model,
per this plan's Implementation step 6 and its Unknowns table's suggested resolution path.

## Scope

**In scope**
- Read requirement 03's and requirement 09's implementation procedure docs' severity-handling
  sections to determine what happens when MCP tool discovery yields zero usable tools (all servers
  unreachable, or all entries malformed).
- Record the answer and its implication for whether items 2-4 (`tool_registry.py`,
  `tool_constants.py`, `config_dataclasses.py`) need to describe an actual runtime fallback code path,
  or only a test/doc-only fallback framing.

**Out of scope**
- Implementing any change to `scripts/agent/startup.py` or `McpToolDiscoveryService` (requirement
  09's job, already landed as a design doc — see Assumption 1).
- Deciding requirement 03/09's severity model from scratch — this item only reads and reports what
  they already specify.

## Assumptions

1. Per `implementations/20260717-225949_requirements_04_09_landing_check.md`, requirements 03 and 09
   **have** landed as implementation procedure docs
   (`implementations/20260717-203830_mcp_tool_discovery.py.md`,
   `implementations/20260717-224511_mcp_tool_discovery.py.md`,
   `implementations/20260717-224630_startup.py.md`), so this resolution can proceed now, independent
   of requirements 04-07's landing status.
2. The unified severity scheme, per `implementations/20260717-224511_mcp_tool_discovery.py.md`
   (Design section, "unified severity scheme"), is:
   ```
   is_fatal = strict or (security_profile == SecurityProfile.PRODUCTION)
   status = StartupCheckStatus.FATAL if is_fatal else StartupCheckStatus.WARNING
   ```
   applied per-finding (duplicates, drift, schema errors, per-server fetch failures) — not as a
   single aggregate "is the whole registry empty" check.

## Implementation

### Target file

N/A for this item directly — this is an analysis/decision artifact. Its conclusion is consumed by
`implementations/20260717-230029_tool_registry.py.md`,
`implementations/20260717-230126_config_dataclasses.py.md`, and (once requirements 04/05 land) whatever
doc specifies routing/schema behavior when the registry is empty.

### Procedure

1. Read `implementations/20260717-203830_mcp_tool_discovery.py.md` lines ~120-150 (per-server
   unreachable/malformed handling) and `implementations/20260717-224511_mcp_tool_discovery.py.md`
   lines ~85-190 (unified severity scheme, duplicate/drift severity table).
2. Read `implementations/20260717-224630_startup.py.md` lines ~140-160 (how `StartupCheckOutcome`
   values fold into `pipeline.add_fatal`/`add_warning`).
3. Determine: is "zero tools discovered across all servers" itself ever elevated to a distinct FATAL
   condition, or does it only ever surface as an accumulation of per-server WARNING outcomes (in the
   non-strict, non-production case)?
4. Record the finding and its implication.

### Method

Manual document read + summarization; no code produced by this item.

### Details

**Finding**: the severity model, as designed across requirements 03/09, handles three kinds of
findings — per-server fetch failure (`StartupCheckStatus.WARNING`, "an unreachable/malformed server is
a warning, not fatal — consistent with today's `repl_health.py` behavior", per
`implementations/20260717-203830_mcp_tool_discovery.py.md` line ~127), duplicate tool names
(FATAL in production / WARNING in local, per requirement 03's Assumption 5), and drift
(`is_fatal = strict or security_profile == PRODUCTION`, per requirement 09's unified scheme). **None
of these treat "zero total tools discovered because every server was unreachable" as its own,
distinct FATAL condition.** In local, non-strict mode, an all-servers-unreachable startup would
accumulate N per-server WARNING outcomes and proceed with what is almost certainly an **empty**
`RuntimeToolRegistry` — startup does not hard-fail in that specific combination unless `strict` is set
or `security_profile == PRODUCTION`.

**Implication for this requirement's compatibility framing**: this is a genuine, real gap the whole
batch has left implicit, exactly as this plan's Unknowns table anticipated. It means:
- The Unknowns table's suggested resolution ("if requirement 03 already treats total discovery
  failure as fatal... this requirement's framing doesn't need a runtime fallback path") does **not**
  fully apply — requirement 03/09's design, as read, does *not* unconditionally fatal an empty
  registry in local/non-strict mode.
- Whether the runtime execution path (requirements 04/05) should therefore fall back to static
  `tool_definitions`/`tool_constants.py` for an empty `RuntimeToolRegistry`, or should instead treat
  an empty registry as "zero tools available, degrade gracefully with no tools" (i.e., no static
  fallback, just an empty tool set), is a genuine product/design decision that requirements 04/05 must
  make explicitly when they land — this requirement (10) cannot invent that decision on their behalf,
  per this plan's own Out-of-scope ("Re-doing requirements 04-09's actual migration work").
- For this requirement's own docstring/comment items (2-4), the correct, honest framing is: state that
  a static-fallback path *may* exist for the empty-registry case (contingent on requirements 04/05's
  actual decision, not yet made), rather than asserting either "no fallback exists" or "a fallback
  exists" as settled fact. `implementations/20260717-230029_tool_registry.py.md`'s Details section
  already reflects this hedge ("Whether such a runtime fallback path exists at all is resolved
  separately... do not assume one exists without checking").
- Recommend flagging this finding back toward whichever future work item covers requirements 04/05,
  so their plans explicitly decide: hard-fail on empty registry (recommended for production
  consistency with the duplicate/drift FATAL rule), or graceful empty-tool-set degradation, or static
  `tool_definitions` fallback (least preferred, since it would resurrect the very static-primary
  behavior this whole batch is migrating away from).

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Finding cross-referenced correctly | manual re-read of the three cited docs' cited line ranges | quotes/paraphrases in this doc match the source docs |
| Docstring hedge consistency | manual read of `implementations/20260717-230029_tool_registry.py.md` and `implementations/20260717-230126_config_dataclasses.py.md` | both correctly hedge rather than assert a settled answer |
| No unauthorized decision made | manual review at requirement 04/05 planning time | requirements 04/05's own plans make the empty-registry decision explicitly, not inherited silently from this doc |
