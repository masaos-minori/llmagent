## Goal
Correct `Automatic retry (subprocess), manual restart (persistent)` in `security_01` to the recovery behavior ADR-004 and the code define (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Behavior: an Agent-launched subprocess server gets one startup retry (ADR-004 Exceptions; `retry_once_with_delay()` in `scripts/agent/shared/retry_helper.py` through `startup_mcp_starter.py`); a crashed subprocess server is restarted only on the next tool dispatch (`ensure_ready()`, `agent_10_05`); a persistent server is restarted manually. There is no background watchdog.
- The line 213 row (`fails to start after its single retry`) is already correct.
- Overlap: `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` / adrrev019 may edit other rows (compatible).

## Design decisions
- One table cell, no new section.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Replace the Recovery cell of the `MCP server unavailable` row.

### Method
- New cell: `One startup retry, then restart on the next tool dispatch (subprocess); manual restart (persistent)`.

### Details
- Do not claim an automatic or background retry.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain overview` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- The row states the single startup retry, the next-dispatch restart, and the manual restart for persistent servers.

## Out of Scope
- Runtime behavior; the line 213 row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-180138 | 20261112-180138 | docs/91_security/security_01_architecture-and-trust-boundaries.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-180138 | 20261112-180138 | checkers and check_docs_consistency --domain overview pass |

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
- **Requirement ID**: `REQ-005` — correct the subprocess retry wording
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`
