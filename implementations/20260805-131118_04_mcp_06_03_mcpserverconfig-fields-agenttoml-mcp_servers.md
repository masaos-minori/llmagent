# Implementation Procedure: 04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md

## Goal
Update `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` so the field table
matches the actual `McpServerConfig` dataclass (13 TOML-settable fields + 1 auto-derived `key`),
and add accurate usage notes for `tool_names` and `role`.

## Scope
- In scope: `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` only.
- Out of scope: any source file under `scripts/`, any other `docs/*.md` file.

## Assumptions
- The field list in the plan (`plans/20260804-066200_plan.md`, now moved to `plans/done/`)
  reflects the dataclass at `scripts/shared/mcp_config.py:49` as of this writing.
- No behavior change is intended; this is a documentation-accuracy fix (see
  `rules/coding.md` "Documentation notes" classification: this falls under
  "Documentation fix required" — the doc under-lists fields relative to code).

## Design decisions
- Keep the existing doc structure (frontmatter, ownership note, table, deprecation note,
  `key` note, `startup_mode="none"` note, validation rules) — only the table and two new
  usage notes change, per `skills/python-design` guidance to avoid over-scoping a
  documentation-only change.
- Add `tool_names` and `role` usage notes as new paragraphs after the table (not inside the
  table cells) to keep the table skimmable, matching the existing prose-note pattern already
  used for `key`, `startup_mode="none"`, and the deprecation note.
- Source of truth for defaults/types is the dataclass field list at
  `scripts/shared/mcp_config.py:49-71` (verified by direct read, not the plan text alone).

## Alternatives considered
- Splitting fields into multiple tables (e.g. "core" vs "operational"): rejected — adds
  structure not requested by the plan and increases diff size beyond what's needed.
- Leaving `tool_names`/`role` clarification only as table cell text: rejected — the nuance
  (drift-validation-only, not routing; display-only, not dispatch) needs more than a
  one-line cell to avoid re-introducing the same ambiguity the plan flags.

## Implementation
### Target file
- `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure
1. Replace the sentence "以下の4つのフィールドのみが agent.toml に含まれる:" (line 21) with
   an accurate statement noting 13 TOML-settable fields plus the auto-derived `key` field.
2. Replace the table (lines 23-29) with a table covering all 13 fields, in dataclass
   declaration order: `transport`, `url`, `startup_mode`, `call_timeout_sec`,
   `startup_timeout_sec`, `tool_names`, `auth_token`, `role`, `cmd`, `env`,
   `startup_stagger_delay_sec`, `max_stderr_log_size_mb`, `max_stderr_log_files`. Keep the
   existing `フィールド | 型 | デフォルト | 説明` column format.
3. After the table (and before or alongside the existing `key` note), insert a note for
   `tool_names`: not used for routing decisions; serves as metadata for drift validation
   (cross-reference `docs/04_mcp_03_01_dispatch-and-routing.md`); document the three states
   — omitted (defaults to `[]`), empty list `[]`, and a configured list.
4. Insert a note for `role`: human-readable label for operators, shown in the `/mcp status`
   command output `ROLE` column; not consumed by routing or dispatch logic.
5. Preserve the existing deprecation note (`healthcheck_mode`), the `key` field note, and the
   `startup_mode="none"` note unchanged, only adjusting surrounding text if the new notes
   change paragraph ordering.

### Method
- Manual/AI text edit of the single Markdown file using an editor tool (no script needed;
  single-file, well-bounded change).
- Verify field types/defaults against `scripts/shared/mcp_config.py:49-71` (dataclass
  definition) before finalizing table values — do not copy plan text blindly since the plan
  is a secondary source.
- Verify `tool_names` drift-only usage against `scripts/shared/tool_routing_validation.py:15-31`
  (`validate_tool_names_match`, gated on `if not cfg.tool_names: continue`).
- Verify `role` display-only usage against `scripts/agent/services/mcp_status.py:116,189`
  (`role=cfg.role or ""`) and `scripts/agent/commands/cmd_mcp.py:47-49` (role shown in
  formatted status line).

### Details
- Field defaults/types to use in the table (from `scripts/shared/mcp_config.py`):
  - `transport: TransportType` — required, `TransportType.HTTP` (`"http"`)
  - `url: str` — required, base URL for HTTP transport
  - `startup_mode: StartupMode = StartupMode.NONE` — `"none"` / `"persistent"` / `"subprocess"`
  - `call_timeout_sec: float = 60.0` — per-call timeout; `0` = no timeout
  - `startup_timeout_sec: int = 30` — subprocess startup health-poll timeout (seconds)
  - `tool_names: list[str] = []` — drift-validation metadata only, not routing
  - `auth_token: str = ""` — Bearer token sent by `ToolExecutor`
  - `role: str = ""` — human-readable label, shown in `/mcp status` `ROLE` column
  - `cmd: list[str] = []` — launch command, required non-empty when `startup_mode=subprocess`
  - `env: dict[str, str] = {}` — extra subprocess env vars; denylist enforced
    (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`)
  - `startup_stagger_delay_sec: float = 0.0` — stagger delay between consecutive server starts
  - `max_stderr_log_size_mb: float = 100.0` — max stderr log size before rotation
  - `max_stderr_log_files: int = 3` — number of rotated stderr log files kept
  - `key: str = ""` (auto-derived, not TOML-settable) — already documented separately; no
    change needed to that existing note beyond confirming it still reads correctly with the
    new table above it.

## Compatibility considerations
- Documentation-only change; no source code, config schema, or runtime behavior is affected.
- No impact on `check-mcp-docs` port/tool-name drift checks since no port or tool-name tokens
  are being changed, only field documentation prose/table content.

## Security considerations
- N/A — no code change. Ensure the `env` field description does not omit the denylist
  behavior, since that is a security-relevant validation rule already enforced in
  `scripts/shared/mcp_config.py:123-132` and should stay documented accurately.

## Rollback considerations
- Single-file Markdown edit; revert via `git checkout -- docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md`
  or a follow-up commit reverting the change. No migration or data implications.

## Validation plan
- Manual review: confirm the table lists all 13 TOML-settable fields plus the separately
  documented `key` field, with correct types/defaults per `scripts/shared/mcp_config.py:49-71`.
- Confirm the old "4つのフィールドのみ" claim is fully removed.
- Confirm `tool_names` note states drift-validation-only usage and the three states
  (omitted / `[]` / configured list).
- Confirm `role` note states display-only usage (`/mcp status` `ROLE` column) and explicitly
  states it is not consumed by routing/dispatch.
- Run `uv run check-mcp-docs` (per `rules/toolchain.md` "MCP documentation consistency") to
  confirm no new broken-link or drift regressions were introduced by the edit.

## Out of scope
- Any change to `scripts/shared/mcp_config.py` or other source files.
- Any change to other `docs/*.md` files, including `04_mcp_03_01_dispatch-and-routing.md`
  and `04_mcp_06_02_configuration-file-inventory.md` (referenced only for cross-linking).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-066200_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-131118
- Related target files: docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md
