## Goal

- tools/check_compat_shims.py — register the four facade import patterns (AC-004, REQ-006)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Four import-syntax patterns only: prose mentions of the retired paths are not flagged (Plan Mitigation, row 189).

## Alternatives considered

- Register the retired paths in `tools/compat_exceptions.toml` instead: rejected — exceptions allow references; `COMPAT_PATTERNS` is the retire mechanism (compatrm002 precedent).

## Implementation
### Target file
`tools/check_compat_shims.py`
### Procedure
1. Add four entries to `COMPAT_PATTERNS` (dict opening at line 39), after the last
   existing entry and before the closing brace, following the existing
   `"description": r"regex"` style:
   ```python
   "from db.store import": r"\bfrom db\.store import\b",
   "from eventbus.db import": r"\bfrom eventbus\.db import\b",
   "import eventbus.db": r"\bimport eventbus\.db\b",
   "from eventbus import db": r"\bfrom eventbus import db\b",
   ```
2. Do not touch `tools/compat_exceptions.toml`: with every reference deleted by docs
   01-02 and 04-25, no exception is needed (plan Reference Files).
3. Keep the checker's own file out of its scan corpus as it already is (the pattern
   literals live here).
### Method
REQ-006 / AC-004. The shim checker scans the repository for retired import/feature
patterns. Four new regex literals must retire the facade import paths:
`\bfrom db\.store import\b`, `\bfrom eventbus\.db import\b`, `\bimport eventbus\.db\b`,
and `\bfrom eventbus import db\b`. The last pattern also catches the two
`from eventbus import db as eb_db` module-object uses, and cannot false-positive on
`db_conn` because the underscore continues the word (no `\b` boundary after `db`).
Full checker-configuration consolidation stays with compatrm004; compatrm002 adds the
auth-compat entries to the same dict independently.
### Details
Four dictionary entries; no checker logic changes.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing for the edit itself (the `COMPAT_PATTERNS` dict at line 39 is the
  established mechanism, proven by the compatrm002 precedent).
  - Blocks: sibling documents 01, 02 (the deletions are only regression-guarded once these patterns
  exist; same commit).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `uv run python tools/check_compat_shims.py`
  Expected: clean once docs 01-02 and 04-25 land (run it failing-first: before the
  cutover commit it reports the existing facade imports, proving the patterns match).
- Command: `uv run pytest tests/tools/test_check_compat_shims.py -q`
  Expected: pass without editing the test file — it iterates `COMPAT_PATTERNS`
  generically (compatrm002 precedent).
  `docs/` fails the checker (AC-004).

## Completion criteria

- reintroducing any facade import path in `scripts/`, `tests/`, or (AC-004, REQ-006)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the four facade patterns to `COMPAT_PATTERNS` — Plan Phase 2 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-006 / AC-004
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `tools/check_compat_shims.py`
