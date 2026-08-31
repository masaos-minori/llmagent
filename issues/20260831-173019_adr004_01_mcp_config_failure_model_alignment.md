# Align McpServerConfig's failure-handling fields with ADR-004's revised Production-only model

## Priority
Medium

## Summary
`docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md` was revised to define Production
mode as the only supported execution mode and to require that any configured component
(including MCP servers) that is unavailable causes Fail-Fast at startup, with no
required/optional distinction. `scripts/shared/mcp_config.py`'s `McpServerConfig` still
implements the pre-revision three-value model (`required_in_production`,
`required_in_local`, `failure_policy`), which no longer matches the ADR.

## Background
This is the recommended action recorded in the revised ADR-004's Known Deviations entry
`ADR-004-D1-profile-config-model-still-present`. That revision explicitly left source-code
changes out of scope and asked for this alignment to be tracked as a follow-up issue.

## Problem
`McpServerConfig` (Evidence: Explicit in code — `scripts/shared/mcp_config.py`) defines:
- `required_in_production: bool = True`
- `required_in_local: bool = True`
- `failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST`

ADR-004's current Decision Details #7 states: "設定されたコンポーネント（MCPサーバーを含む）
が利用不能な場合、起動を中止する。必須／非必須という区分は設けない" (a configured component
that is unavailable causes startup to abort; no required/optional distinction is made). The
implementation's `required_in_local` field and the three-value `failure_policy` enum
(`fail-fast` / `disable-tool` / `degraded`, per the ADR's prior Known Deviation
`ADR-004-D8-failure-policy-unused`) both encode a distinction and a set of behaviors the ADR
no longer permits.

## Reason for Change
An implementation that still offers `disable-tool`/`degraded` failure policies and a separate
`local` required-flag contradicts the current architectural decision and could be
misconfigured to produce Degraded-startup behavior that ADR-004 now prohibits (INV-09: safety
or integrity failures must never be converted into Degraded operation; and more broadly,
Decision Details #7's Fail-Fast-only model for component unavailability).

## Implementation Intent
Simplify `McpServerConfig`'s failure-handling fields to match the single Fail-Fast model:
remove `required_in_local` and `failure_policy` (or reduce `failure_policy` to a single
enforced value), and keep a single required/enabled flag per server (`required_in_production`,
possibly renamed since "production" is now the only mode) whose unavailability always causes
startup to abort. Update every call site that reads these fields (starting with
`McpToolDiscoveryService`) to the simplified model.

## Target Files or Areas
- `scripts/shared/mcp_config.py` — `McpServerConfig`, `FailurePolicy` definitions
- `scripts/agent/services/mcp_tool_discovery.py` — consumer of the required/failure-policy fields
- `config/agent.toml` — any MCP server entries setting `required_in_local` or `failure_policy` explicitly
- `tests/` — tests constructing `McpServerConfig` with these fields (Evidence: Needs confirmation — exact test files not yet enumerated)

## Required Changes
- Remove `required_in_local` from `McpServerConfig`.
- Remove or collapse `failure_policy` (`FailurePolicy` enum) to a single Fail-Fast behavior; if the enum type itself is removed, update all references.
- Rename or repurpose `required_in_production` if a name change better reflects the Production-only model (decide during implementation; not a required rename).
- Update `McpToolDiscoveryService` (and any other consumer) to stop branching on `failure_policy` or on a local/production distinction.
- Update `config/agent.toml` if it sets `required_in_local` or `failure_policy` on any server entry.
- Update or remove the Known Deviation entries `ADR-004-D1-profile-config-model-still-present` and `ADR-004-D8-failure-policy-unused` in `docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md` once the implementation is aligned.

## Constraints
- Do not introduce a new required/optional distinction or a new multi-value failure policy — ADR-004's current decision is a single Fail-Fast behavior for all configured components.
- Do not change the meaning of "startup abort on unavailability" — only remove the now-unsupported alternatives (`disable-tool`, `degraded`, local-specific requiredness).
- Do not modify ADR-004's Decision, Rationale, Invariants, or Failure Policy content — only its Known Deviations section, once resolved.

## Acceptance Criteria
- `McpServerConfig` no longer has a `required_in_local` field or a multi-value `failure_policy`.
- Every consumer of the removed fields is updated and no longer branches on a local/production distinction.
- `config/agent.toml` contains no reference to the removed fields.
- ADR-004's Known Deviations no longer lists `ADR-004-D1-profile-config-model-still-present` (or it is updated to reflect a new, smaller residual gap if one remains).
- `uv run pytest` shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Update or add unit tests for `McpServerConfig` construction and validation to reflect the simplified field set.
- Update or add tests for `McpToolDiscoveryService` verifying that any configured MCP server's unavailability causes startup failure, with no path producing Degraded/disabled-tool continuation.
- Run the full `uv run pytest` suite once and compare against the pre-change baseline.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
Update `docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md`'s Known Deviations
section once the implementation change lands, per that document's own Known Deviations entry.
Check `docs/00_index.md`'s task-scope mapping for any other document referencing
`McpServerConfig`'s failure-handling fields before editing further.

## Out of Scope
- Any other field on `McpServerConfig` unrelated to failure handling.
- Changing MCP server startup retry/backoff behavior.
- Re-litigating ADR-004's Decision Details #7 (already settled).

## Dependencies
Follows the ADR-004 revision to a Production-only, single-Fail-Fast model (see
`docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md`, Known Deviations
`ADR-004-D1-profile-config-model-still-present`).

## Unresolved Questions
- Whether `required_in_production` should be renamed now that "production" is the only mode, or left as-is for minimal diff — needs an owner decision, default to leaving it as-is unless a maintainer requests the rename.
- Whether any `config/agent.toml` server entry actually sets `required_in_local` or a non-default `failure_policy` today — needs confirmation before editing the config file.

## AI Implementation Instruction
- Read `scripts/shared/mcp_config.py` and every call site of `required_in_local`/`failure_policy` before editing — do not guess which behavior to preserve.
- Do not invent a replacement multi-value model; the ADR requires a single Fail-Fast behavior.
- Update `docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md`'s Known Deviations section in the same change once the implementation is aligned, per that document's own instruction.
- Do not modify ADR-004's Decision/Invariants/Failure Policy sections.
- Stop and report if `config/agent.toml` has server entries using the removed fields in a way that would change observed behavior if simply deleted.
