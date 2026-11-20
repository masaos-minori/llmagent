# Remove the duplicated system prompt key and pin the standard configuration with a snapshot

## Priority
Medium

## Summary
Keep one default system prompt, prune every removed field from the reload and validation registries, and pin the standard `agent.toml` with an effective-configuration snapshot that proves explicit values override code defaults.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 5). The comment cleanup and the typed staged reload parts of that backlog item are not repeated here: they belong to `issues/20261117-123022_adrchk022_history-comment-removal.md` and `issues/20261119-145303_cliplc005_staged-reload-transaction.md`, which were updated to carry them.

Evidence (`Explicit in code`, by reading): `config/agent.toml` holds `system_prompt_tool` (line 243) and `[system_prompts].default`, and a parse of the file shows the two values are identical; the builders, the reload registry, the production valid-key set, and the tests recognize both (the last claim is from the backlog and `Needs confirmation`).

## Problem
Two keys carry one prompt. When the earlier issues remove or move fields, entries left in the field registry, startup-only classification, and service sync can cause unknown-key errors, reload differences, or silent defaults.

## Reason for Change
Maintainability and reload consistency once the field removals of the earlier issues are decided; not time-sensitive before them.

## Implementation Intent
`system_prompts.default` is the only default prompt. After each removal or move, the registries, classifications, and sync paths hold no trace of the field, and a removed key is reported as an unknown key. The standard file keeps explicit values that equal code defaults as the deployment contract, and a snapshot test pins the effective configuration.

## Target Files or Areas
- `config/agent.toml`
- `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/config_builders.py`
- `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_reload.py`, `scripts/agent/services/config_section_reload.py`, `scripts/agent/services/config_service_sync.py`
- `scripts/agent/production_config_validator.py`
- `tests/agent/test_config_builders.py`, `tests/agent/services/test_config_reload.py`, `tests/agent/services/test_config_reload_classification.py`, `tests/agent/test_production_config_validator.py`

## Required Changes
- Remove `system_prompt_tool` from the dataclass, builder, reload registry, production valid-key set, TOML, and tests; make `system_prompts.default` the only default and apply its change safely to the conversation state on reload.
- Remove each field deleted or moved by `issues/20261120-114209_agentcfg001_tool-policy-mode.md` to `issues/20261120-114212_agentcfg004_config-ownership-split.md` from the field registry, the startup-only classification, and service sync.
- Add an effective-configuration snapshot of the standard `config/agent.toml` and a test that an explicit TOML value takes precedence over the code default.
- Keep every explicit value that equals its code default.

## Constraints
- Follow the Current-Specification-Only policy: no alias for `system_prompt_tool`.
- Do not delete a TOML value only because it equals the code default.
- Change only the Target Files; if another file must change, stop and report a scope amendment.

## Acceptance Criteria
- [ ] The prompt has one source.
- [ ] A removed key is reported as an unknown key and is never ignored silently.
- [ ] Explicit values equal to code defaults remain in the standard file.
- [ ] Startup and reload use the same typed schema for the removed fields.
- [ ] The snapshot test passes against the real `config/agent.toml`.

## Testing Expectations
- Prompt reload; removed-key rejection; production validation of the real `config/agent.toml`; effective-configuration snapshot; reload prepare and commit failure paths touched by the removals.
- Run ruff, mypy, and the affected tests.

## Documentation Impact
Yes. The single default prompt and the removed key.

## Out of Scope
- History-style comment cleanup (`issues/20261117-123022_adrchk022_history-comment-removal.md`); typed staged reload and rollback (`issues/20261119-145303_cliplc005_staged-reload-transaction.md`).

## Dependencies
- Depends on `issues/20261120-114209_agentcfg001_tool-policy-mode.md`, `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`, `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`, and `issues/20261120-114212_agentcfg004_config-ownership-split.md` for the fields to prune. Blocks `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`.
- Related: `issues/20261119-145303_cliplc005_staged-reload-transaction.md` provides the typed reload model that this issue prunes; it should land first.

## Unresolved Questions
- `不明`: which tests, besides those listed, reference `system_prompt_tool`.

## AI Implementation Instruction
Prune only fields that the earlier issues actually removed. Do not add an alias for a removed key. Stop and report if a registry entry still has a live consumer.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114213
- **Related target files**: `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/config_builders.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_reload.py`, `scripts/agent/services/config_section_reload.py`, `scripts/agent/services/config_service_sync.py`, `scripts/agent/production_config_validator.py`, `tests/agent/test_config_builders.py`, `tests/agent/services/test_config_reload.py`, `tests/agent/services/test_config_reload_classification.py`, `tests/agent/test_production_config_validator.py`
