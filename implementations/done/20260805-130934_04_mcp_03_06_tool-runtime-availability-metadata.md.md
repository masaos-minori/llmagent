# Implementation Procedure: docs/04_mcp_03_06_tool-runtime-availability-metadata.md

## Goal
- Correct the doc's claim that config reload (`/reload`) causes `RuntimeToolRegistry` to be
  rebuilt from a fresh `/v1/tools` fetch, and clarify the distinct restart requirements for
  agent-level vs. per-server MCP configuration changes.

## Scope
- In scope: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — the "`/v1/tools` as
  RuntimeToolRegistry Source" section and a new "Reload vs. restart for RuntimeToolRegistry"
  subsection, plus a cross-reference to
  `docs/04_mcp_06_17_local-to-production-auth-migration.md`.
- Out of scope: any source code change; any other documentation file body content (only the
  cross-referenced anchor in 06_17 is read, not edited).

## Assumptions
- Source-verified (per plan): `RuntimeToolRegistry` is populated once at agent startup via
  `McpToolDiscoveryService.discover_all()` (`scripts/agent/services/mcp_tool_discovery.py:82`).
- Source-verified: `_ConfigMixin._cmd_reload()` (`scripts/agent/commands/cmd_config.py:37`)
  calls `ConfigReloadService(self._ctx).apply_config_dict(new_cfg)`
  (`scripts/agent/services/config_reload.py:113`), which calls `_reload_approval_settings()`
  (`config_reload.py:442`), which calls `runtime_tools.apply_policy(tier_map=..., allowed_tools=...)`
  (`config_reload.py:196`, target method at `scripts/shared/runtime_tool_registry.py:172`).
- Source-verified: `RuntimeToolRegistry.apply_policy()` only rewrites
  `agent_safety_tier`, `requires_approval`, `enabled_for_llm` via `dataclasses.replace`
  (`runtime_tool_registry.py:190-199`); it never touches `raw_definition`, `disabled_reason`,
  or `status`, and never re-fetches `/v1/tools`.
- Source-verified: `docs/04_mcp_06_17_local-to-production-auth-migration.md` already documents,
  in Japanese, that `/reload` never changes `[mcp_servers.*]` definitions and that MCP server
  definition changes require a full agent restart (lines 30-32, 68-72); its subsection heading
  is `#### /reload とフル再起動の違い`, so the anchor is `#reload-とフル再起動の違い`.

## Design decisions
- Keep the correction file-local: edit only the one doc file identified in the plan; do not
  touch `04_mcp_06_17` itself — link to its existing anchor instead of duplicating its content
  (avoids two sources of truth for the reload/restart distinction).
- Use two clearly separated concepts/headings ("Policy Application" vs. "Metadata Rebuild") per
  the plan's risk mitigation, rather than a single blended paragraph, to prevent readers from
  conflating hot-reloadable policy fields with startup-only discovery-derived fields.
- Classify this change as "Documentation fix required" per `rules/coding.md`'s "Current
  behavior" classification table (the current doc text is stale/incorrect, not describing an
  implementation bug) — fix the doc directly, no `issues/` entry needed.

## Alternatives considered
- Rewriting the whole "`/v1/tools` as RuntimeToolRegistry Source" section from scratch: rejected
  — larger diff than needed; the section is otherwise accurate about `/v1/tools` being the
  startup-time source, only the reload-causes-update sentence is wrong.
- Filing an `issues/` entry instead of fixing the doc directly: rejected — this is a
  documentation-only correction of stale prose, not a code defect, so it falls under
  "Documentation fix required", not "Implementation fix required".

## Implementation
### Target file
- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure
1. Locate the incorrect sentence at line 78 ("Any changes to tool availability (e.g., due to
   health degradation, config reload) will be reflected in subsequent `/v1/tools` responses and
   will cause `RuntimeToolRegistry` to be updated accordingly.") in the "`/v1/tools` as
   RuntimeToolRegistry Source" section (heading at line 69).
2. Replace that sentence with prose stating: `RuntimeToolRegistry` is populated once at agent
   startup via `McpToolDiscoveryService.discover_all()`; neither `/reload` nor any live
   health-check path triggers a rebuild of the registry from a fresh `/v1/tools` fetch.
3. Insert a new subsection "Reload vs. restart for RuntimeToolRegistry" after that section
   (before "## Field Mapping: /v1/tools ↔ RuntimeTool" at line 80), covering:
   - `/reload` (`_ConfigMixin._cmd_reload()`) calls
     `ConfigReloadService.apply_config_dict()`, which calls
     `RuntimeToolRegistry.apply_policy()`.
   - `apply_policy()` only updates policy-derived fields (`agent_safety_tier`,
     `requires_approval`, `enabled_for_llm`) and does not touch `raw_definition`,
     `disabled_reason`, or `status`.
   - A full agent process restart is required for the registry's discovery-derived state
     (including `/mcp status`'s `DISABLED_REASON` column) to reflect config changes.
   - Per-server config files (e.g. `allowed_dirs` in `file_read_mcp_server.toml`) require
     restarting that MCP server process itself, separate from the agent restart above.
4. Add a cross-reference link to
   `docs/04_mcp_06_17_local-to-production-auth-migration.md#reload-とフル再起動の違い`, noting
   that 06_17 covers restarts for `[mcp_servers.*]` connection definitions specifically, while
   this note covers the broader `RuntimeToolRegistry` availability-snapshot requirement.
5. Manual review pass: re-read the edited section and new subsection to confirm no remaining
   reference implies `/reload` refreshes discovery-derived fields.

### Method
- Direct Markdown edits (no code, no generated content). Preserve existing heading levels and
  the doc's existing citation style (backtick-quoted symbols and file paths).

### Details
- Anchor target confirmed present in `docs/04_mcp_06_17_local-to-production-auth-migration.md`
  (heading `#### /reload とフル再起動の違い`, lines 68-72); no change needed in that file.
- Existing section 6 (`## 6. RuntimeToolRegistry (agent-side)`, line 100) and the
  `diagnostics()` paragraph (line 104) already describe `disabled_reason` derivation correctly
  and do not need edits — only the reload-causes-update claim at line 78 is wrong.

## Compatibility considerations
- Documentation-only change; no API, schema, or behavior compatibility impact.
- No cross-references elsewhere in the repo point at the specific sentence being replaced
  (verified: the sentence is not quoted verbatim elsewhere); safe to edit in place.

## Security considerations
- N/A — no code, credentials, or configuration files touched.

## Rollback considerations
- Single-file Markdown edit; revert via `git checkout -- docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
  or a follow-up commit if the correction is found inaccurate.

## Validation plan
- Manual review per the plan's own validation plan: re-read the edited section against the
  source evidence above (`config_reload.py`, `runtime_tool_registry.py`,
  `mcp_tool_discovery.py`) to confirm the corrected text matches current code behavior.
- No `rules/toolchain.md` code-validation steps apply (doc-only change: no ruff/mypy/bandit/
  pytest/lint-imports/diff-cover run needed).
- Optional: `uv run check-mcp-docs` may be run after implementation to confirm no broken
  internal Markdown links were introduced by the new cross-reference.

## Out of scope
- Any change to `docs/04_mcp_06_17_local-to-production-auth-migration.md` itself.
- Any source code change to `config_reload.py`, `runtime_tool_registry.py`, or
  `mcp_tool_discovery.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-065900_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-130934
- Related target files: 04_mcp_03_06_tool-runtime-availability-metadata.md
