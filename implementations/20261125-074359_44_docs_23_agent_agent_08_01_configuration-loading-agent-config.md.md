## Goal

State that the hot-reloadable scope is exactly the registry entries with `hot_reloadable=True`, that startup-only fields stay pending, and that every MCP server-definition change is restart-required (REQ-003, REQ-008, REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: `### Hot-Reloadable Scope` (line 47) names `context_char_limit`, `context_compress_turns`, and `context_token_limit`, which the registry marks `hot_reloadable=False`.

## Design decisions
- The scope list is stated as the registry-derived set rather than a hand-maintained list, so the document cannot drift from `config_field_registry.py`.
- The three context limits move to the startup-only list, the set `startup_only_for` returns.

## Alternatives considered
- N/A: the list is the claim being corrected.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure

### Method
- Rewrite `### Hot-Reloadable Scope` to the registry-derived set and add the startup-only and MCP restart-required statements.

### Details
- No other section is changed; the `Related Documents` heading stays.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: no configuration values are documented.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The scope list matches the registry, the three context limits appear as startup-only, and the MCP restart rule is stated.

## Out of Scope
- The hot-reload command behavior document (row 43) and the generated artifacts (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-008, REQ-014; AC-2, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`
