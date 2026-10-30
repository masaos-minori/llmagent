# Implementation Procedure: docs/22_mcp/mcp_03_03_transport-and-health.md

## Goal

Document the deterministic idempotency key and the durable dedup layer at the dispatcher
so the transport contract doc matches shipped behavior (REQ-001–REQ-003 key/dedup
contract; REQ-005 replay states).

## Scope

**In scope:**
- `docs/22_mcp/mcp_03_03_transport-and-health.md`: key-derivation section update + a
  durable-dedup subsection.

**Out of scope:**
- Code (rows 01-04); tracing doc (row 12).

## Assumptions

- Docs describe operational behavior and failure semantics only (`skills/DESIGN.md` Docs
  content policy).
- Land after rows 01-04 so the doc describes shipped behavior (plan Phase 6).

## Design decisions

- State the key contract as: caller-supplied key precedence (REQ-010), else
  deterministic `sha256(method + tool_name + canonical-JSON(args) + uid)` reused across
  retries and processes — wording follows the plan REQ-001/UNK-01 resolution, not code
  internals.
- Dedup subsection: `pending / completed / failed` states, interrupted classification via
  `pending_timeout_minutes` (new), the four REQ-005 replay outcomes in a decision table, and
  that `_duplicate_cache` is now a store-fed fast-path overlay.

## Alternatives considered

- N/A: doc-only row; structure follows the existing section flow of the file.

## Implementation
### Target file
`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure
1. Update the existing idempotency-key text where it describes per-call UUID4 keys.
2. Add the durable-dedup + replay-decision subsection.

### Method
Prose edits; keep the file's existing heading levels and terminology
(`X-Idempotency-Key` header name unchanged).

### Details
- Do not duplicate the config key table — cross-link `docs/41_db/db_03_07` (row 14) for
  retention/config specifics.

## Compatibility considerations

- N/A: docs-only change (sibling docs cross-links unchanged elsewhere).

## Security considerations

- N/A: no secret or internal-only detail published.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Docs checkers per `routing.md` Tools ("When to run which tool"): index/structure checks
  and `tools/stale_detector.py` on this file's claims after rows 01-04 land.

## Completion criteria

- The doc's key-derivation and dedup sections match the implemented behavior of rows
  01-04 with no stale claims (stale detector clean).

## Out of Scope

- Workflow tables (row 13/14 docs territory).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update key + dedup sections | Pending | — | — | After rows 01-04 |
| 2 | Run the docs validation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`–`REQ-003`, `REQ-005` (transport/dedup contract documentation)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: docs/22_mcp/mcp_03_03_transport-and-health.md
