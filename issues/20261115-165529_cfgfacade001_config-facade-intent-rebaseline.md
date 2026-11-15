# Config-facade unification intent from `memo2.md` does not match the current architecture — re-baseline before any implementation

## Priority
Medium

## Summary
`memo2.md` proposes unifying config loading into a single agent-side settings facade
(`agent/settings.py`), centralizing cross-domain config validation, and normalizing
comma-separated `providers` config. Verified against the current filesystem, every
file-level and config-key premise of the memo is absent, and the memo's intent is
already largely implemented by the existing loader/builder architecture. This issue
re-files the intent so the pipeline can classify each memo item as already-implemented,
gap-confirmed-with-evidence, or rejected, and only then proceed to a plan.

## Background
`memo2.md` (repository root) records a prioritized improvement list (P1-1..P1-4, P2-1..P2-2)
and claims a prior implementation was completed and archived
(`implementations/done/2026-11-15-145440_settings-config-facade.md`). The memo itself
warns that prior verification may have run against a cached/memory tree rather than the
filesystem, and requires re-verification before execution.

Verification on 2026-11-15 against the current filesystem (master, clean tree, in sync
with origin/master 0/0, worktree `ragrev015-verify` checked too) found none of the memo's
claims exist:

- `agent/settings.py`, `agent/providers.py`, `mcp/config.py`, `mcp/toll_gate.py`,
  `mcp_settings.py`, `tests/agent/test_settings.py`, `tests/agent/test_providers.py`,
  `tests/mcp/test_config.py` — none exist; `scripts/mcp/` does not exist (MCP code lives
  in `scripts/mcp_servers/` and `scripts/mcp_launcher.py`).
- Config keys `mcp_timeout`, `mcp_max_call_time`, `mcp_max_result_tokens`, and a
  `providers = "openai, gemini"` string — zero occurrences in `config/agent.toml` or
  anywhere in the repository.
- The claimed commit `refactor(config): unify config loading and MCP settings into
  agent.settings facade` and the claimed archived procedure file do not exist in any
  branch or in `implementations/done/`.

The real config architecture (confirmed by repository evidence):

- `scripts/shared/config_loader.py` — shared `ConfigLoader` (TOML/JSON, `_merge_one_level`
  for `[mcp_servers.<key>]` sections) with per-process file isolation via `restrict_to()`
  (the per-process config isolation design noted in `config/agent.toml` comments, adrrev008).
- `scripts/agent/config_builders.py` + `scripts/agent/config_section_builders.py` +
  `scripts/agent/config_dataclasses.py` — typed `AgentConfig` assembly from loaded data.
- `scripts/shared/mcp_config.py` — `McpServerConfig` with timeout fields
  (`call_timeout_sec`, `health_timeout`, `startup_timeout_sec`) and its own validation
  (`_validate_timeouts`).
- `scripts/agent/production_config_validator.py` — production key validation derived from
  dataclass field introspection, plus tool safety-tier and registry checks.
- Per-domain loaders instantiate `ConfigLoader` with their own allowed files:
  `scripts/db/config.py`, `scripts/eventbus/config.py`, `scripts/rag/config_resolution.py`,
  `scripts/mcp_servers/<server>/*_models.py`.

## Problem
The memo's P1 items target files, config keys, and a completed refactor that do not exist.
Acting on the memo as written would create parallel config machinery alongside the
existing shared loader/builders and contradict the per-process config isolation design.
Whether any genuine residual gap remains (e.g. consistency of timeout keys across the
transport layer and server-internal layers) is unconfirmed.

## Reason for Change
`memo2.md` is actionable-looking but built on a phantom tree. Without a re-baselined issue,
the next session is likely to repeat the same phantom-premise work. Filing the intent
against verified facts prevents that and lets the pipeline judge whether any work remains.

## Implementation Intent
Do not implement a facade. First produce a classification of each memo item against the
existing architecture, citing file/line evidence: already-implemented, gap-confirmed, or
rejected. Only gap-confirmed items may proceed to a plan. Any future unification must
respect the per-process config isolation boundary (`ConfigLoader.restrict_to`), not merge
domain configs into one process-wide reader.

## Target Files or Areas
- `memo2.md` (source document to be marked expired or superseded once classification completes)
- `scripts/shared/config_loader.py`
- `scripts/shared/mcp_config.py`
- `scripts/agent/config_builders.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/config_dataclasses.py`
- `scripts/agent/production_config_validator.py`
- `config/agent.toml`
- `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` (doc-side comparison target)

## Required Changes
- Classify each `memo2.md` item (P1-1 providers normalization, P1-2 MCP timeout keys,
  P1-3 result-token cap, P1-4 providers facade delegation, P2-1 unified validation,
  P2-2 config consistency) against the existing architecture with file/line evidence.
- Where a memo item is already implemented by an existing mechanism, cite the mechanism
  and mark the item satisfied.
- Where a residual gap is plausible (e.g. no documented budget relation between
  `McpServerConfig.call_timeout_sec` and server-internal timeouts such as
  `search_timeout_sec` in `config/web_search_mcp_server.toml`), confirm or reject it with
  evidence; confirmed gaps become follow-up issues.
- Update `memo2.md` status (expired/superseded header) after the classification, so it is
  not re-executed.

## Constraints
- The per-process config isolation design (`ConfigLoader.restrict_to`, adrrev008) must not
  be weakened: an agent-side facade may not cause MCP server processes to load cross-domain
  config files.
- No new config machinery may be created while an existing equivalent (shared loader,
  section builders, production validator) covers the same responsibility.
- Memo claims are treated as claims only; nothing from `memo2.md` enters a plan without
  filesystem evidence.

## Acceptance Criteria
- Every `memo2.md` item has a recorded verdict (already-implemented / gap-confirmed /
  rejected) with file/line citations.
- Gap-confirmed items (if any) are filed as separate follow-up issues.
- `memo2.md` carries a superseded/expired marker pointing to this issue's outcome.

## Testing Expectations
No code changes in this issue; no new tests required. Verification is evidence review
(grep/file citations) recorded in the classification. Follow-up issues from confirmed gaps
carry their own test expectations.

## Documentation Impact
`memo2.md` gets a status header. Only if a gap-confirmed follow-up changes behavior would
`docs/22_mcp/mcp_06_01_configuration-file-inventory.md` or agent config docs need updates —
handled by the follow-up, not here.

## Out of Scope
- Implementing any facade, settings module, or providers normalization in this issue.
- Creating or reviving `agent/settings.py`, `agent/providers.py`, `mcp/config.py`,
  `mcp/toll_gate.py`, or `mcp_settings.py`.
- Changing any `config/agent.toml` key.
- The stale reference at `conf.d/web-search-mcp:6` to a `search_providers` key that does
  not exist in `config/web_search_mcp_server.toml` — noted as an observation, handled as a
  separate follow-up only if confirmed.

## Dependencies
N/A: none

## Unresolved Questions
- Where the `memo2.md` phantom tree came from (another machine, an unpushed session, or a
  deleted worktree) — unknown; does not block the re-baseline.
- Whether the transport-level `call_timeout_sec` vs server-internal `search_timeout_sec`
  relationship is an operational problem in practice — needs confirmation.

## AI Implementation Instruction
Start from the verified facts in Background; never execute `memo2.md` as-is. Produce an
evidence-cited classification first. Do not add new config loading code without confirming
no existing mechanism already covers the claim. Respect `ConfigLoader.restrict_to`
boundaries in any proposal.

## Traceability
- **Workflow phase**: N/A: manually filed (from filesystem verification of `memo2.md`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-165529
- **Related target files**: `memo2.md`, `scripts/shared/config_loader.py`, `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/production_config_validator.py`, `config/agent.toml`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
