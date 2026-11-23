## Goal

Restore the ADR-003 INV-03, INV-04, INV-07 Verification rows to Blocking citing the new tests, remove the three pending bullets, update the manual-review note.

## Scope
**Release unit**: N/A: not part of a release unit

One ADR file; runs after the procedures that create the tests it cites (`seq` 01, 02, 04).

## Assumptions

- Rows 254 (INV-04), 256 (INV-03), 259 (INV-07), bullets 338-340, note 280: all read as stated in Step 3a.

## Design decisions

- Set `Blocking` to `Yes` and replace `Not verified` with the node ids from procedures 01, 02, 04.
- Remove the AAL-033, AAL-034, AAL-035 pending bullets as a revert; write no approval text.

## Alternatives considered

N/A: the maintainer chose to restore the rows to Blocking, which is what the issue asked for.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Edit the three rows, remove the three bullets, reword the INV-03 Manual Review line.
2. Run the checkers in Validation plan.

### Method
- Cite nodes as `tests/<path>::<Class>::<test>` so `.github/run_cited_adr_tests.py` extracts them.

### Details
- Keep row types and other pending bullets as is.

## Compatibility considerations

N/A: documentation only; the Verification table and index must keep agreeing (`tools/check_adr_invariant_matrix.py`).

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python .github/run_cited_adr_tests.py`

## Completion criteria

- Three rows Blocking with passing cited tests; three bullets gone; no approval text written.

## Out of Scope

- Any file other than the target file; any change under `scripts/` or `config/`; approval text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Rows and bullets read at the stated lines; the three rows are `Yes` with the node ids from procedures 01, 02, 04; bullets removed; the Manual Review line reworded to state the test and keep review as a secondary trigger. |
| 2 | Run the documentation checkers named in Validation plan | Completed | 2026-11-23 | 2026-11-23 | `check_adr_structure.py` and `check_adr_invariant_matrix.py` clean; `.github/run_cited_adr_tests.py` reports all cited nodes passing. Length finding: the required sections and the three Execution Status tables alone exceed the 60-line lightweight target, so only the bodies are kept minimal. |

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
