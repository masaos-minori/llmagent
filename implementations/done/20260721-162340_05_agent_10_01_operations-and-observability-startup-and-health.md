# Implementation: docs/05_agent_10_01_operations-and-observability-startup-and-health.md — document production-fatal mcp_tool_discovery behavior

Source plan: `plans/20260721-031357_plan.md` ("Make MCP tool-discovery failure visible/fatal
(sole-authority routing follow-up)"), Implementation step 5 ("Recommended follow-up
documentation update").

Not already implemented: verified against the current doc content (Startup Validation Severity
Mapping table, lines 189-213, read directly). The only row describing the outer except-clause
behavior for step 4's discovery-call failure is row 209 (`routing_drift_live` /
`check_routing_drift_vs_live()`, status `SKIPPED`), which documents today's unconditional
`add_skipped(...)` — there is no mention anywhere in the file of a `production_mode` branch or a
`FATAL` outcome for this failure path. The one filename-matching doc under
`implementations/done/` (`20260714-181038_05_agent_10_01_operations-and-observability-startup-and-health.md`)
covers an unrelated topic (removing an obsolete "not loaded" description from
`_get_workflow_status()`), confirmed by reading its Goal/Scope.

## Goal

Document the new production-fatal / upgraded-message behavior for total MCP tool-discovery
failure (the outer `except Exception` in `_check_services()` step 4), once
`implementations/20260721-162337_startup.py.md` is implemented, so the severity-mapping table
stays the accurate one-stop reference the file's own preamble (lines 185-187) claims it is.

## Scope

**In scope:**
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, the "Startup
  Validation Severity Mapping" table (lines 189-213) and its footnote list (lines 215-219).

**Out of scope:**
- Any other section of this file.
- Reconciling the table's existing use of the source label `routing_drift_live` /
  `check_routing_drift_vs_live()` for row 209 against the pipeline source string actually used at
  runtime by step 4 (`"mcp_tool_discovery"`, per `scripts/agent/startup.py` line 246) — this is a
  **pre-existing** naming inconsistency in the doc unrelated to this plan (row 209 already existed
  before this change and describes the same except-clause this plan modifies, just under a
  different source label than the code emits). Flagged here for the implementer's awareness per
  `rules/coding.md`'s "Current behavior" classification table (this would classify as
  "Documentation fix required" if pursued), but reconciling it is **not** part of this plan's
  scope and must not be silently folded into this edit — it would widen the diff beyond what the
  source requirement asked for. If the implementer judges it low-risk to fix in the same commit,
  raise it for explicit review first rather than fixing silently.

## Assumptions

1. The doc's row 209 (`routing_drift_live`, `SKIPPED`) is the row describing the *same*
   `except Exception as exc:` block in step 4 that `implementations/20260721-162337_startup.py.md`
   modifies — confirmed by matching the row's Condition text ("caught by `_check_services()`'s
   `except Exception as exc: pipeline.add_skipped(...)`") against the actual except block at
   `scripts/agent/startup.py` lines 245-248.
2. This doc update should be written only after (or alongside) the code change lands, so the
   documented behavior matches shipped code — but the procedure below can be drafted now since the
   exact code diff is already fully specified in
   `implementations/20260721-162337_startup.py.md`.
3. No other doc file references this specific except-clause's severity (only this file's table was
   found to describe it); no cross-file update is needed.

## Implementation

### Target file

`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Locate row 209 in the "Startup Validation Severity Mapping" table (the `SKIPPED` row for the
   outer except-clause of step 4).
2. Split it into two rows: keep a `SKIPPED` row for the non-production case (update its Condition
   text to reflect that it now only applies when `production_mode=False`), and add a new `FATAL`
   row for the `production_mode=True` case.
3. Add one line to the footnote list (lines 215-219) cross-referencing the new
   `tests/test_mcp_tool_discovery_fatal_in_production_on_exception` regression test (added per
   `implementations/20260721-162339_test_startup.py.md`), following the existing pattern of the
   last footnote bullet (line 219) that cross-references `TestCheckServicesSeverityClassification`.
4. Do not touch any other row or section.

### Method

Direct Markdown table-row edit plus one footnote-bullet addition. No structural change to the
table's column layout (`Check (source) | Severity | Condition | Rationale`).

### Details

Current row 209 (verbatim):

```
| `routing_drift_live` (`check_routing_drift_vs_live()`) | SKIPPED | Any exception from `check_routing_drift_vs_live()`, including the `strict=True` `RuntimeError` raised for "all servers unreachable", "duplicate tool ownership detected", or "live routing drift detected" — caught by `_check_services()`'s `except Exception as exc: pipeline.add_skipped(...)`. | Live/dynamic checks may legitimately be unavailable in some valid environments (e.g. MCP servers not yet started); `SKIPPED` distinguishes "could not check" from "checked and found a problem" (`WARNING`). |
```

Replace with two rows (keep the same source label used by the existing row, to avoid silently
fixing the out-of-scope naming inconsistency noted above):

```
| `routing_drift_live` (`check_routing_drift_vs_live()`) | SKIPPED | `production_mode=False` and any exception from the outer discovery call (including a `check_routing_drift_vs_live()` `RuntimeError` under `strict=True`) — caught by `_check_services()`'s `except Exception as exc:` block, which now branches on `production_mode` (see next row). | Live/dynamic checks may legitimately be unavailable in some valid environments (e.g. MCP servers not yet started); `SKIPPED` distinguishes "could not check" from "checked and found a problem" (`WARNING`). |
| `mcp_tool_discovery` (outer `except Exception` around `McpToolDiscoveryService(ctx).discover_all()`) | FATAL | `production_mode=True` and the outer discovery call raises for any reason (including the `check_routing_drift_vs_live()` cases above). A discovery-call failure means every tool call will fail for the entire session — an outage-grade condition, unlike a per-server finding (handled separately inside the `try` block and never escalated by this except clause). | Production deployments must not silently continue with tool-call routing entirely broken; matches the same production-fatal precedent already used by `_start_servers()` for subprocess startup failures. |
```

Footnote addition (append to the bullet list at lines 215-219):

```
- 回帰テスト: `tests/test_startup.py`の`test_mcp_tool_discovery_fatal_in_production_on_exception`が、`production_mode=True`時にこの分岐が`FATAL`になることを検証する。
```

## Validation plan

Documentation-only change; no lint/type/security tooling applies. Verify manually:

| Check | Method | Target |
|---|---|---|
| Consistency with code | Re-read `scripts/agent/startup.py`'s step 4 except block after `implementations/20260721-162337_startup.py.md` is implemented; confirm the doc's two new rows match the actual `production_mode` branch verbatim | Doc and code agree |
| Consistency with tests | Re-read `tests/test_startup.py`'s `test_mcp_tool_discovery_fatal_in_production_on_exception` (added per `implementations/20260721-162339_test_startup.py.md`) after it lands; confirm the footnote's test name matches exactly | Doc and test agree |
| MCP docs consistency | `uv run check-mcp-docs` | Passes — no startup-mode/routing-authority wording is changed by this edit |
| Markdown table formatting | Visual review — table renders correctly with the row split (4 columns preserved) | No broken table syntax |
