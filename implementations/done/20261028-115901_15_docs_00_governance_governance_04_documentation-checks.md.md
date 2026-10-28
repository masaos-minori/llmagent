# Procedure: describe the error severities and the marker in the governance check description

## Goal

Replace the "warns (exit code unchanged)" wording in section 12 with the error behavior and describe the marker (Plan REQ-008).

## Scope

- Modify only `docs/00_governance/governance_04_documentation-checks.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- Rows 1 and 3 have landed.
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

- In `### 12. ADR Invariant Matrix Checks`, change the sentence that says `check_adr_invariant_matrix.py` warns without changing the exit code to: an empty `Implementation` cell, a body/index citation disagreement and a cited node that does not exist are errors that fail the check.
- Describe the source-reference rule as: every `scripts/` file cited in the matrix carries a `# ADR-NNN` comment marker.
- Check the GV-012 row of the check table for a `Warning` severity statement and align it with the new behavior only if it describes these two checkers.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- Keep the existing `**Enforcement:** pre-commit.` line.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain governance` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-162007 | 20261028-162007 | GV-012 Gate changed Warning -> Blocking: both checkers now fail the run and run in pre-commit |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261028-162007 | 20261028-162007 |  |

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
- **Requirement ID**: REQ-008 (governance description)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md