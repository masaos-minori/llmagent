## Goal

Update `tools/TOOL_DESCRIPTIONS.md` for the merge: no mention of the retired tool, the kept tool listed among the `--dry-run` writers with its multi-path form, and the hard-coded writer count replaced by a count-free reference (Plan REQ-005: drop the retired tool, update the kept tool, remove the count).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: three edits in `tools/TOOL_DESCRIPTIONS.md` — the `--dry-run` writers paragraph, the atomic-write sentence that counts "the seven above", and the two tool rows.
- Out of scope: removing the tool files (seq 03 document); workflow documents (seq 05/06 documents).

## Assumptions

- Current anchors (verified 20261118 at revalidation): the dry-run writers paragraph names `fix_procedure_new_markers.py` and omits `mark_procedure_new_symbols.py`; the atomic-write sentence ends "and the seven above", already stale against the current eight-entry writer list; the retired-tool row still names a `--files` option its parser does not have.
- `tools/TOOL_DESCRIPTIONS.md` is targeted by 7 Frozen Plans of this batch (cross-plan overlap report); this Plan's edits are the retired-tool row, the two paragraphs, and the kept-tool row, and the plans are processed sequentially, so row-level conflicts cannot occur at generation time.
- The sibling Plan `plans/20261117-124614_wftool002_status-vocabulary-unify.md` (archived, completed) already applied its convention-paragraph edits; this Plan's writer-list wording follows them (Plan Scope dependency, satisfied).

## Design decisions

- The count sentence becomes a pointer to the writers named in the `--dry-run` paragraph, with no number, so it cannot go stale again when the list changes (Plan Decision 4).

## Alternatives considered

- Re-count the writers ("the eight above"): rejected — the count broke once already and would break again with every sibling Plan (Plan Risk mitigation).

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
1. Dry-run writers paragraph: remove `fix_procedure_new_markers.py,` and insert `mark_procedure_new_symbols.py` (`mark` writes; a dry run also leaves the target document unwritten),`.
2. Atomic-write sentence: replace the trailing ", and the seven above." with ", and the writers named in the `--dry-run` paragraph above."
3. Delete the `fix_procedure_new_markers.py` row from the tool table.
4. Update the `mark_procedure_new_symbols.py` row to the merged, multi-path form (see Details).

### Method
Row-level and sentence-level edits only; the section headings and table structure are unchanged.

### Details
Kept-tool row, After:

    | `mark_procedure_new_symbols.py` | Work item | `list` reports, per procedure document, the symbol names `stale_detector.py` reports as missing with the lines of their unmarked backticked occurrences; `mark` inserts the `(new)` marker for the names the operator supplies (or `--all` reports), refuses any name `stale_detector.py` does not report as missing for that document, validates every path before any write, and accepts one or more procedure documents |

## Compatibility considerations

- Run this document after the seq 03 deletion so the end-of-batch `tools/check_tool_descriptions_sync.py` run sees tool files and rows consistent (seq 03 document's Compatibility note).
- The kept-tool row must match the tool's actual multi-path parser after the seq 01 change lands.

## Security considerations

- N/A: documentation file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` → no finding (AC-6).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` → size gate passes.
- `rg -n "fix_procedure_new_markers|the seven above" tools/TOOL_DESCRIPTIONS.md` → no match (AC-4, AC-6).

## Completion criteria

- The description has no retired-tool mention, lists the kept tool among the dry-run writers, describes its multi-path form, and contains no "the seven above" count (AC-6); the sync checker and size gate pass.

## Out of Scope

- Deleting the tool files (seq 03 document).
- Workflow documents (seq 05/06 documents).
- Other rows of `tools/TOOL_DESCRIPTIONS.md` owned by sibling Plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs-only row; validation is the description checkers |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row is the documentation change |

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
- **Requirement ID**: `REQ-005` (description drops the retired tool and the hard-coded count)
- **Source issue**: issues/20261117-123332_wftool003_new-marker-tools-merge.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124834_wftool003_new-marker-tools-merge.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-041553
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
