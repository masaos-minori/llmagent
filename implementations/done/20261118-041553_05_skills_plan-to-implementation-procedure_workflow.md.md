## Goal

Name the kept marker tool where this workflow handles a detector mismatch: case (1) of the Step 3 stale-detector handling states how to apply the `(new)` marker with `tools/mark_procedure_new_symbols.py` (Plan REQ-004: name the tool where `symbol_missing` is handled).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one sentence added to case (1) of the Step 3 document-generation stale-detector handling in `skills/plan-to-implementation-procedure/workflow.md`.
- Out of scope: any other section of this or any other workflow document; the tool itself.

## Assumptions

- Case (1) currently tells the author to add `(new)` by hand and names no tool (verified 20261118 at revalidation: the case list "(1) … (2) … (3) …" sits in the Step 3 bullets after the `stale_detector.py` run).
- The tool's `mark --all` marks every name the detector reports missing for the document and refuses names that exist in source, which matches case (1)'s intent exactly.

## Design decisions

- One sentence only (Plan Historical mitigation: the workflow documents have the highest churn of the targets, so edits are one sentence each).

## Alternatives considered

- N/A: the Plan fixes the edit location (Step 3, case (1)).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`
### Procedure
Extend case (1) so the marker application is a named command instead of an unattributed instruction.

### Method
Single-sentence addition inside the existing case (1) bullet; no heading, table, or case-list restructuring.

### Details
Before:

    (1) a name, import, or target file this document creates — add `(new)` after it
    (see `templates/implementation-procedure.md` Notes);

After:

    (1) a name, import, or target file this document creates — add `(new)` after it
    (see `templates/implementation-procedure.md` Notes), in bulk with
    `uv run python tools/mark_procedure_new_symbols.py mark {document_path} --all` for the names
    the detector reports missing in the document;

## Compatibility considerations

- `tools/mark_procedure_new_symbols.py` exists and is registered in `tools/TOOL_DESCRIPTIONS.md` today, so `tools/check_skills_references.py` resolves the added reference; the seq 07 document keeps the registration current.

## Security considerations

- N/A: documentation sentence.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py` → no finding (AC-5).
- `uv run python tools/check_skills_heading_cycles.py` → no finding (AC-5).

## Completion criteria

- The workflow names `tools/mark_procedure_new_symbols.py` in the stale-detector handling (AC-5) and both reference checkers pass.

## Out of Scope

- `skills/code-implementation/workflow.md` (seq 06 document).
- `tools/TOOL_DESCRIPTIONS.md` (seq 07 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-095500 | 20261118-095500 | Named tools/mark_procedure_new_symbols.py in the plan-to-implementation-procedure workflow's stale-detector Step 3 case (1): the name this document creates gets its (new) marker via this tool. One clause added; surrounding bullets untouched. |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-095500 | 20261118-095500 | check_skills_references.py: No issues found; check_skills_heading_cycles.py: No issues found. Read-back confirms the added clause and adjacent bullets intact. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-095500 | 20261118-095500 | This row IS the documentation change. |

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
- **Requirement ID**: `REQ-004` (name the kept tool where the detector's missing-symbol case is handled)
- **Source issue**: issues/20261117-123332_wftool003_new-marker-tools-merge.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124834_wftool003_new-marker-tools-merge.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-041553
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
