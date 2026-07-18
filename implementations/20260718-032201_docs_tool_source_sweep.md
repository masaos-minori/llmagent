# Implementation procedure: documentation sweep for static-tool-source compatibility framing (plan step 7)

Source plan: `plans/20260717-130629_plan.md` (requirement `requires/done/20260717_10_require.md`),
Implementation step 7.

## Goal

Sweep `docs/` for prose that still describes `config/agent.toml`'s `[[tool_definitions]]` and/or
`shared/tool_constants.py`'s frozensets and/or `shared/tool_registry.py`'s `ToolRegistry` as the
normal/authoritative runtime tool source, and update each genuine hit to state that MCP `/v1/tools`
(consumed via `RuntimeToolRegistry`) is the normal runtime source once requirements 04-07 land, with
the static sources repositioned as fallback/compatibility — mirroring the code-comment corrections
already drafted in `implementations/20260717-230029_tool_registry.py.md` and
`implementations/20260717-230059_tool_constants.py.md`.

## Scope

**In scope**
- All files returned by `rg -l "tool_definitions|tool_constants|ToolRegistry" docs/` (33 files,
  enumerated in Assumption 1) — read each and classify as "needs update" / "no update needed"
  (already-fallback-framed or unrelated mention) / "needs cross-link only".
- Prioritized, concrete edit guidance for the files with the strongest stale "sole/primary authority"
  claims, identified by grep in this investigation (Assumption 2).

**Out of scope**
- Any change to `docs/` files that do not mention these three terms.
- Rewording `docs/04_mcp_07_tool_schema_export_policy.md`'s own subject (tool schema export via
  `/v1/tools` and each server's `TOOL_LIST`) beyond its one `ToolRegistry` cross-reference — that
  doc already frames `/v1/tools`/`TOOL_LIST` as the schema source of truth, consistent with this
  requirement's goal, not contradicting it.
- Re-doing requirements 04-09's actual migration work (out of scope for the whole plan).

## Assumptions

1. `rg -l "tool_definitions|tool_constants|ToolRegistry\b" docs/` (run directly against the current
   tree) returns exactly these 33 files:
   `04_mcp_00_document-guide.md`, `04_mcp_01_system_overview.md`, `04_mcp_02_01_endpoints-and-transport.md`,
   `04_mcp_03_01_dispatch-and-routing.md`, `04_mcp_03_02_tool-registry.md`,
   `04_mcp_03_05_lifecycle-and-new-server.md`, `04_mcp_05_05_mdq-enforcement-and-lockdown.md`,
   `04_mcp_06_02_configuration-file-inventory.md`,
   `04_mcp_06_10_settings-with-high-operational-impact.md`,
   `04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`,
   `04_mcp_06_14_new-tool-registration-procedure.md`,
   `04_mcp_06_15_new-mcp-server-addition-checklist.md`,
   `04_mcp_06_16_pre-production-fail-open-checklist.md`, `04_mcp_07_tool_schema_export_policy.md`,
   `05_agent_02_runtime-architecture-part2.md`, `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`,
   `05_agent_05_llm-and-streaming-part1.md`,
   `05_agent_06_01_tool-execution-and-approval-execution.md`,
   `05_agent_06_02_tool-execution-and-approval-approval.md`,
   `05_agent_08_03_configuration-tools-memory.md`,
   `05_agent_10_01_operations-and-observability-startup-and-health.md`,
   `05_agent_11_02_extension-points-tool-registration-part1.md`,
   `05_agent_11_03_extension-points-registry-rules.md`, `05_agent_13_reference-api-part1.md`,
   `90_shared_01_01_overview-purpose-and-scope.md`, `90_shared_01_02_overview-layer-responsibilities.md`,
   `90_shared_02_01_types_and_protocols-core-types.md`,
   `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md`,
   `90_shared_02_03_types_and_protocols-reference.md`,
   `90_shared_03_01_runtime_and_execution-config-and-logging.md`,
   `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`,
   `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`,
   `01_overview-files-04-shared-part2.md`, `99_documentation_sync_report.md`.
2. Direct grep of the strongest-claim subset (performed for this investigation) found these
   high-priority, verbatim stale-authority statements (Japanese originals, paraphrased in brackets):
   - `docs/04_mcp_03_01_dispatch-and-routing.md:61`: `` `ToolRegistry` を**唯一のルーティング権威**として
     `tool_name → server_key` を解決する。`` [ToolRegistry as the **sole routing authority**] — also
     lines 64, 67, 83, 99, 124, 127 repeat "唯一のルーティング権威" (sole routing authority) /
     "正典集合" (canonical set) framing.
   - `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md:175-216`: section header
     `## 4b. ToolRegistry / route_resolver / tool_routing_validation (ルーティングの正本)` [routing's
     canonical source] plus body text "MCPツール所有権とルーティングの唯一の正本" [the sole canonical
     source for MCP tool ownership and routing] and "ルーティング判断の唯一の権威は ToolRegistry"
     [ToolRegistry is the sole authority for routing decisions] (lines 178-179) — this is the most
     detailed/central stale-claim block found, including a `ToolRegistry` class sketch (lines 190-216).
   - `docs/04_mcp_03_02_tool-registry.md:20,35-37,49-57`: the tool-registry reference doc itself;
     line 20 already correctly scopes `ToolRegistry` to "所有関係とルーティングのみ...スキーマレジストリ
     ではない" (ownership/routing only, not a schema registry) — this line does not need a routing-
     authority correction, but its step-list (lines 49-57) still frames `tool_constants.py` +
     `agent.toml`'s `tool_definitions` registration as the (only) procedure for adding a routable tool,
     which becomes incomplete once `RuntimeToolRegistry` (requirement 04) is the routing authority.
   - `docs/05_agent_06_01_tool-execution-and-approval-execution.md:38`: cross-link comment
     `ToolRouteResolver.resolve() — tool_name → server_key (ルーティングの権威; 04_mcp_03 §Routing
     Source of Truth 参照)` [the routing authority] — a one-line cross-reference, low edit cost.
   - By contrast, `docs/05_agent_06_02_tool-execution-and-approval-approval.md:62` already uses
     "フォールバック" (fallback) wording for `tool_constants.py`-based risk classification — this file
     already matches the target end-state framing and likely needs no change (confirm at
     implementation time rather than assume).
3. Requirements 04-07 (the actual `RuntimeToolRegistry` migration for routing/schema/side-effect/policy)
   have **not landed** yet, per `implementations/20260717-225949_requirements_04_09_landing_check.md`.
   Per this plan's own Risk section and Implementation step 1's gate, this sweep's *edits* must not be
   applied to `docs/` until those requirements land — this procedure document itself is the sweep plan
   (what to change and where), executed for real only after the gate passes, exactly like the
   `tool_registry.py`/`tool_constants.py` docstring edits.

## Implementation

### Target file

No single file — cross-cutting documentation sweep across the 33 files listed in Assumption 1, under
`docs/`. Highest-priority targets (concrete stale "sole authority" claims found by direct grep):
`docs/04_mcp_03_01_dispatch-and-routing.md`, `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`,
`docs/04_mcp_03_02_tool-registry.md`.

### Procedure

1. Re-run `rg -l "tool_definitions|tool_constants|ToolRegistry" docs/` at execution time (the doc set
   may have shifted since this investigation) to get the current candidate list.
2. Gate: confirm requirements 04-07 have landed (production-code docs, not just enum/test scaffolding
   — re-check `implementations/` per the same method as
   `implementations/20260717-225949_requirements_04_09_landing_check.md`) before applying any edit.
3. For each candidate file, read it and classify:
   - **Needs update**: states or implies `ToolRegistry`/`tool_constants.py`/static `tool_definitions`
     is the current/normal runtime routing, schema, side-effect, or policy source.
   - **Already correct / no update needed**: already uses fallback/compatibility framing (e.g.
     `05_agent_06_02_tool-execution-and-approval-approval.md`), or mentions these terms in an unrelated
     context (e.g. a changelog entry, a historical note already marked as superseded).
   - **Cross-link only**: a one-line reference to another doc's routing-authority claim (e.g.
     `05_agent_06_01`'s line 38) — update the referenced phrase, not the whole section.
4. For each "needs update" file, rewrite the specific claim to name `RuntimeToolRegistry`
   (`scripts/shared/runtime_tool_registry.py`) as the runtime-authoritative source, and reposition
   `ToolRegistry`/`tool_constants.py`/static `tool_definitions` as fallback/compatibility/seed-data,
   consistent with the wording already drafted for the code docstrings
   (`implementations/20260717-230029_tool_registry.py.md`,
   `implementations/20260717-230059_tool_constants.py.md`).
5. Do not touch files whose only mention is of the *schema-export* role (`TOOL_LIST`,
   `04_mcp_07_tool_schema_export_policy.md`) unless they also assert routing/policy authority — schema
   export is a separate concern from this requirement's routing/side-effect/policy scope (per the
   plan's Reason section's 4 named roles).

### Method

Per-file manual read + targeted prose edit (Markdown text only, no code/frontmatter schema change);
this is a content audit, not a mechanical find-replace, per the plan's own Design section step 3 and
Risks section (second risk: unbounded scope, mitigated by treating every genuine hit as in-scope).

### Details

- Treat `docs/04_mcp_03_01_dispatch-and-routing.md` and
  `docs/90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md` as the two highest-value
  edits — both currently state, in the strongest possible terms ("唯一の権威" / "唯一の正本" — "sole
  authority" / "sole canonical source"), a claim that becomes false once requirement 04 lands.
- `docs/90_shared_03_02_...` additionally contains a `ToolRegistry` class sketch (lines 190-216) that
  should gain a note that this sketch describes the fallback/seed-data role, with a pointer to
  `RuntimeToolRegistry`'s own sketch (once requirement 02's design, already landed as
  `implementations/20260717-203200_runtime_tool_registry.py.md`, is reflected in this doc too — that
  cross-link is itself part of requirement 02/09's own doc-sync scope, not invented fresh here; if it
  doesn't exist yet, add a minimal pointer rather than a full duplicate description).
- `docs/04_mcp_03_02_tool-registry.md`'s step-list (lines 49-57) should gain a note that step 1
  (`tool_constants.py` frozenset registration) is now the fallback/compat registration path, with the
  primary path being `RuntimeToolRegistry`'s live `/v1/tools` discovery (requirement 03, landed) —
  without removing the step list itself, since `tool_constants.py` registration remains necessary for
  the fallback/drift-detection role.
- `docs/99_documentation_sync_report.md`: check whether this file is itself a generated/point-in-time
  report (its name suggests a sync-check output) — if so, it may only need a regeneration after the
  other doc edits land, not a manual content edit; confirm at execution time rather than hand-edit a
  generated report.
- Do not invent wording for files not actually read — this list of high-priority files is not
  exhaustive; the remaining ~28 files from Assumption 1 must each still be individually read and
  classified per step 3 above at execution time.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Requirements 04-07 gate | manual check of `implementations/` for landed production-code docs | sweep edits not applied until gate passes |
| Sweep completeness | re-run `rg -l "tool_definitions\|tool_constants\|ToolRegistry" docs/` after edits | every "needs update" file from step 3's classification has been edited; no new stale-authority phrase remains |
| Content accuracy (manual) | read each edited file | no doc describes static config as the normal/current tool source; fallback/compat framing consistent with the code docstring wording |
| Automated doc-consistency check | `uv run check-mcp-docs` (per `rules/toolchain.md` "MCP documentation consistency"; specifically checks "Routing authority language consistency" and "Tool count consistency against canonical frozensets") | passes — this tool is purpose-built to catch exactly this class of stale-authority-language drift, so prefer it over relying on manual review alone |
| `uv run pytest` | full suite | no failures (docs-only change) |
