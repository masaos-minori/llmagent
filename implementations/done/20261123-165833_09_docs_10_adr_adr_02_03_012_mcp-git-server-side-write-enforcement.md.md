## Goal

Restore the ADR-012 INV-04 Verification row to Blocking citing the new tests and remove its pending bullet.

## Scope
**Release unit**: N/A: not part of a release unit

One ADR file. Run this procedure after the procedures that create the tests it cites (earlier `seq` values 01 to 06); it cites test node ids that must exist and pass.

## Assumptions

- Row at line 170 and pending bullet at line 204 (read in Step 3a).

## Design decisions

- Cite the tests from procedure 05 and set `Blocking` to `Yes`; remove the AAL-036 bullet as a revert.

## Alternatives considered

N/A: single mechanical change.

## Implementation
### Target file
`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`

### Procedure
1. Edit the INV-04 row.
2. Remove the AAL-036 bullet.
3. Run the checkers.

### Method
- Cite `tests/mcp_servers/git/test_git_approval_independence.py::<Class>::<test>` nodes.

### Details
- Other pending bullets (AAL-014, AAL-015) stay.

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

- The INV-04 row is Blocking with passing cited tests.
- The AAL-036 bullet is gone.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Row read at line 170 and bullet at 204 as stated; the row is `Yes` citing `TestStageThreeWithoutApprovalState` and `TestGitPackageHasNoApprovalDependency`; the AAL-036 bullet removed. AAL-014 and AAL-015 untouched. |
| 2 | Run the documentation checkers named in Validation plan | Completed | 2026-11-23 | 2026-11-23 | `check_adr_structure.py` and `check_adr_invariant_matrix.py` clean; both cited nodes pass in `.github/run_cited_adr_tests.py`. Length finding: the required sections and the three Execution Status tables alone exceed the 60-line lightweight target, so only the bodies are kept minimal. |

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
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
