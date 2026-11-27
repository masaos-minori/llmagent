# Implementation Procedure — scripts/mcp_servers/mdq/health_check.py

## Goal

Make readiness prove the stored FTS5 definition and the trigger synchronization, publish the
canonical identity through the health body `details` map, and report the readiness conditions through
the closed capability vocabulary (REQ-001, REQ-002, REQ-003, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002, REQ-003, REQ-006. Acceptance criteria: AC-1, AC-2.

## Assumptions
- Full form: this row changes what `/health` guarantees, which is a public contract for the health
  registry and its consumers.
- The functional probe runs against a scratch in-memory apply of the canonical DDL; the live store is
  only inspected, so readiness never writes (Plan Assumption, and the transaction it would need is
  mdqmcp005's scope).
- The identity is read from `scripts/shared/mdq_schema.py` (new) through `scripts/mcp_servers/mdq/db_schema.py`
  (row 1); this document does not compute it.
- The five readiness names stay internal condition names; no state or reason code is added
  (UNK-02), so the mapping is recorded in the docs row, not in the contract.
- `tests/mcp_servers/mdq/test_mdq_fts_schema.py` (row 6) is a Plan row with its own document, so it is
  not listed as a companion here.

## Design decisions
- Readiness compares the stored statement text and the normalized trigger SQL through the shared
  fingerprint comparison (row 2) rather than by name sets.
- The condition name is published as a `details` entry; `ready` continues to be derived from the
  dependency map in `scripts/mcp_servers/health_response.py` (line 65), so no new vocabulary is
  invented.

## Alternatives considered
- Probe rows in the live store: rejected (inspect-only rule, and a probe write would need a
  transaction owned by mdqmcp005).
- Add readiness names as capability states: rejected; the contract owner's decision is required
  (UNK-02).

## Implementation
### Target file
`scripts/mcp_servers/mdq/health_check.py`

### Procedure
- Replace the name-set checks in `_check_schema_health` (lines 55-89): the table-name checks at
  lines 64-69 and the trigger-name checks at lines 71-79 become a comparison of the stored FTS5
  statement text and the normalized trigger SQL against the canonical text.
- Add the functional insert, update, and delete probe on a scratch apply of the canonical DDL, using
  `apply_ddl_in_memory` from the shared fingerprint module, and keep the live probe read-only.
- In `_collect_dependencies` (line 114), add the identity to `details` (line 136) and the readiness
  condition name to the same map.

### Method
- The scratch apply is opened, probed, and closed inside the same call, so the production connection
  used at lines 155-168 is never written to.
- A drift, a no-op trigger, or an empty FTS index over rows produces a dependency entry, which is what
  makes `ready` false; the condition name only labels which case it is.

### Details
- Mapping: healthy to the `ok` capability state, rebuild in progress and degraded to `degraded`,
  inconsistent to `degraded`, failed to `unavailable`, each with an existing reason code, so no state or
  code is added (UNK-02).
- The existing health keys (`service`, `database`, `allowed_dirs_count`, `deny_all`, the index counts)
  keep their names and positions, so the preserved-key assertions in the companion stay valid.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
  - Procedure: move the plain-table fixtures (lines 68-79, 128-136, 165-173) onto the real FTS5
    definition; the corrupt case `test_fts5_query_failure_returns_ready_false` (line 551) on the
    fixture at lines 219-223 now fails through the definition comparison instead of the missing
    `chunks_fts` column; the key-presence assertions stay unchanged.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health_endpoint.py` — readiness refuses
    a plain table named `chunks_fts` and the preserved keys are still present.

## Compatibility considerations
- Overlap with the mdqmcp001 plan on this file and on `docs/22_mcp/mcp_04_04_mdq.md` is a compatible
  ordering overlap: this Plan executes after it per the dependency bullets.
- The health body gains entries; consumers that read only the existing keys are unaffected.

## Security considerations
- The published identity is a hash of canonical DDL text; no path, secret, or row content is added to
  the health body, consistent with the non-sensitive health shape mdqmcp001 defines.

## Rollback considerations
- Reverting restores the name-based checks; a store that was refused under the definition comparison
  is accepted again, so no data change is involved.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_fts_schema.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A plain table named `chunks_fts` or a no-op trigger cannot pass readiness (AC-1); the identity and
  the condition name appear in the health body `details` map (AC-2).

## Out of Scope
- The posture status change for an empty FTS index (row 5); the fingerprint comparison itself
  (row 2); the identity computation (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 2 and Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 15), `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` (row 16) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-006 (readiness proves the definition, probes
  synchronization, publishes the identity, maps onto the closed vocabulary)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/mcp_servers/mdq/health_check.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
