## Goal
Reorder `skills/python-refactoring/validation.md`'s 4-item "At minimum" list to put
`ruff format`/`ruff check --fix` first, matching `workflow.md`'s actual sequence
(REQ-001).

## Scope
In scope: the 4-item "At minimum" list (lines 44-47). Out of scope:
`workflow.md`'s own content (Step 6/8's behavior is unchanged — only `validation.md`'s
description is corrected); any other section of `validation.md`;
`report-template.md` (a separate target-file row in this same Plan).

## Assumptions
- Reordering 4 short bullets will not push this file over the 400-line File Split
  Rule trigger in `skills/DESIGN.md`.
- `workflow.md` Step 6 (line 236, "Run `ruff format` and `ruff check --fix` after
  each transformation") and Step 8 (line 273, "Run tests, `ruff`, and `mypy` once per
  logical group") remain the authoritative actual sequence this reorder matches,
  confirmed via Reference Files below.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), this is a pure list-item reordering — no item's own wording changes,
only sequence, per the Plan's own Design section framing this as
additive/corrective rather than restructuring.

## Alternatives considered
- Rewriting the list items to describe the full workflow.md Step 6/8 sequence in
  detail — rejected: the Plan's REQ-001 specifies only a reorder of the existing 4
  items with one new leading item citing `workflow.md` Step 6, not a rewrite of each
  item's content.

## Implementation
### Target file
skills/python-refactoring/validation.md

### Procedure
1. Locate the "At minimum:" 4-item list (lines 44-47).
2. Replace the list with the same 4 concepts, reordered to put the ruff
   format/check --fix step first (as a new leading item citing `workflow.md` Step 6),
   followed by mypy, pyright, and characterization tests.
3. Leave all other content in this file unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full 4-item list
(unique in the file), replacing it with the reordered version.

### Details
Change:
```
At minimum:
- Run `mypy`.
- Cross-check with `pyright`.
- Run `ruff`.
- Run characterization tests.
```
to:
```
At minimum:
- Run `ruff format`/`ruff check --fix` (per `workflow.md` Step 6, immediately after
  each transformation).
- Run `mypy`.
- Cross-check with `pyright`.
- Run characterization tests.
```

Do not alter any other line in this file.

## Compatibility considerations
This file is referenced by 3+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected — this corrects a description
of an existing, unchanged `workflow.md` behavior.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
reordering only.

## Rollback considerations
Single-file, list-reorder-only edit; revertable independently of the companion
`report-template.md` document via `git checkout -- skills/python-refactoring/
validation.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/python-refactoring/validation.md` — confirm only the 4-item list's
  order changed (with the new ruff cross-reference item), no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new item references
  `workflow.md` Step 6 by name).

## Completion criteria
`validation.md`'s stated tool order matches `workflow.md`'s actual sequence (ruff
format/check --fix first, then mypy, pyright, characterization tests);
`tools/check_skills_references.py` passes (Plan AC-1).

## Out of scope
`workflow.md`'s actual behavior (unchanged); `report-template.md` (a separate
target-file row in this Plan); any other section of `validation.md`; any other file;
any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110158 | 20260915-110158 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110158 | 20260915-110158 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110158 | 20260915-110158 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110158 | 20260915-110158 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 (reorder validation.md's 4-item list to match workflow.md's actual sequence)
- **Source issue**: issues/20260914-115550_skillqa12_python-refactoring-tool-order-and-completion-gate-exit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095918
- **Related target files**: skills/python-refactoring/validation.md