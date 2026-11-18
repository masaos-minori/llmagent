## Goal

Name the kept marker tool in the approved-correction way forward of `skills/code-implementation/workflow.md`, keeping the abort-and-report rule intact (Plan REQ-004: name the tool where `symbol_missing` is handled; `code-implementation` keeps its abort rule).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one clause added to way-forward bullet (a) of "Stale detection result handling".
- Out of scope: the abort rule, the other ways forward, every other section.

## Assumptions

- Way-forward bullet (a) today reads "they approve a correction to the procedure document, then re-invoke this skill" and names no tool (verified 20261118 at revalidation).
- Plan Decision 3: no workflow step starts correcting a procedure on its own; the tool is named only inside the user-approved way forward.

## Design decisions

- One clause only, inside bullet (a), so the abort-and-report bullets above it are untouched (Plan Risk mitigation: the workflow edit must not invite on-the-spot correction).

## Alternatives considered

- N/A: the Plan fixes the edit location (the approved-correction way forward).

## Implementation
### Target file
`skills/code-implementation/workflow.md`
### Procedure
Extend way-forward bullet (a) so an approved marker correction names the tool that applies it.

### Method
Single-clause insertion inside the existing bullet (a); the section's abort rule and rules against self-correction stay word-for-word unchanged.

### Details
Before:

    - Offer the user these ways forward and do none of them without their decision: (a) they
      approve a correction to the procedure document, then re-invoke this skill; (b)

After:

    - Offer the user these ways forward and do none of them without their decision: (a) they
      approve a correction to the procedure document — for a name the procedure creates,
      `uv run python tools/mark_procedure_new_symbols.py mark {proc_path} --all` applies the
      `(new)` markers the detector left unmarked — then re-invoke this skill; (b)

## Compatibility considerations

- `tools/mark_procedure_new_symbols.py` exists and is registered in `tools/TOOL_DESCRIPTIONS.md` today; the seq 07 document keeps that registration current.

## Security considerations

- N/A: documentation sentence.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py` → no finding (AC-5).
- `uv run python tools/check_skills_heading_cycles.py` → no finding (AC-5).
- Read-back check: the section still states "Abort execution immediately" and "MUST NOT correct the procedure and continue" (AC-5: `code-implementation` keeps abort and report).

## Completion criteria

- Both workflow documents name `tools/mark_procedure_new_symbols.py` (with the seq 05 document) and `code-implementation` still states abort and report (AC-5); both checkers pass.

## Out of Scope

- `skills/plan-to-implementation-procedure/workflow.md` (seq 05 document).
- `tools/TOOL_DESCRIPTIONS.md` (seq 07 document).
- Any change to the stale-detector behavior or the abort rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-095815 | 20261118-095815 | Extended way-forward bullet (a) of 'Stale detection result handling' to name `tools/mark_procedure_new_symbols.py mark {proc_path} --all` for approved marker corrections. Abort-and-report bullets (364/367) word-for-word unchanged. |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-095815 | 20261118-095815 | check_skills_references.py: No issues found; check_skills_heading_cycles.py: No issues found. Read-back confirms abort + MUST NOT correct rules intact. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-095815 | 20261118-095815 | This row IS the documentation change. |

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
- **Related target files**: `skills/code-implementation/workflow.md`
