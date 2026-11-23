## Goal

Restore the ADR-003 INV-03, INV-04, and INV-07 Verification rows to Blocking citing the new tests, remove the three pending bullets, and update the manual-review note.

## Scope
**Release unit**: N/A: not part of a release unit

One ADR file. Run this procedure after the procedures that create the tests it cites (earlier `seq` values 01 to 06); it cites test node ids that must exist and pass.

## Assumptions

- Rows at lines 254 (INV-04), 256 (INV-03), 259 (INV-07), pending bullets at lines 338-340, and the manual-review note at line 280 (read in Step 3a).
- The new tests exist and pass before this procedure runs.

## Design decisions

- Set `Blocking` to `Yes` and replace `Not verified` with the cited node ids from procedures 01, 02, and 04.
- Remove the three `Current Decision Approval (pending)` bullets for AAL-033, AAL-034, AAL-035 as a revert; write no approval text.

## Alternatives considered

Keep the rows Non-Blocking with the tests cited: rejected, the maintainer chose to restore Blocking.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Edit the three Verification rows.
2. Remove the three pending bullets.
3. Reword the INV-03 line of `### Manual Review` so it no longer says there is no dedicated test.
4. Run the checkers in Validation plan.

### Method
- Cite nodes as `tests/<path>::<Class>::<test>` so `.github/run_cited_adr_tests.py` extracts them.

### Details
- Keep the INV-03 row type `Integration` and the write-classification row as is.
- Do not edit other pending bullets (INV-05/08/09 notes stay).

## Compatibility considerations

N/A: documentation only; the Verification table and index must keep agreeing (`tools/check_adr_invariant_matrix.py`).

## Security considerations

N/A: documentation only; no approval text, approver, or date is written, since an entry is removed as a revert.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python .github/run_cited_adr_tests.py`

## Completion criteria

- The three rows are Blocking with passing cited tests.
- The three pending bullets are gone and no approval text was written.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (restore Blocking rows and close the ledger entries)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
