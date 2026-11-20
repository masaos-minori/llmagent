## Goal

- Make the ADR front matter cross-check run independently of the invariant matrix result, and fix the checker's stale governance citations.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-008 (no early return: a vacuous matrix no longer suppresses `check_frontmatter_vs_model()`), REQ-009 (docstring cites real anchors: governance_04 §12, GV-012, ADR-016 Decision 7, GV-024).

## Assumptions
- Verified current source: `collect_issues()` (lines 243-266 area) early-returns when `refs` is empty, skipping `check_frontmatter_vs_model()`; the module docstring (line 13 area) cites `GV-012 Implementation intent §3`, an anchor that does not exist in governance_04 (verified: zero grep matches).
- The vacuity error itself stays: the matrix must still fail when it yields no source references; only the suppression of the cross-check is removed.

## Design decisions
- Build the issue list as `([] if refs else [vacuity error]) + check_adr_reference(refs) + check_frontmatter_vs_model()` — one composition point, no control-flow branch (Plan Design).
- Citations name only anchors that exist today: governance_04 §12 and GV-012 for the marker check, ADR-016 Decision 7 and GV-024 for the front matter cross-check (the GV-024 Tool-column completion itself belongs to the governance_04 row).

## Alternatives considered
- Splitting the checker into two commands — rejected: the CI job runs one command; the fix is flow, not surface.

## Implementation
### Target file
`tools/check_adr_reference.py`
### Procedure
- Rework `collect_issues()` so the no-refs case appends the vacuity error and still runs both checks (REQ-008).
- Replace the `GV-012 Implementation intent §3` citation in the module docstring with the real anchors listed above (REQ-009).
### Method
- One flow expression change plus a docstring edit; finding codes and Issue shape unchanged.
### Details
- Keep the existing `Issue` construction (`file`, `line_no`, `severity`, message with `[CODE]` prefix) for the vacuity error so output shape stays stable.

### Companion test files
- `tests/tools/test_check_adr_reference.py`
  - Procedure: add an empty-matrix fixture asserting `FRONTMATTER_DIVERGENCE` findings are still produced alongside the vacuity error (REQ-027).
  - Validation: `uv run pytest tests/tools/test_check_adr_reference.py` — the independence fixture passes; existing vacuity tests stay green.

## Compatibility considerations
- Blast radius: the check runs in the CI lint job; the live repo has a non-empty matrix, so live behavior only adds the previously-suppressed cross-check result (already exercised today when refs are non-empty).

## Security considerations
- N/A: read-only checker.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_reference.py` — independence fixture passes (AC-3).
- `uv run python tools/check_adr_reference.py` — live run stays clean.
- `rules/toolchain.md` static checks (ruff, mypy).

## Completion criteria
- With an empty matrix the tool reports the vacuity error and the cross-check findings together; every docstring citation resolves against governance_04 (AC-3).

## Out of Scope
- The governance_04 GV-024 Tool-column registration (its own row) and any core change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the early return so the cross-check always runs (REQ-008) | Completed | 20261120 | 20261120 | — |
| 2 | Fix the module docstring citations (REQ-009) | Completed | 20261120 | 20261120 | — |
| 3 | Add the companion independence fixture (REQ-027) | Completed | 20261120 | 20261120 | — |
| 4 | Run the Validation plan commands | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-008 (cross-check independence), REQ-009 (docstring citations)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/check_adr_reference.py`, `tests/tools/test_check_adr_reference.py`
