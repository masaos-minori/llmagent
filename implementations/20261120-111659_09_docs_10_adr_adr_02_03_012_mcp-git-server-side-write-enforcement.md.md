## Goal

- Add the missing INV-04 row to the ADR-012 `### Automated Tests` table, citing a concrete test or recording `Not verified` (`REQ-003`, body matches the Index).
- Gated: show the Blocking change of INV-04 as a pending amendment when it is `Not verified` (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one table row (Plan step 3) and, gated, one pending bullet and the Blocking value of that row (Plan step 11, UNK-02).
- Execute step 1 before the Index procedure; step 11 only after the owner resolves UNK-02.

## Assumptions

- A search of `tests/mcp_servers/git/` for `independen` and `approval` found only `TestCrossRepoPathIndependence`, which is unrelated to Agent-side approval (checked in Step 3a); UNK-03 stays open until the implementer repeats the search for a test that calls the Git service without any approval state.
- With no test found, the row reads `Not verified (no automated test exists)` with `Blocking` `Yes` (the Gate the Index carries today) until the gated step changes it.
- No approval text is written; the pending bullet cites a ledger entry that the `governance_03` procedure creates.

## Design decisions

- Row text mirrors invariant INV-04: Git MCP validation does not assume or require Agent-side approval state.

## Alternatives considered

N/A: the Plan fixes the choice between a cited test and `Not verified`.

## Implementation
### Target file
`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
### Procedure
1. Search `tests/mcp_servers/git/` for a test showing that the validation pipeline runs without Agent approval state; if one is found, add the INV-04 row citing its full node, otherwise add the row with `Not verified (no automated test exists)`.
2. (Gated on UNK-02) When the row is `Not verified`, change its `Blocking` cell to `No` and add under `### Approval Record` a `- **Current Decision Approval (pending)**:` bullet that states the change and cites its `AAL-NNN` entry, following the existing bullets of this ADR.
### Method
- Direct table and bullet edits; the row sits with the other `Verifies` rows in invariant order.
### Details
- Type `Integration`; the pending bullet follows `governance_01` "ADR Pending Amendment Form" and keeps the ADR Status `Accepted`.

## Compatibility considerations

N/A: step 1 adds a row and changes no decision; step 2 uses the governed pending form.

## Security considerations

- Step 2 must not state or imply an approval; the bullet records that the maintainer's approval is not recorded.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The table has an INV-04 row and `uv run python tools/check_adr_invariant_matrix.py` exits 0 (AC-3).
- Gated: no `Not verified` row of this ADR is `Blocking` and the pending bullet cites an existing ledger entry (AC-5).

## Out of Scope

- Changing invariant text, and any approval statement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the INV-04 row (Plan step 3) | Pending | — | — |  |
| 2 | Show the INV-04 Blocking change in the pending form (Plan step 11) | Pending | — | — | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 11 - UNK-02 owner decision pending |
| 3 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (body matches the Index), `REQ-009` (pending Blocking amendment, gated)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
