## Goal

Update `_SUBPROCESS_REACHABLE_CONFIGS` (lines 47-57): remove `mcp_dedup.toml` and its explanatory comment once the shared file is gone; the `*_mcp_server.toml` pattern already covers the replacement (REQ-004, AC-003).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- The code-side contract changes come from the sibling procedures cited above; this row only follows them.

## Design decisions
- Follow the sibling procedure's contract exactly; no new fixture abstraction beyond what the sibling's Validation plan implies.

## Alternatives considered
- N/A: test-only follower row.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_env_allowlist_integration.py`
### Procedure
1. Apply the changes described in Goal at the sites named in Reason/Repository Evidence; remove references to deleted APIs (discovery loader, cache clear, `[retry_class]` map, `mcp_dedup.toml`).
### Method
Edit in place; keep existing fixture names where consumers depend on them.
### Details
- Evidence for each site is in the plan's Implementation Target Files row (Verified column).

## Compatibility considerations
- Keep public fixture names and test class names stable where other tests or tooling reference them.

## Security considerations
- N/A: test edit.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py -q`; then the delivery-unit full-suite run (`uv run pytest -q`).

## Completion criteria
- Allowlist expectations match the post-Phase-4 config surface; `${ENV:...}` reachability assertions still pass against the spawned server processes.

## Out of Scope
- Production code changes (owned by the sibling procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file per Implementation | Completed | 2026-11-22 | 2026-11-22—mcp_dedup.toml removed from allowlist after seq 23 deletion; 8 green|
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—mcp_dedup.toml removed from allowlist after seq 23 deletion; 8 green|

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
- **Requirement ID**: REQ-004; AC-003
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `tests/agent/test_http_lifecycle_env_allowlist_integration.py`
