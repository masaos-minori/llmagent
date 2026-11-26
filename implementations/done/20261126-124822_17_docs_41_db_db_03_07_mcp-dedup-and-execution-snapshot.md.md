## Goal
- Update the dedup document's `[dedup]` key list with ranges and resolve its contradictory statements about `pending_timeout_minutes` (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the config-keys paragraph and the stale-pending paragraph of `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`.
- Out of scope: invariant-to-test links and runbook consistency, which the design-docs update Plan owns.

## Assumptions
- Overlap judgment (Plan overlap check): the MCP design docs update Plan also modifies this document, for invariant-to-test links and a runbook consistency check. This document edits the config-key paragraph and the stale-pending wording; different passages; compatible; the phases rebase onto each other.
- Verified in Step 3a: the config-key paragraph lists `db_path`, `retention_days`, `lease_seconds` (1..3600), and `max_attempts` (1..10) and says the stale-pending timeout is Agent-side only (`db_03_07...md:134-138`), while a later bullet says `classify_stale_pending` uses `dedup.pending_timeout_minutes` (`:178`); the validator accepts `pending_timeout_minutes` (1..1440) and the shipped tables will set it explicitly, though no server-side consumer exists (Plan UNK-01).
- Written after the configuration and test procedures so it describes implemented state.

## Design decisions
- State both facts: the `[dedup]` table accepts and validates `pending_timeout_minutes` (and it is part of the config fingerprint), and the stale-pending classification is driven by the Agent-side `AgentConfig.pending_timeout_minutes`; fix line 178's wording to name the Agent-side setting.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. In the config-keys paragraph, add `retention_days` (default 14, accepted range 1..365) and `pending_timeout_minutes` (default 10, accepted range 1..1440, set explicitly in every shipped table, validated and included in the config fingerprint, with no server-side runtime consumer); keep `lease_seconds` and `max_attempts` as written.
2. Reword the stale-pending sentence so it states that the classification uses the Agent-side `pending_timeout_minutes` and that the `[dedup]` key does not drive it.
3. Reword the bullet at the stale-pending classification so it refers to the Agent-side setting, removing the `dedup.` prefix that implies the `[dedup]` key.

### Method
- Use values from `scripts/shared/mcp_dedup_config.py`; the code wins on any difference.

### Details
- Do not add invariant-to-test links here; another Plan owns them.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- The documentation checkers named in `rules/tool-gates.md` "When to run which tool", through `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The document lists both keys with ranges and defaults, and no passage contradicts the Agent-side ownership of the stale-pending timeout; the documentation gates report no finding.

## Out of Scope
- Invariant links, runbook content, and code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document described in Implementation > Procedure | Completed | 20261126-131011 | 20261126-131011 | Changed: docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261126-131011 | 20261126-131011 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain db, gates passed |

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
- **Requirement ID**: `REQ-006` (dedup configuration documentation)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
