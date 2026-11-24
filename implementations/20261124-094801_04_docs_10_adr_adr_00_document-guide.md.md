## Goal
Replace the ADR-008 display name in the ADR document guide so it no longer says four databases (REQ-008 display names).

## Scope
**Release unit**: adr-amendment

- Edits only `docs/10_adr/adr_00_document-guide.md`. The file link and the front matter `related` entry keep the current file name.

## Assumptions
- The new display name matches the amended ADR-008 title: "Separation and Lifecycle Policy for Six SQLite Stores".

## Design decisions
- Display name changes only; the file name stays until the rename follow-up (UNK-04).

## Alternatives considered
N/A: one-line display change.

## Implementation
### Target file
`docs/10_adr/adr_00_document-guide.md`

### Procedure
1. In the Reading Order table (line 37) change `SQLite 4DB Separation` to `Six SQLite Stores: Separation and Lifecycle` (or the amended title's short form), leaving the backticked file name as is.

### Method
- Single Edit on that table cell.

### Details
- Search the file for other "4DB" or "four-database" wording with `rg -n "4DB|four" docs/10_adr/adr_00_document-guide.md` and change only current-specification wording found there.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_docs_structure.py`.

## Completion criteria
- The guide shows no four-database display name for ADR-008 and still links the existing file.

## Out of Scope
- File rename; other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the ADR-008 display name per Implementation | Pending | — | — | |
| 2 | Run the reference and docs-structure checks per Validation plan | Pending | — | — | Release unit adr-amendment |

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
- **Requirement ID**: REQ-008 (ADR-008 display name in the guide)
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-094324_adrdoc001_adr-eventbus-memory-amendment.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-094801
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`
