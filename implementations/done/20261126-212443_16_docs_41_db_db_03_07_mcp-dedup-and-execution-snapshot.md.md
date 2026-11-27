## Goal

Link each state and recovery invariant in the dedup store document to its automated test, and
confirm the runbook content and the absence of any `mcp_dedup.toml` requirement (REQ-005,
REQ-006, AC-4, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file has no test citations (re-verified 20261126), so the invariant-to-test links are the
  row's main work.
- The runbook content is present at lines 69 and 280 (store migration, identity initialization,
  legacy handling, rollback, operator resolution) and is confirmed, not rewritten.
- `mcp_dedup.toml` appears only as a historical removal note at
  `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:88`; that file is a
  reference, not a target, so this row verifies the state without editing it.

## Design decisions
- Each invariant cites the test that proves it by file and test name; invariants with no proving
  test are reported rather than asserted.
- The runbook section is checked for consistency with the implemented store behavior, not
  extended.

## Alternatives considered

N/A: the document already owns the store and snapshot description; only the verification
references are added.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
### Procedure
- Add a verification reference to each state and recovery invariant, naming the test that proves
  it.
- Confirm the runbook content against `scripts/shared/mcp_dedup.py` (`resolve_store`, store
  identity, lease acquisition) and correct any statement that contradicts the code.
- Run the `mcp_dedup.toml` reference sweep and record that only the historical note remains.
### Method
- Locate each invariant with grep, read the limited range, and verify the named test before
  writing it.
### Details
- Proving tests: `tests/shared/test_mcp_dedup.py`
  (`test_acquire_creates_owned_pending_row`, `test_completed_snapshot_mismatch_is_replay_unavailable`),
  `tests/mcp_servers/test_mcp_dispatch_concurrency.py`
  (`test_100_concurrent_callers_execute_handler_exactly_once`, `test_lost_lease_surfaces_without_redispatch`).

## Compatibility considerations

N/A: documentation-only change; no pinned counts change.

## Security considerations

N/A: documentation-only change describing existing store behavior.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/shared/test_mcp_dedup.py tests/mcp_servers/test_mcp_dispatch_concurrency.py`
- `grep -rn "mcp_dedup.toml" docs/ config/ deploy.sh` — only the historical removal note remains

## Completion criteria

- Every state and recovery invariant has a verification reference to a test that exists and
  passes, the runbook content matches the implementation, and no document or deployment artifact
  requires `mcp_dedup.toml`.

## Out of Scope

- No store behavior change; the historical note in the reference ADR is not edited.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | Added proving-test references to the four state/recovery invariants (lease state machine, terminal immutability, identity start states, operator resolution runbook) and the lease_conflict side note. Runbook confirmed against resolve_store(); stale claim corrected: the runbook has no rollback content and resolve_store itself archives the file as <path>.corrupt-<ts> rather than the operator removing it. legal_hold_states claim has no proving test (reported, not asserted). mcp_dedup.toml sweep: only the historical removal note remains (deploy.sh does not exist in the repo). |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving tests | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; 118 passed (test_mcp_dedup.py + test_mcp_dedup_identity.py + test_mcp_dispatch_concurrency.py) |

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
- **Requirement ID**: `REQ-006` (invariant-to-test links), `REQ-005` (`mcp_dedup.toml` sweep)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`