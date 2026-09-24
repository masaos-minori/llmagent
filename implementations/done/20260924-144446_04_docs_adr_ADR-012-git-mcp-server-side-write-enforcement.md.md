## Goal
Fix `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`'s relative link to the
moved `docs/91_security/00_security_02_high-risk-tool-common-policy.md`, broken
because that file is now one directory level deeper than the bare
`../00_security_02_high-risk-tool-common-policy.md` reference assumed, implementing
`REQ-002`.

## Scope
In scope: the single relative-path string
`../00_security_02_high-risk-tool-common-policy.md` →
`../91_security/00_security_02_high-risk-tool-common-policy.md`. Out of scope: any
other content in this file; any other file (see seq 03/05 for the Plan's other 2
REQ-002 rows).

## Assumptions
- `docs/91_security/00_security_02_high-risk-tool-common-policy.md` exists at this new
  location (moved by this same Plan's seq 02) — confirmed via `ls`.
- `tools/check_docs_structure.py`'s `check_links()` resolves a `/`-containing link via
  plain `(path.parent / target).resolve()`, with no basename-index fallback — confirmed
  via Read.
- This row runs after seq 02 (the file's own `git mv`) has landed.

## Design decisions
None beyond the mechanical path-string fix.

## Alternatives considered
Convert to a bare filename and rely on the basename index instead of a relative path:
rejected — inconsistent with this file's existing relative-link style; out of scope for
this row.

## Implementation
### Target file
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure
1. Locate the line
   `[High-Risk MCP Tool Common Policy](../00_security_02_high-risk-tool-common-policy.md)`.
2. Change the link target to
   `../91_security/00_security_02_high-risk-tool-common-policy.md`.

### Method
Single-line text replacement targeting only the one link target; no other line in the
file is touched.

### Details
Confirmed via `grep -n "00_security_02_high-risk-tool-common-policy\.md"
docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`: exactly one occurrence
(line 239).

## Compatibility considerations
N/A: a single relative-path string fix with no behavioral surface beyond link
resolution.

## Security considerations
N/A: no executable content, no external input.

## Rollback considerations
Revert via `git checkout --
docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`, or `git revert` the
commit containing this change if already committed.

## Validation plan
`uv run python tools/check_docs_structure.py "docs/**/*.md" --schema
schemas/doc_front_matter.json` no longer reports a `broken link` finding for this file
(Plan `AC-3`).

## Completion criteria
The link resolves to
`docs/91_security/00_security_02_high-risk-tool-common-policy.md`; no other content
in this file changed.

## Out of scope
Any other link or content in this file; any other REQ-002 file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `../00_security_02_high-risk-tool-common-policy.md` link to `../91_security/00_security_02_high-risk-tool-common-policy.md` | Completed | 20260924-145518 | 20260924-145518 | Fixed ../00_security_02_high-risk-tool-common-policy.md link to ../91_security/00_security_02_high-risk-tool-common-policy.md. |
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
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md