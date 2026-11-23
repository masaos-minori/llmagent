# Implementation procedure: REQ-004 — Per-key reference and explicit-values-equal-defaults policy in the agent config reference doc

## Goal

Complete REQ-004 (the per-key configuration reference for `config/agent.toml`) in the target document, including the explicit-values-equal-code-defaults policy statement.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- REQ-004 stays in force and its target file is unchanged; the plan is not amended.
- Verification against the live sources: `config/agent.toml` states values that differ from the code default for 20 keys (`allowed_root`, `allowed_tools`, `plan_blocked_tools`, `approval_shell_safe_prefixes`, `approval_high_risk_branches`, `context_token_limit`, `history_protect_turns`, `http_timeout`, `llm_max_tokens`, `llm_url`, `memory_embed_url`, `memory_min_importance`, `sse_heartbeat_timeout`, `sse_reconnect_max`, `tool_concurrency_limits`, `sqlite_vec_so`, `sqlite_retention_max_age_days`, `sqlite_archive_dir`, plus the two required database paths and the MCP blocks), and only `tool_concurrency_limits` carries an explanatory comment in the file. The policy paragraph is normative, so the section does not claim the current file is compliant; reconciling the file or adding the comments is a separate decision for the owner. The `[diagnostics]` keys are equal to their defaults.

## Design decisions

- Units are named only where the reading code establishes them; every other value is marked as carrying no unit. Rows are built from the live sources (dataclass defaults, `config_field_registry.py`, the call sites that read each value), not asserted from the key name.
- The deployed value is not copied into the document (`skills/DESIGN.md` No concrete configuration values), so the reference records the code default and names `config/agent.toml` as the canonical source of the operational value. Reload classes reuse the categories `agent/services/config_reload.py` defines.

## Alternatives considered

- N/A: the plan's own Design decisions already record the table-shape choice; nothing new was considered.

## Implementation
### Target file
- `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure
1. Regenerate the guarded block after the REQ-003 generator change.
2. Add the per-key reference section: reading component, value type, unit, code default, reload class.
3. Add the explicit-values-equal-code-defaults policy paragraph.
4. Run the documentation checkers named by `rules/tool-gates.md`.

### Method
- Table header and heading wording avoid the patterns `tools/check_docs_content_policy.py` `check_field_type_table` and `check_docs_quality.py` flag; both were confirmed with the owner before the section was written.
- The policy paragraph states only what the toolchain can back (`config-key-ownership`, `check_docs_consistency.py` `configkey`).

### Details
- 77 rows: 68 top-level keys, 6 `[mcp_servers.*]` key shapes, 2 `[diagnostics]` keys. Document is 14.7 KB, inside the 32768-byte ceiling.
- The generator covers only the guarded migration block; the per-key reference is not generator-backed, so `generate_reference_table.py --check` verifies the block and the doc checkers verify the rest. The section was built from the live sources through a throwaway extraction script, not through a tool change.
- Full form rather than the lightweight fill: the recorded owner decisions and the five named checks do not fit a 60-line lightweight row.

## Compatibility considerations

- N/A: documentation-only change.

## Security considerations

- N/A: no runtime behavior changes.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria

- Every key `config/agent.toml` defines has a row with a source-verified unit or an explicit no-unit marker, the policy paragraph states the rule and its audit method, and the five checks above report no findings.

## Out of Scope

- Changing `skills/DESIGN.md` or the content-policy and quality gates; adding the policy statement to `config/agent.toml`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded block | Completed | 2026-11-23 | 2026-11-23 | Validator-mapping row now correct |
| 2 | Write the per-key reference and the policy paragraph | Completed | 2026-11-23 | 2026-11-23 | Owner decisions on units, table shape, value policy |
| 3 | Run the documentation checkers | Completed | 2026-11-23 | 2026-11-23 | Five checks clean |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (per-key reference and explicit-values-equal-defaults policy)
- **Source issue**: `issues/done/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
