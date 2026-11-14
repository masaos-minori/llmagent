# Make RuntimeToolRegistry the sole runtime tool authority

## Priority
High

## Summary
Remove the static `tool_definitions` fallback and static counts from the runtime paths so that LLM tool exposure and the `/mcp status`, `/mcp tools`, and `/help` displays all report one authority, `RuntimeToolRegistry`.

## Background
Source: `memo-issue.md` (Issue F), re-verified against current source on 2026-11-11.

- `Explicit in code`: `LLMTurnRunner._stream_llm()` in `scripts/agent/llm_turn_runner.py` uses `registry.llm_tool_definitions()` when a registry exists, and otherwise uses `ctx.cfg.tool.tool_definitions`.
- `Explicit in code`: `scripts/agent/commands/cmd_mcp.py` prints `len(ctx.cfg.tool.tool_definitions)` labeled as coming from `config/tools_definitions.toml` in `/mcp status`.
- `Explicit in code`: `scripts/agent/commands/registry.py` also reads `len(ctx.cfg.tool.tool_definitions)` (likely the `/help` source; `Needs confirmation`).
- `Documentation only` (memo): the same `/mcp status` run later renders a RuntimeToolRegistry diagnostics table; `/mcp tools` uses the registry only. Not re-verified in this pass.

## Problem
Two tool authorities coexist at runtime. When the registry is absent, the LLM receives static definitions that may not match the live MCP surface, and operator-facing commands show static counts next to registry diagnostics.

## Reason for Change
The runtime authority is documented as the registry, but code still honors a static fallback. This is a wiring and correctness risk (the LLM can be offered tools that are unavailable or disabled) and the discrepancy is visible to operators. No separate deadline; severity follows the runtime-correctness criterion.

## Implementation Intent
- Treat registry absence after startup as a typed wiring error (fail closed), not a trigger for a fallback.
- Keep an empty but concrete registry valid as a no-tools surface, subject to component mandatoriness rules.
- Make all operator displays read runtime totals from the registry (LLM-visible, disabled, unavailable).
- Narrow static `tool_definitions` to drift validation and fixtures only, after the last runtime consumer is removed.

## Target Files or Areas
- `scripts/agent/llm_turn_runner.py`
- `scripts/agent/commands/cmd_mcp.py`
- `scripts/agent/commands/registry.py`
- `scripts/agent/config_dataclasses.py` (`ToolConfig` comments)
- `scripts/shared/tool_constants.py` (obsolete routing comments; shared with the classification issue)
- Tests for `cmd_mcp.py` and the command registry under `tests/` (paths `Unknown`)
- ADR-003 under `docs/10_adr/` (Known Deviations)

## Required Changes
- Remove the static fallback from `_stream_llm()`; raise a typed configuration or wiring error when the registry is absent.
- Preserve an empty concrete registry as a valid no-tools LLM surface only where component mandatoriness allows it.
- Replace the `/mcp status` static count with registry totals including LLM-visible, disabled, and unavailable counts.
- Update the `/help` implementation that reads static definitions.
- Revise `ToolConfig.tool_definitions` comments after all runtime consumers are gone.
- Register the current fallback and count behavior in ADR-003 Known Deviations until the fix lands.

## Constraints
- Do not remove static definitions that drift validation and fixtures use.
- No compatibility fallback may be introduced.
- Known Deviations entries must stay in sync with the governance list (`tools/check_known_deviation_sync.py`).

## Acceptance Criteria
- No LLM call receives static tool definitions at runtime.
- `/mcp status`, `/mcp tools`, and `/help` report the registry as the single authority.
- Registry absence raises a typed fail-closed error and does not trigger a fallback.
- Static definitions remain only for drift validation and fixtures.

## Testing Expectations
- Unit tests for `_stream_llm()` with and without a registry (typed error, empty registry, populated registry).
- Update command tests that assert the static count; add tests for the runtime totals.
- Run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports`, targeted pytest, and `uv run python tools/check_docs_consistency.py --domain agent`.

## Documentation Impact
Update ADR-003 Known Deviations and Verification, and the agent and MCP documents that describe `/mcp status`, `/help`, and tool authority: intent, failure behavior (fail closed), and Needs Confirmation items. Run `uv run python tools/check_known_deviation_sync.py` and `uv run python tools/check_docs_quality.py`.

## Out of Scope
- Changes to `RuntimeToolRegistry` discovery or availability logic.
- Removing the static definition file or its drift validation.
- MCP route or dispatch changes.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping items:
- `plans/20261111-110144_adrrev017_docs-history-wording.md` (overlap: partial, documentation only): remove change-history passages from current-specification documents, and correct the FATAL definition in `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` and other ADR wording (including ADR-003). It does not change runtime tool authority.
- `issues/20261110-171040_rmcompat007_history-comment-sweep.md` (overlap: partial): remove or rewrite module docstrings and comments in `scripts/` and `config/` that describe code origin or plan history. The contradictory routing comment in `tool_constants.py` is a current-behavior contradiction, not only history; handle it here or in the classification issue, and leave history wording to rmcompat007.

Ordering and other dependencies:
- `plans/20261111-110144_adrrev017_docs-history-wording.md` edits ADR-003 and `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` wording; re-verify ADR-003 text after it lands to avoid a documentation conflict.
- Shares the `tool_constants.py` comment cleanup with the side-effect classification issue filed in this batch; assign the comment edit to one of them.

## Unresolved Questions
Decision required from the maintainer:
- Decision 1: whether an empty RuntimeToolRegistry is a valid no-tools startup state for optional MCP-only configurations, or a startup error.

Open facts (不明):
- the actual `/help` source module and the existing command test paths (`registry.py` is a candidate).
- Assumption: ADR-003 is the correct ADR for the Known Deviations entry.

## AI Implementation Instruction
- Change only the runtime consumers, command output, and their tests and docs; keep the diff minimal.
- Fail closed; never add a fallback to static definitions.
- Stop and report if the empty-registry decision blocks the startup path.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163741
- **Related target files**: `scripts/agent/llm_turn_runner.py`, `scripts/agent/commands/cmd_mcp.py`, `scripts/agent/commands/registry.py`, `scripts/agent/config_dataclasses.py`, `scripts/shared/tool_constants.py`
