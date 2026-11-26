## Goal
- Make `pending_timeout_minutes` explicit in the `[dedup]` table of `config/file_read_mcp_server.toml` with the validator default (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one added key in the `[dedup]` table of `config/file_read_mcp_server.toml`.
- Out of scope: any other key, the validator, and the store identity (unchanged by design).

## Assumptions
- Verified in Step 3a: the table sets `db_path`, `retention_days`, `lease_seconds`, and `max_attempts` only, and no shipped `config/*_mcp_server.toml` sets `pending_timeout_minutes` (`rg pending_timeout_minutes config` found no match).
- The value 10 equals `DEFAULT_PENDING_TIMEOUT_MINUTES` (`scripts/shared/mcp_dedup_config.py`), so the config fingerprint and the dedup store identity do not change; the key is validated (range 1..1440) and has no server-side runtime consumer (the stale-pending sweep is Agent-side), see the Plan's UNK-01.
- The file is already copied by `deploy/deploy.sh`; modifying an existing file needs no deploy script change.

## Design decisions
- Insert the key right after `retention_days` and keep the existing order of the other keys.

## Alternatives considered
- N/A: single-line configuration change; removing the key from the validator was rejected in the Plan because it would change the fingerprint.

## Implementation
### Target file
`config/file_read_mcp_server.toml`

### Procedure
1. In the `[dedup]` table, add `pending_timeout_minutes = 10` on the line after `retention_days`.

### Method
- No other change; do not alter `db_path`, `lease_seconds`, or `max_attempts`.

### Details
- The real-file test of the shipped tables (the shipped-config test procedure, seq 05) asserts the key is present and the fingerprint equals the default fingerprint; write that test first and confirm it fails before this edit.

## Compatibility considerations
- N/A: the explicit value equals the default, so behavior and the store fingerprint are unchanged.

## Security considerations
- N/A: no secret or credential involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py tests/mcp_servers/test_config_isolation_fail_closed.py`; the configuration and documentation checkers named in `rules/tool-gates.md` "When to run which tool".

## Completion criteria
- The `[dedup]` table contains `pending_timeout_minutes = 10`; the file still loads through the typed validator; the shipped-config test passes for this file.

## Out of Scope
- Other keys, other files, and the validator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the key described in Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation commands named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (explicit pending timeout in the shipped dedup table)
- **Source issue**: issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-113156_mcpdd001_dedup-keyless-config-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-124822
- **Related target files**: `config/file_read_mcp_server.toml`
