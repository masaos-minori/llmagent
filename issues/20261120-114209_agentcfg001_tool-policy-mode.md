# Replace `allowed_tools` with an explicit tool exposure policy mode

## Priority
High

## Summary
Define one closed tool exposure policy so that the meaning of an empty list is identical in the configuration comment, the production validator, preflight, the RuntimeToolRegistry policy step, and reload.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 1).

Evidence (`Explicit in code`, by reading and `rg`): the `allowed_tools` comment in `scripts/agent/config_dataclasses.py` (line 216) says an empty list means all tools are allowed; `scripts/agent/production_config_validator.py` (lines 279-281) rejects `allowed_tools=[]` as "every tool is denied"; `scripts/agent/tool_policy.py` (lines 558-561) denies a tool that is not in `cfg.tool.allowed_tools`; `scripts/shared/runtime_tool_registry.py` (lines 209-226) applies `allowed_tools` as an allowlist. The names `tool_policy_mode` and `disabled_tools` appear nowhere in the repository, so they are proposals. Whether an empty list hides every tool after `/reload` is `Needs confirmation`. Related archived work to re-verify first: `plans/done/20261119-094759_adrchk004_hot-reload-validation.md` (validated allowed-tool fields on reload).

## Problem
The documented, validated, and runtime meanings of an empty `allowed_tools` disagree. Removing the long tool-name lists from `agent.toml` without fixing this contract could leave every tool unusable, or change tool visibility only after a reload.

## Reason for Change
Correctness of tool visibility. It is the first step of the `agent.toml` reduction: the later issues remove tool lists and metadata maps and need one stable exposure contract. Nothing else makes it time-sensitive.

## Implementation Intent
Live discovery behind a passing Security Posture is the base of exposure. An environment-specific stop is a denylist. A regulated environment that needs an explicit allowlist selects a dedicated mode. A missing or unknown mode, or a list that contradicts the mode, is rejected at startup and at reload with the same result. No fallback to the static tool registry is introduced.

## Target Files or Areas
- `config/agent.toml`
- `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`
- `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_service_sync.py`
- `scripts/agent/production_config_validator.py`, `scripts/agent/tool_policy.py`
- `scripts/shared/runtime_tool_registry.py`
- `tests/agent/test_production_config_validator.py`, `tests/shared/test_runtime_tool_registry.py`

## Required Changes
- Add a closed `tool_policy_mode` with the values `discovered` and `explicit_allowlist`.
- Add `disabled_tools`; reject a name that is not a known tool at startup.
- In `discovered` mode keep the registry's base visibility and apply only the denylist; reject `allowed_tools` in this mode.
- In `explicit_allowlist` mode require a non-empty `allowed_tools`; an empty list is a fatal error.
- Make `check_preflight()` and `RuntimeToolRegistry.apply_policy()` mode-aware.
- Make the validator, builder, reload registry, and service sync apply one contract; startup and reload give the same result.
- Correct the "Empty = all tools allowed" comment.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (`governance_01`, `governance_05`); do not write or simulate that approval.
- Follow the Current-Specification-Only policy: no migration window, alias, shim, or tolerant fallback for the old meaning of `allowed_tools`.
- The new mode names are proposals; keep the change within the Target Files.

## Acceptance Criteria
- [ ] In `discovered` mode, live-discovered tools are usable.
- [ ] Only a disabled tool is hidden from the LLM and rejected at preflight.
- [ ] An empty `allowed_tools` in `explicit_allowlist` mode is rejected at startup.
- [ ] Startup and reload yield the same visibility.
- [ ] The comment, validator, runtime, and tests give an empty list the same meaning.

## Testing Expectations
- `discovered` mode with and without a denylist; `explicit_allowlist` with a normal and an empty list; unknown mode and unknown tool name; visibility preserved after reload.
- Run ruff, mypy, and the affected tests; run `tools/generate_reference_table.py --check` after the configuration change.

## Documentation Impact
Yes. The Agent tool policy and configuration reference: modes, the meaning of each list, restart or reload behavior.

## Out of Scope
- Removing tool definitions and per-server tool name lists (`issues/20261120-114210_agentcfg002_tool-catalog-registry.md`); safety and approval metadata (`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`).

## Dependencies
- No prerequisite. Blocks `issues/20261120-114210_agentcfg002_tool-catalog-registry.md` and `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`.
- Related: `issues/20261119-145303_cliplc005_staged-reload-transaction.md` changes the same reload and field-registry code; either order works, but the second to land re-verifies its tests.

## Unresolved Questions
- `不明`: the shipped default mode and whether a mode change is hot-reloadable or restart-required.
- `不明`: whether ADR-003 or ADR-004 text names `allowed_tools` and so needs an approved wording change.

## AI Implementation Instruction
Write the contract tests first. Do not keep the old meaning of an empty list as a compatibility path. Do not write ADR approval statements. Stop and report if the reload path cannot apply the mode atomically.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114209
- **Related target files**: `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_service_sync.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/tool_policy.py`, `scripts/shared/runtime_tool_registry.py`, `tests/agent/test_production_config_validator.py`, `tests/shared/test_runtime_tool_registry.py`
