## Goal

- Restructure the `scripts/shared/` file-structure section of
  `docs/01_overview-files-04-shared-part2.md`: drop the stale ASCII tree, replace it with a
  pointer + structured list of files, add the three missing files
  (`config_utils.py`, `runtime_tool.py`, `runtime_tool_registry.py`) with their
  responsibilities, and confirm/refresh the existing design-rationale and drift-verification
  prose so it matches current code.

## Scope

- In scope: the "## 3. ファイル構成" section (ASCII tree, currently lines ~18-69) and the
  "### 設計上の意図と動作仕様" section (currently lines ~71-80) of
  `docs/01_overview-files-04-shared-part2.md`.
- Out of scope: any file under `scripts/`; any other `docs/*.md` file; the "Related
  Documents" / "Keywords" sections of this same file.

## Assumptions

- Fact (verified this session via `ls scripts/shared/`): `config_utils.py`,
  `runtime_tool.py`, and `runtime_tool_registry.py` exist in `scripts/shared/` and are
  absent from the current ASCII tree in the doc — the plan's stated drift is real.
- Fact (verified this session via direct read of
  `docs/01_overview-files-04-shared-part2.md` lines 71-80): the design-rationale paragraph
  for `tool_cache.py`/`mcp_health.py`/`tool_transport_invoker.py` and the drift-verification
  bullet list (Config-drift / Live-drift / Duplicate-ownership) already exist in the doc and
  already state the same behaviors the plan asks to confirm. This portion of the plan
  appears to already be satisfied at the doc level.
- Assumption: the user still wants the ASCII-tree-to-flat-list conversion and the
  three-file addition carried out as instructed, and wants the existing cache/drift prose
  re-verified against current code (not blindly trusted) rather than left untouched — per
  `rules/coding.md` "Documentation notes" classification, an already-correct passage is
  "Accepted current specification" and should be kept as plain prose, not re-labeled.

## Design decisions

- Per `skills/python-design/workflow.md` Step 4 ("design package layout at responsibility
  level; do not list every planned file unless the file boundary itself is a design
  decision") — this doc is explicitly a file-structure reference, so a per-file
  responsibility list is the correct format here (exception to the general guidance, by the
  doc's own purpose).
- Follow the same replacement pattern already used for `web_search/`/`github/` in
  `docs/01_overview-files-03-scripts-part4.md` (see
  `implementations/20260805-105913_01_overview-files-03-scripts-part4.md`): keep short,
  one-line-per-file responsibility descriptions rather than prose paragraphs, since
  `scripts/shared/` is a flat directory of ~44 files where a scannable list is more useful
  than free text.
- Keep the existing bilingual convention (Japanese prose, English module/symbol names)
  used throughout the surrounding file.
- Per `rules/coding.md` "Documentation notes" classification: treat the existing
  cache/health-gate and drift-verification prose as "Accepted current specification" if
  re-verification confirms it still matches code (expected, based on this session's
  `repl_health.py`/`startup.py`/`mcp_tool_discovery.py` checks) — do not add a "Current
  behavior" label, just leave/lightly refresh the prose.

## Alternatives considered

- Keep the ASCII tree and only patch in the 3 missing lines — rejected: the plan explicitly
  asks for the tree to be replaced with a flat/lightly-grouped list (plan Assumptions,
  item 1), and an ASCII tree is harder to keep in sync with `ls scripts/shared/` long-term.
- Auto-generate the file list from `ls scripts/shared/` at doc-build time — rejected: no
  doc-generation pipeline exists in this repo (plain hand-maintained Markdown); out of
  scope for a single-file listing fix.
- Rewrite the cache/drift-verification section from scratch instead of re-verifying the
  existing prose — rejected: the existing prose already matches current code behavior per
  this session's investigation; a full rewrite would be unnecessary churn.

## Implementation

### Target file

- `docs/01_overview-files-04-shared-part2.md`

### Procedure

1. Re-run `ls scripts/shared/` immediately before editing to get the authoritative current
   file list (44 files + `protocols/` subpackage as of this investigation).
2. Re-read `docs/01_overview-files-04-shared-part2.md` (full file is short, ~93 lines) to
   confirm current line numbers for the tree block and the design-rationale block, since
   they may have shifted since this procedure was written.
3. Replace the ASCII tree (fenced ` ```text ` block) with: (a) one sentence pointing to
   `scripts/shared/` as the authoritative source, and (b) a flat Markdown list of
   `` `filename.py` `` — one-line responsibility, grouped loosely by theme (LLM
   client/transport, tool routing/execution, config, misc utilities, `protocols/`) to keep
   it scannable, matching the existing per-file comment style already used in the tree.
4. Add the three missing entries:
   - `` `config_utils.py` `` — typed config value accessors (e.g. `get_str()`) for reading
     validated values out of raw TOML/JSON-loaded dicts.
   - `` `runtime_tool.py` `` — `RuntimeTool` frozen dataclass: normalized runtime
     tool-metadata shape (name, server_key, description, input_schema, is_write,
     agent_safety_tier, etc.) plus `build_runtime_tool()` constructor.
   - `` `runtime_tool_registry.py` `` — `RuntimeToolRegistry`: in-memory
     `{name: RuntimeTool}` registry populated by `McpToolDiscoveryService.discover_all()`
     at startup; sole routing authority consulted by
     `ToolRouteResolver.resolve()` (no fallback to `tool_registry.ToolRegistry`).
5. Re-verify (do not blindly keep) the "設計上の意図と動作仕様" prose against current code:
   - `tool_cache.py` / `ToolResultCache` vs. `ToolExecutor` usage.
   - `mcp_health.py` health-gated dispatch.
   - Drift behaviors: Config-drift (`routing_drift_strict`), Live-drift
     (`tool_definitions_strict` / `security_profile == PRODUCTION`), Duplicate-ownership
     (always Fatal).
   If unchanged from current code (expected per this session's checks), leave the prose as
   plain "Accepted current specification" text — no edit needed beyond confirming.
6. Explicitly state in prose that `ToolResultCache` is not currently used by
   `ToolExecutor` (already present in the current doc at line 74 — verify wording is still
   accurate and keep if so).

### Method

- Use `Read` on the full file first (it is only ~93 lines — no need to bound the read for
  this particular file).
- Use `grep -n "class RuntimeTool\|class RuntimeToolRegistry\|def get_str\|class ConfigUtils"
  scripts/shared/{runtime_tool,runtime_tool_registry,config_utils}.py` plus a bounded
  `Read` (first ~40-60 lines of each) to confirm responsibilities — do not read full
  module bodies.
- Use `grep -n "routing_drift_strict\|tool_definitions_strict\|security_profile"
  scripts/agent/{repl_health,startup,config_builders}.py` plus bounded reads around
  matches to re-verify drift behavior, rather than re-deriving it from scratch.
- Use `Edit` for the tree-block replacement and any prose touch-ups; avoid a full-file
  rewrite.

### Details

- Evidence (this session, `ls scripts/shared/`): current file set includes
  `config_utils.py`, `runtime_tool.py`, `runtime_tool_registry.py` — all three absent from
  the doc's current ASCII tree (doc lines 22-69).
- Evidence (this session, `scripts/shared/config_utils.py:18-25`): `get_str(d, key,
  default="")` — typed accessor raising `ValueError` on wrong type.
- Evidence (this session, `scripts/shared/runtime_tool.py:1-40`): module docstring states
  `RuntimeTool` is "the foundational data type that a future `RuntimeToolRegistry`
  ... will store and operate on"; `@dataclass(frozen=True)` at line 25.
- Evidence (this session, `scripts/shared/runtime_tool_registry.py:1-55`): module docstring
  states `route_resolver.ToolRouteResolver.resolve()` "consults this registry as the sole
  routing authority — no fallback to `shared.tool_registry.ToolRegistry` exists."
- Evidence (this session, `scripts/agent/startup.py:377-386`): `check_routing_drift(ctx,
  strict=ctx.cfg.tool.routing_drift_strict)` — non-strict findings become
  `pipeline.add_warning`; a `RuntimeError` (raised only when strict) is caught and becomes
  `pipeline.add_fatal`. Confirms the doc's existing Config-drift description.
- Evidence (this session, `scripts/agent/services/mcp_tool_discovery.py:29-30`, comment):
  "a duplicate is **always** reported as `FATAL`, regardless of `security_profile` or
  `strict`" — confirms the doc's existing Duplicate-ownership description.
- Evidence (this session, `scripts/agent/config_dataclasses.py:163,165`):
  `tool_definitions_strict: bool = False` and `routing_drift_strict: bool = False` fields
  exist on the tool config dataclass, consistent with the doc's field names.

## Compatibility considerations

- Documentation-only change; no code, schema, or API surface is touched.
- No `deploy/deploy.sh` copy-list update needed (per `rules/coding.md` "Module addition"
  row) since no module is added/removed in `scripts/`.
- No `config/agent.toml` change needed (no MCP server added).

## Security considerations

- N/A — prose/listing-only edit to a Markdown file; no executable content, no secrets
  involved.

## Rollback considerations

- Single-file Markdown edit; revert via
  `git checkout -- docs/01_overview-files-04-shared-part2.md`, or a follow-up commit
  reverting the specific hunk if wording needs adjustment.

## Validation plan

- Manual review: `git diff docs/01_overview-files-04-shared-part2.md` — confirm only the
  file-structure and design-rationale sections changed, and that the three new files
  (`config_utils.py`, `runtime_tool.py`, `runtime_tool_registry.py`) are present in the new
  list.
- `ls scripts/shared/` re-run and diffed by eye against the new doc list — no missing or
  extra files.
- `uv run check-mcp-docs` (per `rules/toolchain.md` "MCP documentation consistency") — run
  to confirm no broken internal links or `scripts/`-path reference regressions were
  introduced by the edit.
- No Python-code validation steps (ruff/mypy/pytest/bandit/lint-imports) apply — this is a
  documentation-only change with no `scripts/` edits.

## Out of scope

- Any other section of `docs/01_overview-files-04-shared-part2.md` (Related Documents,
  Keywords) beyond the two sections listed under Scope.
- `docs/01_overview-files-04-shared-part1.md` or any other doc file.
- Any source code change under `scripts/shared/` or elsewhere.
- Wiring `RuntimeToolRegistry` into any consumer — that is separate implementation work
  tracked outside this documentation cycle.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-120000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-111221
- Related target files: 01_overview-files-04-shared-part2.md
