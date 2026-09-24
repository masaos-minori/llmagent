## Goal
Fix `docs/91_security/00_security_01_architecture-and-trust-boundaries.md`'s 2
relative links to `docs/adr/ADR-013-eventbus-authentication-authorization.md`, both
broken because that file is now one directory level deeper than the bare
`adr/ADR-013-...md` references assumed, implementing `REQ-002`.

## Scope
In scope: both occurrences of the relative-path string
`adr/ADR-013-eventbus-authentication-authorization.md` →
`../adr/ADR-013-eventbus-authentication-authorization.md`. Out of scope: any other
content in this file; any other file (see seq 04/05 for the Plan's other 2 REQ-002
rows).

## Assumptions
- `docs/adr/ADR-013-eventbus-authentication-authorization.md` exists and did not
  itself move — confirmed via `ls`.
- `tools/check_docs_structure.py`'s `check_links()` resolves a `/`-containing link via
  plain `(path.parent / target).resolve()`, with no basename-index fallback — confirmed
  via Read — so this is a genuine break, not a tool false-positive.
- This row runs after seq 01 (this file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix, applied identically to both occurrences.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row.

## Implementation
### Target file
`docs/91_security/00_security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Locate both lines containing
   `[ADR-013-eventbus-authentication-authorization](adr/ADR-013-eventbus-authentication-authorization.md)`.
2. Change both link targets to
   `../adr/ADR-013-eventbus-authentication-authorization.md`.

### Method
Two single-line text replacements (identical target string, two separate source
lines); no other line in the file is touched.

### Details
Confirmed via `grep -n "adr/ADR-013-eventbus-authentication-authorization.md"
docs/00_security_01_architecture-and-trust-boundaries.md`: exactly 2 occurrences
(lines 274, 294).

## Compatibility considerations
N/A: a relative-path string fix with no behavioral surface beyond link resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/91_security/00_security_01_architecture-and-trust-boundaries.md`, or `git
revert` the commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports either `broken link` finding for this
file (Plan `AC-3`).

## Completion criteria
Both links resolve to `docs/adr/ADR-013-eventbus-authentication-authorization.md`; no
other content in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix both `adr/ADR-013-...md` links to add the `../` prefix | Completed | 20260924-145518 | 20260924-145518 | Fixed both adr/ADR-013-eventbus-authentication-authorization.md links to ../adr/ADR-013-eventbus-authentication-authorization.md. |
| 2 | N/A: no test to add for a link-string fix | Completed | 20260924-145518 | 20260924-145518 | N/A: no test to add for a link-string fix. |
| 3 | Run `check_docs_structure.py` (see Validation plan) | Completed | 20260924-145518 | 20260924-145518 | check_docs_structure.py re-run across all 5 rows: no broken-link finding remains for any of the 5 changed files (before/after diff confirmed, only a pre-existing unrelated Keywords-section finding shifted position); check_docs_quality.py exit 0 no ERROR; pytest tests/tools/test_check_docs_quality.py: 20 passed unchanged; grep "^area:" confirms governance unchanged on both moved files; scoped pre-commit passes except the known pre-existing adr-invariant-matrix/adr-reference-scoped gap, no unrelated files touched. |
| 4 | N/A: no further documentation update | Completed | 20260924-145518 | 20260924-145518 | N/A: no further documentation update. |

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
- **Requirement ID**: `REQ-002` (fix relative-path references broken by the move)
- **Source issue**: issues/20260923-141119_docsreorg08_move-security-docs-into-new-security-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-143444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-144446
- **Related target files**: docs/91_security/00_security_01_architecture-and-trust-boundaries.md