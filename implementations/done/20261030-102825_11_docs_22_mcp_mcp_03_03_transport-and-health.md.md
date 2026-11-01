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
- Land after rows 01-04 so the doc describes shipped behavior (plan Phase 6). Rows 01-04 are
  landed/verifying in this batch: `derive_idempotency_key` shipped in `shared/http_transport.py:62-73`
  (deterministic `sha256(method\n tool_name\n canonical-JSON(args)\n uid)`, replacing the previous
  per-call `uuid.uuid4()`), durable store + bounded overlay shipped in `mcp_servers/dispatch.py` (staged).
- Adversarial verification finding 2026-10-31: this file contains **no** existing idempotency-key,
  UUID4, or cache text (`rg -i 'uuid|idempotency'` clean) — the Procedure's "update the existing
  idempotency-key text" premise is false for this target. The shipped key/cache prose lives in
  `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:57-66` ("Idempotency and retry": key ownership,
  cache keying, TTL/eviction), which is not a frozen target row. Owner decision 2026-10-31: keep
  the frozen path; row 11 adds a new "Idempotency key derivation and durable dedup" section to
  this file (it documents `HttpTransport`, which now derives and emits the key), and does **not**
  silently edit `mcp_03_01`. If the post-landing stale detector flags the `mcp_03_01` cache/TTL
  prose as outrunning shipped behavior (overlay is now store-fed), a minimal wording adjustment
  there is authorized as an additional target of the row 11 cycle, recorded in this doc's Notes.

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
| 1 | Update key + dedup sections | Completed | 2026-10-31 | 2026-10-31 | Step 1's "update existing UUID4 text" premise stayed false (Assumption finding): file had no key text, so a new "Idempotency Key Derivation and Durable Dedup" subsection was added under HttpTransport per the owner decision. `mcp_03_01` not edited: the stale detector on this procedure is clean and `check_docs_consistency --domain mcp` reports no cross-doc conflict, so the authorized additional-target edit was not needed. Replay table not duplicated — cross-links `db_03_07`. Added `db_03_07_mcp-dedup-and-execution-snapshot.md` to front matter `related:`. |
| 2 | Run the docs validation checkers (`routing.md` Tools) | Completed | 2026-10-31 | 2026-10-31 | `check_docs_structure` (target file), `check_docs_content_policy`, `check_docs_consistency --domain mcp`, `check_docs_quality` all pass; `stale_detector` on this procedure: not stale. |

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
