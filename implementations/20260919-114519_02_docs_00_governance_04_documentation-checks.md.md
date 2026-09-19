## Goal
Update `GV-021`'s row in `docs/00_governance_04_documentation-checks.md`'s
Governance Verification Matrix to describe the expanded check coverage and the
guard-detection fix (`REQ-005`).

## Scope
In scope: this one row's description text. Out of scope: changing `GV-021`'s
Warning/Partial classification, or any other row in the matrix.

## Assumptions
- `GV-021`'s row content unchanged since the Plan was written — re-confirmed
  verbatim at `docs/00_governance_04_documentation-checks.md:329`.
- Depends on seq 01's document (`tools/check_docs_content_policy.py`'s actual
  new function names) for accurate description text — read that document's
  Details section for the exact 6 new category names rather than re-deriving
  them here.

## Design decisions
Append to the existing row's description text (it is already a long,
comma/period-delimited running description of `GV-021`'s history) rather than
replacing it — the existing text documents a prior decision (`REQ-001: Option
(b) chosen...`) that must be preserved as a historical record, per this
project's own "do not silently overwrite a recorded decision" convention
(mirrors `rules/coding.md` Documentation notes classification: this is neither
stale nor wrong, so it is retained, not removed).

## Alternatives considered
Splitting `GV-021` into multiple matrix rows (one per check category) was
considered, but rejected — the source issue's Constraints explicitly forbid
adding a second, separately-registered tool/entry; the existing single-row
structure with an expanding description is the established pattern this file
already uses for `GV-021`'s history.

## Implementation
### Target file
docs/00_governance_04_documentation-checks.md

### Procedure
1. Append a new sentence to `GV-021`'s row description (after the existing
   "Exemption narrowly scoped to content between..." sentence, line 329),
   naming the 6 new check categories and the guard-detection fix.

### Method
Direct text edit (`Edit` tool) — a single appended sentence within one existing
table cell; no table structure change.

### Details
- Appended sentence (example wording, to be finalized against seq 01's actual
  function names): "Extended to also detect default-value restatement, plain
  field/type tables, config-file inventory tables, CLI-command enumerations,
  environment-setup sequences, and DDL/schema blocks; the guard-comment
  exemption (previously matching only the literal string `<!-- AUTO-GENERATED
  -->`) now recognizes any line starting with `<!-- AUTO-GENERATED`, applied
  consistently across all guard-aware checks."
- Do not change the row's `Chk`/`Auto`/`PR`/`Warning`/`Partial` classification
  columns — text-only addition to the description cell.

## Compatibility considerations
Single-cell, additive text change to an existing governance matrix row — no
other row or column is affected.

## Security considerations
N/A: no code, credentials, or runtime behavior described or changed.

## Rollback considerations
Trivial: `git checkout -- docs/00_governance_04_documentation-checks.md`
reverts this text-only addition independently of the other 2 rows in this pass.

## Validation plan
- Run `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py` — expect no new findings.
- Manual review: confirm the appended sentence accurately names the 6 categories
  actually implemented in seq 01's document (not a mismatched or stale list).

## Completion criteria
- `GV-021`'s row description names all 6 new check categories and the
  guard-detection fix, while its Warning/Partial classification is unchanged.
- `tools/check_docs_quality.py`/`tools/check_docs_structure.py` report no new
  findings.

## Out of scope
Changing `GV-021`'s blocking status; any other matrix row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on seq 01 for exact category names |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only — manual review + structural checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Scoped to `tools/check_docs_quality.py` + `tools/check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-005 (update GV-021's Governance Verification Matrix row)
- **Source issue**: issues/done/20260918-130159_docschk01_extend-check_docs_content_policy-instead-of-new-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114519
- **Related target files**: docs/00_governance_04_documentation-checks.md
