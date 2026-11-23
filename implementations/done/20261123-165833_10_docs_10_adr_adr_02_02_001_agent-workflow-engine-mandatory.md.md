## Goal

Restore the ADR-001 INV-02 Verification row to Blocking citing the new test and remove its pending bullet.

## Scope
**Release unit**: N/A: not part of a release unit

One ADR file. Run this procedure after the procedures that create the tests it cites (earlier `seq` values 01 to 06); it cites test node ids that must exist and pass.

## Assumptions

- Row at line 185 and pending bullet at line 263 (read in Step 3a). The bullet's parenthetical about supplying a test is removed with it.

## Design decisions

- Cite the tests from procedure 06, set `Blocking` to `Yes`; remove the AAL-001 bullet as a revert.

## Alternatives considered

N/A: single mechanical change.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Edit the INV-02 row.
2. Remove the AAL-001 bullet.
3. Run the checkers.

### Method
- Cite `tests/agent/workflow/test_no_workflow_bypass.py::<Class>::<test>` nodes.

### Details
- State the recorded scope (the tool-execution and LLM-turn chain) in the row's evidence, so the scope is visible to the maintainer.

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

- The INV-02 row is Blocking with passing cited tests.
- The AAL-001 bullet is gone.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Row read at line 185 and bullet at 263 as stated; the row is `Yes` citing `TestNoCallPathOutsideTheEngine` and records the allowlisted scope; the AAL-001 bullet removed with its parenthetical. |
| 2 | Run the documentation checkers named in Validation plan | Completed | 2026-11-23 | 2026-11-23 | `check_adr_structure.py` and `check_adr_invariant_matrix.py` clean; the cited node passes in `.github/run_cited_adr_tests.py`. The ADR row no longer names a plan identifier (`check_known_deviation_sync.py` fails on a plan-local id cited in an ADR); the scope is stated as data. Length finding: the required sections and the three Execution Status tables alone exceed the 60-line lightweight target, so only the bodies are kept minimal. |

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
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
