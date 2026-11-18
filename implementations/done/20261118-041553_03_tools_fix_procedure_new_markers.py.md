## Goal

Retire the unguarded marker tool: remove `tools/fix_procedure_new_markers.py` and its test, after the seq 01 document has carried its capability into the guarded tool (Plan REQ-003: remove the duplicate tool and its test with no alias or wrapper).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: deleting `tools/fix_procedure_new_markers.py` and its companion test; the zero-caller re-check before deletion.
- Out of scope: `tools/TOOL_DESCRIPTIONS.md` row and list edits (seq 07 document); the kept tool's implementation (seq 01 document).

## Assumptions

- The retired tool's four test cases are migrated in the seq 01 document before this deletion (Plan Phase 3 order).
- Plan UNK-01: no operator script outside the repository calls the tool by path; the capability is preserved in the kept tool either way.
- Open references today are only the tool itself, its test, and `tools/TOOL_DESCRIPTIONS.md` (re-verified 20261118 with `rg -n fix_procedure_new_markers --glob '!**/done/**'`).

## Design decisions

- Delete both files in the same change as the `rg`-clean check so no unguarded marker path survives between commits (Plan Decision 1: the guarded tool stays, the unguarded one goes).

## Alternatives considered

- Keep the file as a deprecated shim: rejected — the Plan makes an alias or wrapper Out-of-Scope, and the file is the exact call path that could mark an existing symbol as new.

## Implementation
### Target file
`tools/fix_procedure_new_markers.py`
### Procedure
1. Re-run `rg -n fix_procedure_new_markers --glob '!**/done/**'`; stop if any caller outside `tools/fix_procedure_new_markers.py`, `tests/tools/test_fix_procedure_new_markers.py`, and `tools/TOOL_DESCRIPTIONS.md` appears (Plan Phase 1).
2. Confirm the migrated cases pass in `tests/tools/test_mark_procedure_new_symbols.py` (seq 01 document) before deleting (Plan Phase 3).
3. Delete `tools/fix_procedure_new_markers.py`.
4. Delete the companion test file.

### Method
- Plain file deletion; nothing imports either module (Plan Design — Dependency graphing, re-verified at revalidation).

### Details
- Do not add a history note, alias, or wrapper (REQ-003).
- The `tools/TOOL_DESCRIPTIONS.md` mentions (dry-run writer list line and the tool row) are removed by the seq 07 document; between this document and seq 07, `tools/check_tool_descriptions_sync.py` reports the stale row. The plan-batch rule of `skills/code-implementation/workflow.md` runs the full suite and the sync checker once at end of batch, after seq 07 lands.

### Companion test files
- `tests/tools/test_fix_procedure_new_markers.py`
  - Procedure: delete the module after its cases pass in migrated form in `tests/tools/test_mark_procedure_new_symbols.py` (seq 01 document).
  - Validation: `rg -n fix_procedure_new_markers --glob '!**/done/**'` prints nothing outside `issues/done/`, `plans/done/`, and `implementations/done/`; `uv run pytest tests/tools` stays green without the deleted module (AC-4).

## Compatibility considerations

- The tool is run by hand only; no importer exists outside its test (Plan Affected areas: blast radius Low).
- Archived plans and procedures may mention the tool and stay unchanged (Plan Assumptions).

## Security considerations

- N/A: deletion of a file with no new behavior.

## Rollback considerations

- N/A: revert the commit; both files return from history.

## Validation plan

- `rg -n fix_procedure_new_markers --glob '!**/done/**'` → no reference outside the `done/` archives (AC-4).
- `uv run pytest tests/tools` → green without the deleted test module.
- `ls tools/fix_procedure_new_markers.py tests/tools/test_fix_procedure_new_markers.py` → both absent (AC-4).

## Completion criteria

- Both files are absent; `rg` finds no naming of the retired tool outside `issues/done/`, `plans/done/`, and `implementations/done/`; the kept tool's tests (seq 01) pass with the migrated cases (AC-3, AC-4).

## Out of Scope

- `tools/TOOL_DESCRIPTIONS.md` edits (seq 07 document).
- The kept tool's multi-path implementation (seq 01 document).
- Archived plans and procedures that mention the retired tool.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-095430 | 20261118-095430 | git rm of tools/fix_procedure_new_markers.py and tests/tools/test_fix_procedure_new_markers.py; zero external callers confirmed (rg clean beyond tool/test/TOOL_DESCRIPTIONS.md). No alias/wrapper/history note. |
| 2 | Add or update tests per Validation plan | N/A | — | — | Deletion only; migrated cases live in tests/tools/test_mark_procedure_new_symbols.py (seq 01). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-095430 | 20261118-095430 | pytest tests/tools: 2145 passed, 2 skipped (deleted module gone). ls confirms both files absent. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | TOOL_DESCRIPTIONS.md row/list handled by seq 07. |

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
- **Requirement ID**: `REQ-003` (remove the unguarded tool and its test)
- **Source issue**: issues/20261117-123332_wftool003_new-marker-tools-merge.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124834_wftool003_new-marker-tools-merge.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-041553
- **Related target files**: `tools/fix_procedure_new_markers.py`, `tests/tools/test_fix_procedure_new_markers.py`
