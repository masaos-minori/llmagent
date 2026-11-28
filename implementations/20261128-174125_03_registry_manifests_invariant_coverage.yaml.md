## Goal
- Regenerate `registry/manifests/invariant_coverage.yaml` from the updated index matrix (`REQ-004`).

## Scope
**Release unit**: matrix-registration

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 16 unchanged, 0 changed).
- Sequencing (Step 2): the TTL-precedence evidence needs the tests added by the admin TTL-precedence procedures (adrr001), and the publication evidence needs the tests added by the publication-boundary procedures (adrr002). Both Plans are archived, so `plan_dependency_order.py` reports this Plan ready, but their procedures are not yet executed and MUST be implemented first. Cite only test node ids that exist at implementation time; read the actual names from the merged test files.
- Overlap judgment (Step 2): the ADR-013 body is also edited by adrr001 (Decision Detail 12) and adrr002 (the `auth.py` implementation-reference line); the edits are in different sections, a sequencing dependency.
- The manifest is built by `_invariant_coverage_entries` in `tools/generate_reference_table.py` from the index matrix rows; it is never hand-edited.

## Design decisions
- Run the generator once after procedure 02 and review that only ADR-013 entries were added.

## Alternatives considered
N/A: generated output.

## Implementation
### Target file
`registry/manifests/invariant_coverage.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py`.
2. Review `git diff registry/manifests/invariant_coverage.yaml`: expect new `adr: ADR-013` entries for INV-01, INV-03, INV-04, INV-05, and INV-06 with the cited nodes and status of procedure 02.

### Method
- Stop and report on unrelated drift; do not hand-edit.

### Details
- A `Partial` row yields `cadence` and related fields; they come from the index cell.

## Compatibility considerations
N/A: generated manifest, drift-checked.

## Security considerations
N/A: no credential content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`; `uv run pytest tests/tools/test_generate_reference_table.py tests/test_run_cited_adr_tests.py -q`; `uv run python tools/run_validation_gates.py`.
- No `scripts/` or `config/` file changes in this Plan, so no deploy step is needed.

## Completion criteria
- The manifest has an ADR-013 entry per registered invariant and `generate_reference_table.py --check` reports no drift (`REQ-004`).

## Out of Scope
- Hand edits; the index and the ADR body (procedures 01 and 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate `registry/manifests/invariant_coverage.yaml` with `tools/generate_reference_table.py` and review the diff | Pending | — | — | |
| 2 | Run `uv run python tools/generate_reference_table.py --check` and the gate run | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (manifest regenerated, not hand-edited)
- **Source issue**: issues/20261125-103309_adrr003_adr013-invariant-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172904_adrr003_adr013-invariant-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-174125
- **Related target files**: `registry/manifests/invariant_coverage.yaml`
