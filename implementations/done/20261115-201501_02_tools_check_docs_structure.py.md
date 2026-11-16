## Goal

Close the `tools/check_docs_structure.py` Plan row at HEAD: the `adr_02_04_006` ceiling re-record (30064 -> 30069 with a dated comment) is already present from maintainer commit `bca9ec63f`. This procedure verifies that state and edits nothing.

## Scope
**Release unit**: N/A: no release unit

- Covers `REQ-002` verification: the recorded ceiling equals the accepted size (30069) and the dated comment names commit `23ca93846` (rmcompat005) and the INV-08 verification-row / events-column growth. Also covers `REQ-001` gate confirmation.

## Assumptions
- Verified 2026-11-15: the entry `"adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md": 30069` exists in `SIZE_EXCEPTIONS` with the dated comment "Re-accepted 30069 (2026-11-15), closing gate drift" naming `23ca93846` (rmcompat005) and the INV-08 verification row plus events column list — exactly what AC-02 requires.
- `MAX_SIZE` is still 24576 and no other entry was altered by the re-record (the commit changed only ceiling entries).

## Design decisions
- Verification-only; apply the Plan's Phase 1 edit only if verification shows the entry or its dated comment missing at execution time (HEAD drift), which is not the case today.

## Alternatives considered
- Re-appending the dated comment now: rejected — it already exists; duplicating it would violate the existing comment convention.

## Implementation
### Target file
- `tools/check_docs_structure.py`

### Procedure
1. Confirm the `adr_02_04_006` entry in `SIZE_EXCEPTIONS` is 30069 and its dated comment names `23ca93846` (rmcompat005) with the INV-08 verification-row / events-column growth, matching the "the ceiling equals the accepted size" convention.
2. Confirm `MAX_SIZE` is unchanged and no other `SIZE_EXCEPTIONS` entry is touched relative to the `bca9ec63f` diff.
3. Run `uv run python tools/check_docs_structure.py` and confirm exit 0 with no size findings.

### Method
- Read/verify only. Conditional remediation: only if step 1 or 2 fails at execution time, perform the original Phase 1 change (set 30069, append the dated comment naming `23ca93846` and the grown content) and then re-run step 3.

### Details
- Do not add a new entry for `adr_02_03_012` here — it already exists (25253, owned by row 1's verification).
- Do not touch `MAX_SIZE` or remove an entry.

## Compatibility considerations
- The gate is what every procedure's Validation plan depends on; this verification confirms it is currently green.

## Security considerations
- N/A: verification-only.

## Rollback considerations
- None: no change is made.

## Validation plan
- `uv run python tools/check_docs_structure.py` — exit 0, no size findings (AC-01).

## Completion criteria
- Verified: entry 30069 with the AC-02 dated comment present; gate exits 0; no edit performed.

## Out of Scope
- Editing any `docs/` file; changing `MAX_SIZE`; adding or removing `SIZE_EXCEPTIONS` entries beyond the conditional remediation in Method; editing `tools/check_module_size_tools_baseline.txt` (covered by its own procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the 30069 entry and its dated comment naming `23ca93846` | Completed | 20261116-094917 | 20261116-094917 | REQ-002; superseded row, verification-only Verified: entry adr_02_04_006 = 30069; comment 'Re-accepted 30069 (2026-11-15)' names 23ca93846. stale_detector: not stale |
| 2 | Confirm `MAX_SIZE` and all other entries are untouched | Completed | 20261116-094917 | 20261116-094917 | REQ-002 Verified: MAX_SIZE = 24576 (:39); dict at :83-262 with 12 entries, last change bca9ec63f. Note: plan prose said ':83-211, 35 entries' - prose drift, no action |
| 3 | Run `check_docs_structure.py` and confirm exit 0 | Completed | 20261116-094917 | 20261116-094917 | REQ-001 / AC-01 Verified: uv run python tools/check_docs_structure.py exit 0 (All checks passed); baseline row 32352 == checker size |

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
- **Requirement ID**: `REQ-002` (adr_02_04_006 ceiling re-record with dated comment), `REQ-001` (gate exits 0)
- **Source issue**: `issues/20261111-224650_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-073403_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-201501
- **Related target files**: `tools/check_docs_structure.py`