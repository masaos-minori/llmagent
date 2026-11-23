## Goal

Restore the ADR-002 INV-03 Verification row to Blocking citing the new test, remove its pending bullet, and narrow the checklist lines to INV-04.

## Scope
**Release unit**: N/A: not part of a release unit

One ADR file. Run this procedure after the procedures that create the tests it cites (earlier `seq` values 01 to 06); it cites test node ids that must exist and pass.

## Assumptions

- INV-03 row at line 231, pending bullet at line 298, checklist lines 341-342 (read in Step 3a). The INV-04 row and its bullet (AAL-032) stay unchanged.

## Design decisions

- Cite the parametrized node from procedure 03 and set `Blocking` to `Yes`.
- Checklist lines 341 and 342 then name only INV-04 as not verified.

## Alternatives considered

Leave the checklist wording: rejected, it would be false after the restore.

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`

### Procedure
1. Edit the INV-03 row.
2. Remove the AAL-031 bullet.
3. Edit checklist lines 341-342.
4. Run the checkers.

### Method
- Cite `tests/mcp_servers/test_config_isolation_import.py::test_<name>` with the real test name from procedure 03.

### Details
- The INV-04 pending bullets (AAL-030 and AAL-032) are untouched.

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

- The INV-03 row is Blocking with a passing cited test.
- The AAL-031 bullet is gone; INV-04 stays pending.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Row read at line 231 and bullet at 298 as stated; the row is `Yes` citing `test_a_server_starts_when_only_its_own_config_file_is_present`, the AAL-031 bullet removed, checklist lines 341-342 now name only INV-04. AAL-030 and AAL-032 untouched. |
| 2 | Run the documentation checkers named in Validation plan | Completed | 2026-11-23 | 2026-11-23 | `check_adr_structure.py` and `check_adr_invariant_matrix.py` clean; the cited node passes in `.github/run_cited_adr_tests.py`. Length finding: the required sections and the three Execution Status tables alone exceed the 60-line lightweight target, so only the bodies are kept minimal. |

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
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
