## Goal

Close the `tools/check_module_size_tools_baseline.txt` Plan row at HEAD: the `check_docs_structure.py` baseline row already matches the checker's current byte size (32352). This procedure verifies that state and edits nothing.

## Scope
**Release unit**: N/A: no release unit

- Covers `REQ-004` verification: the baseline row for `check_docs_structure.py` equals the checker's exact byte size, so `check_module_size.py` exits 0.

## Assumptions
- Verified 2026-11-15: `tools/check_docs_structure.py` is 32352 B and the baseline row reads `check_docs_structure.py 32352`, so the conditional bump the Plan described is already satisfied by the re-record commit `bca9ec63f` (the earlier 30619 figure is stale).
- If a later edit grows the checker past its baseline before this procedure executes, the row's original conditional bump applies.

## Design decisions
- Verification-only with a conditional remediation (bump only on drift); the baseline contract is "exact current size", so any bump must equal the measured byte count exactly.

## Alternatives considered
- Splitting `tools/check_docs_structure.py` to stay under a size limit: out of scope per the Plan; the baseline-row bump is the accepted mechanism.

## Implementation
### Target file
- `tools/check_module_size_tools_baseline.txt`

### Procedure
1. Measure `tools/check_docs_structure.py` in bytes and compare with its row in the baseline file.
2. If equal (expected: 32352 == 32352), no edit. If the checker is larger, bump only that row to the measured size exactly; if smaller, report the drift without editing (shrinking below baseline is handled by the baseline tool's own reporting).

### Method
- Read/verify; edit at most one line (the `check_docs_structure.py` row) and only under the drift condition in step 2.

### Details
- Do not touch any other baseline row.

## Compatibility considerations
- `check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` gates CI for the tools directory; keeping this row exact keeps the gate meaningful.

## Security considerations
- N/A: verification-only.

## Rollback considerations
- Revert the commit (only applies if the conditional bump fires).

## Validation plan
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — exit 0 (AC-06).

## Completion criteria
- Verified: baseline row equals the checker's exact byte size and `check_module_size.py` exits 0; no edit performed unless drift fired.

## Out of Scope
- Editing `tools/check_docs_structure.py` logic (owned by its own procedure document); splitting the checker; touching any other baseline row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure the checker and compare with its baseline row | Completed | 20261116-094917 | 20261116-094917 | REQ-004; superseded row, verification-only Verified: baseline row 8 = 32352 == os.stat size 32352; MAX_SIZE 24576 and 12 entries unchanged. stale_detector: not stale |
| 2 | Run `check_module_size.py` against the tools baseline | Completed | 20261116-094917 | 20261116-094917 | AC-06 Verified: check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt exit 0 (15 baselined modules) |

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
- **Requirement ID**: `REQ-004` (tools baseline row equals the checker's new byte size)
- **Source issue**: `issues/20261111-224650_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-073403_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-201501
- **Related target files**: `tools/check_module_size_tools_baseline.txt`