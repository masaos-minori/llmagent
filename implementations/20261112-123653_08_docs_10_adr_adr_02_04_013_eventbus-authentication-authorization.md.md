## Goal
Add an Implementation column with test file paths to ADR-013's Automated Tests table without changing any verified claim (`REQ-005`, `REQ-008` / `AC-5`, `AC-8`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The table header is `| Test | Verifies | Type | Blocking |` (checked); other ADRs carry an Implementation column.
- Resolved paths (search of `tests/`): `tests/eventbus/test_eventbus_auth.py` (publish/subscribe-without-token, wrong-role, DLQ and replay rejects, empty mappings, topic restriction, credential leakage, `TestProductionRouteWiring`, shared/admin-token tests), `tests/eventbus/test_eventbus_config.py` (config rejects, non-loopback host), `tests/eventbus/test_eventbus_consumer_authorization.py` (`TestConsumerPrincipalBinding`, `test_subscribe_ack_and_nack_return_403`, `test_rejected_ack_and_nack_change_no_delivery_state`). Rows that cite no test name (for example the one-generation publish and the audit-emission rows) are located by search at implementation; if none is found, report `Needs confirmation` and write no guessed path.
- Overlap: adrrev010 re-maps three Verification rows of the same table and must land first (Plan Assumptions); `rmcompat004` and adrrev017 edit other regions.
- Non-blocking caveat: this ADR sits exactly at its size ceiling (28647), so the added column fails `check_docs_structure.py` until the ceiling is re-recorded (see Details).

## Design decisions
- Copy each existing test reference into the new column as a file path plus node; leave every other cell unchanged.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Add the `Implementation` header and separator cells.
2. For each row, add the file path (and node where the row names one).
3. Append a `Current Decision Approval (pending)` line only if the Plan's approval policy requires one for a table change; otherwise report that none is needed.

### Method
- Node form: `tests/eventbus/test_eventbus_auth.py::test_publish_without_token`, matching ADR-006's Implementation cells.
- Verify every path with `rg -l` before writing; `check_adr_invariant_matrix.py` then verifies cited nodes.

### Details
- Size gate: `tools/check_docs_structure.py` records a per-file ceiling equal to the accepted size, so any growth of this document fails `check_docs_structure.py`. The ceiling table is outside this Plan's target files; re-recording it follows the existing ceiling re-record chore (`plans/done` / `implementations` docsize series). Report the new size; do not edit the tool here (non-blocking `Needs confirmation`).
- Count table rows before and after; no row is dropped. The Security Reviewer approval stays pending and is reported, not written.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`, `check_adr_preservation.py` (only intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- Every row has an Implementation cell with an existing path or a reported gap; no verified claim changed; the matrix checker passes.

## Out of Scope
- Re-mapping Verification rows (adrrev010); editing the Approval or Known Deviations sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` / `REQ-008` — Implementation column with test file paths
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
