## Goal

Wire the GV-002 status enum validation into the CI pipeline as a blocking check by removing `continue-on-error: true` from the schema compliance step. REQ-006.

## Scope

- Remove `continue-on-error: true` from the Front Matter schema compliance check step
- Ensure the step runs as a blocking check in CI

## Assumptions

- The companion implementation procedures for `tools/check_docs_structure.py` and `tests/tools/test_check_docs_structure.py` have been executed before this step
- All existing documents have valid `status` values (stable or draft), so making the check blocking will not cause false failures

## Design decisions

- Direct removal of `continue-on-error: true` from the existing schema compliance step
- Keep the step name unchanged ("Run Front Matter schema compliance check (report-only)") — the "(report-only)" qualifier was accurate when it was opt-in but becomes misleading once it's default-on

### Method

#### Step 1: Remove `continue-on-error: true` from CI workflow

Current code (lines 64-68):
```yaml
      - name: Run Front Matter schema compliance check (report-only)
        continue-on-error: true
        run: |
          set -euo pipefail
          python -m pip install --quiet pyyaml
          python tools/check_docs_structure.py docs/*.md docs/10_adr/*.md --schema schemas/doc_front_matter.json
```

Change to:
```yaml
      - name: Run Front Matter schema compliance check
        run: |
          set -euo pipefail
          python -m pip install --quiet pyyaml
          python tools/check_docs_structure.py docs/*.md docs/10_adr/*.md --schema schemas/doc_front_matter.json
```

Changes made:
1. Removed `continue-on-error: true` line — makes the check blocking
2. Updated step name from "report-only" to just "schema compliance check" since it's no longer report-only

## Compatibility considerations

- Making this check blocking may cause CI failures for any existing documents with invalid `status` values — verify all documents are compliant first
- The step already exists in the workflow; only its error tolerance changes

## Security considerations

N/A — CI configuration change only.

## Rollback considerations

If the change causes CI failures due to invalid status values in existing documents:
1. Re-add `continue-on-error: true` to restore the non-blocking behavior
2. Fix invalid documents first, then re-apply the change

## Validation plan

- Push to GitHub and verify CI passes for documents with valid `status` values
- Verify CI fails for documents with invalid `status` values (e.g., add a test document with `status: obsolete`)

## Completion criteria

- `continue-on-error: true` is removed from the schema compliance step
- CI passes for documents with valid `status` values (stable, draft, or absent)
- CI fails for documents with invalid `status` values

## Out of scope

- Adding new CI steps
- Modifying the tool itself (handled by companion implementation procedures)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260925-220411_gv002_valid_document_status_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-222320_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-230040
- **Related target files**: .github/workflows/governance-docs-consistency.yml
