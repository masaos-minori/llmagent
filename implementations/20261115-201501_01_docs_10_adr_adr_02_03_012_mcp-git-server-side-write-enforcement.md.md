## Goal

Close the `adr_02_03_012` Plan row at HEAD: the row's condensation work was superseded by maintainer commit `bca9ec63f`, which re-recorded the file's size ceiling to 25253. This procedure verifies that state and edits nothing.

## Scope
**Release unit**: N/A: no release unit

- Covers `REQ-003` verification: the document sits at its accepted ceiling (25253 == 25253), protected sections are unchanged, and the gate stays green. No document edit is due.

## Assumptions
- Superseded, verified 2026-11-15: the Plan chose condensation because the Issue forbade a new `SIZE_EXCEPTIONS` entry; maintainer commit `bca9ec63f` ("chore(tools): re-record docs size ceilings for db_07 fix and pre-existing ADR drift", 2026-11-15) instead added the `adr_02_03_012` entry at 25253 with a dated comment naming `a66077b4f`, and touched no ADR content. The maintainer decision replaces the condensation path; do not reopen it.
- A re-accepted ceiling equals the accepted size exactly, so the "further growth fails" contract holds at 25253.

## Design decisions
- Verification-only: confirm the already-recorded state rather than perform the superseded condensation; a maintainer commit is the decision authority for the resolution choice.

## Alternatives considered
- Condensing 677+ B of duplicate prose: rejected — superseded at HEAD by `bca9ec63f`; condensing now would under-size a ceiling that already equals the accepted size and re-litigate a maintainer decision.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`

### Procedure
1. Confirm the file is 25253 B and the checker records 25253 as its ceiling with the dated "Re-accepted 25253 (2026-11-15)" comment naming `a66077b4f`.
2. Confirm `git show bca9ec63f` changed no section of this document (its diff touches only the checker), so Invariants, normative keywords, the Automated Tests table, Implementation References, Known Deviations, and the Approval Record are unchanged in meaning.
3. Run `uv run python tools/check_adr_preservation.py` and confirm no ERROR against `HEAD` for this file.

### Method
- Read/verify only; no edit to the document. Only if step 1 or 2 fails (i.e. HEAD drifted after this Plan was verified) does the original condensation path reopen, and only then with a fresh size measurement.

### Details
- The duplicate prose the Plan identified (Security Consequences and Ongoing Risks bullets restating Invariants) may still exist; removing it is no longer required by this Plan and would be a separate documentation decision.

## Compatibility considerations
- No runtime or interface impact; the docs-size gate for this file is already enforced at its accepted size.

## Security considerations
- N/A: verification-only.

## Rollback considerations
- None: no change is made.

## Validation plan
- `uv run python tools/check_docs_structure.py` — exit 0, no size findings (AC-01).
- `uv run python tools/check_adr_preservation.py` — no ERROR against `HEAD` for this file (AC-04).
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py` — pass (AC-05).

## Completion criteria
- Verified: 25253 B == recorded ceiling with the dated comment; preservation checker clean; no document edit performed.

## Out of Scope
- Any edit to `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`; editing `tools/check_docs_structure.py` (covered by its own procedure document); reopening the maintainer's re-record decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm size 25253 equals the recorded ceiling with the dated `a66077b4f` comment | Pending | — | — | REQ-003; superseded row, verification-only |
| 2 | Confirm `bca9ec63f` touched no section of the document | Pending | — | — | REQ-003 |
| 3 | Run the preservation and docs checkers | Pending | — | — | AC-01, AC-04, AC-05 |

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
- **Requirement ID**: `REQ-003` (adr_02_03_012 at/below its limit; protected sections unchanged — closed via maintainer re-record)
- **Source issue**: `issues/20261111-224650_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-073403_docsize002_re-record-drifted-docs-size-ceilings.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-201501
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
