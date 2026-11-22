# Verify the reduced `agent.toml` end to end and document the migration

## Priority
Medium

## Summary
Validate the reduced standard configuration as the deployment contract through integration tests, and document the old-to-new key migration, owners, and the explicit-default policy.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 6). The reduction changes tool visibility, schema discovery, approval, plan mode, required capabilities, Memory embedding, database maintenance, and reload together, so unit tests alone may not expose a mismatch in a real deployment. Which integration tests already cover startup with the real `config/agent.toml` is `Needs confirmation`.

## Problem
Without an end-to-end check and a migration reference, an operator with an old configuration gets unknown-key failures with no guidance, and the meaning of retained explicit defaults is undocumented.

## Reason for Change
Verification and operability of the whole reduction; it can only be done after the earlier issues land.

## Implementation Intent
Quality is measured by the number of duplicated sources and ownership violations, not by TOML line count. The real standard file is validated strictly, an old key produces a specific migration message at startup, and the reference lists owner process, type, unit, default, reloadability, and restart requirement for each key.

## Target Files or Areas
- `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`
- `scripts/agent/production_config_validator.py`
- Integration tests under `tests/integration/` (the exact new files `Unknown`)
- The Agent configuration reference and migration documentation under `docs/` (found through `docs/00_index.md`)
- A lint or CI check for long TOML comments and unknown keys (a new `tools/` check, `Unknown`)

## Required Changes
- Run startup, MCP discovery, approval, plan mode, reload, Memory, and database maintenance integration tests against the reduced standard `config/agent.toml`.
- Write the migration table from each old key to its new key or owning file.
- Make each removed key a fatal validation error that names the replacement.
- Document owner process, type, unit, default, reloadability, and restart requirement for each key, and state the policy of keeping explicit values equal to code defaults.
- Add the long-comment lint and an unknown-key CI check.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- Follow the Current-Specification-Only policy and `skills/DESIGN.md` Docs content policy: the migration table lives in one place, and the reference does not copy values that the generator already owns.
- Do not run production-affecting checks against `/opt/llm`.

## Acceptance Criteria
- [ ] The standard `agent.toml` passes strict validation.
- [ ] The Agent reads only the settings it needs, and the RAG Pipeline MCP starts from its own file.
- [ ] The sources of tool schema, inventory, and safety metadata are documented and unique.
- [ ] An old key causes a startup error with specific migration guidance.
- [ ] The reduction removed duplicated ownership; it did not merely omit values.

## Testing Expectations
- Integration tests listed under Required Changes; the new lint and CI checks; documentation checkers listed in `routing.md` Tools; `tools/generate_reference_table.py --check`.

## Documentation Impact
Yes. Configuration reference, migration table, and ownership; use the generated-reference tooling where a table is generated.

## Out of Scope
- The individual reductions of `issues/20261120-114209_agentcfg001_tool-policy-mode.md` to `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`.

## Dependencies
- Depends on `issues/20261120-114209_agentcfg001_tool-policy-mode.md`, `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`, `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`, `issues/20261120-114212_agentcfg004_config-ownership-split.md`, and `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`.

## Unresolved Questions
- `不明`: the location and generator of the configuration reference.
- `不明`: whether the long-comment lint is a new tool or an extension of an existing check.

## AI Implementation Instruction
Do not start before the earlier issues land. Prefer extending existing tools over adding a script. Do not write ADR approval statements. Stop and report if the standard file fails validation because of an unfinished earlier issue.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114214
- **Related target files**: `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `scripts/agent/production_config_validator.py`
