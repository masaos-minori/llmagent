## Goal

Wire the GV-006 self-reference prohibition check into the CI pipeline as a Warning-level finding (per Plan's Assumptions section). REQ-010.

## Scope

- No CI step changes needed — the self-reference check is added to `check_docs_structure.py` which is already called by the existing CI step
- The existing CI step calls `check_docs_structure.py` with `--schema`, which triggers structural checks including the new self-reference detection

## Assumptions

- The companion implementation procedure for `tools/check_docs_structure.py` has been executed before this step
- The existing CI step (`Run Front Matter schema compliance check`) already invokes `check_docs_structure.py` with `--schema`, so the self-reference check will be automatically included once the tool change lands
- GV-006 should be treated as Warning-level (non-blocking), consistent with how other structural checks operate per the Plan's Assumptions

### Discrepancy note (UNK-01 resolution)

The Plan's Assumptions states "Warning-level finding (per GV-006 gate column)" but the Governance Verification Matrix table shows GV-006's Gate column as "Blocking". This discrepancy was resolved during Phase 1 verification: the Plan's Assumptions takes precedence as it references a more specific downstream requirement. The CI wiring treats GV-006 findings as Warning-level (non-blocking).

Since the existing CI step already has `continue-on-error: true`, GV-006 findings are effectively non-blocking without any additional CI configuration changes. No modification to this file is required beyond confirming the current state is correct.

## Design decisions

- No CI step changes needed — the self-reference check is integrated into `check_docs_structure.py` which is already called by the existing CI step
- The existing `continue-on-error: true` on the schema compliance step makes all findings from that step (including GV-006) non-blocking, consistent with the Plan's Warning-level requirement

### Method

#### Step 1: Confirm no CI changes needed

Current CI step (lines 64-69):
```yaml
      - name: Run Front Matter schema compliance check (report-only)
        continue-on-error: true
        run: |
          set -euo pipefail
          python -m pip install --quiet pyyaml
          python tools/check_docs_structure.py docs/*.md docs/10_adr/*.md --schema schemas/doc_front_matter.json
```

No changes needed because:
1. The step already calls `check_docs_structure.py` with `--schema`, which includes the self-reference check after the tool change
2. `continue-on-error: true` makes findings non-blocking (Warning-level), consistent with the Plan's Assumptions
3. The step name "(report-only)" accurately reflects its non-blocking nature

If the Plan's Assumptions were later revised to require Blocking-level enforcement for GV-006, the following change would be needed:
- Remove `continue-on-error: true` from this step
- Update the step name from "report-only" to "schema compliance check"

## Compatibility considerations

- No behavioral change to the CI pipeline itself
- The self-reference check becomes active only after the companion tool change is applied

## Security considerations

N/A — CI configuration review only; no changes made.

## Rollback considerations

No rollback needed since no changes are made to this file. If the Plan's Assumptions are later revised to require Blocking-level enforcement:
1. Remove `continue-on-error: true` from this step
2. Update the step name accordingly

## Validation plan

- Manual review: confirm the CI step still calls `check_docs_structure.py` with `--schema`
- After the tool change is applied, verify CI passes for documents without self-references
- Verify CI does not block for documents with self-references (due to `continue-on-error: true`)

## Completion criteria

- The CI step continues to call `check_docs_structure.py` with `--schema`
- Self-reference findings from GV-006 are non-blocking (consistent with Warning-level requirement)

## Out of scope

- Modifying the CI step (no changes needed)
- Adding new CI steps
- Changing the gate level for GV-006 (determined by Plan's Assumptions)

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260925-220411_gv006_self_reference_prohibition_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-222948_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-230646
- **Related target files**: .github/workflows/governance-docs-consistency.yml
