## Goal
- Add to the Core Execution Rules of `skills/plan-to-implementation-procedure/SKILL.md` a narrow exception to the one-target-file-per-document rule for test files tied to a single code row (`REQ-001`: define the companion section and its conditions, keep the rule for everything else).

## Scope
- Modify only `skills/plan-to-implementation-procedure/SKILL.md`: the "One target file = one procedure document" rule and the "No duplicate work" rule. Documentation-only; Medium blast radius (every Plan-to-procedure cycle loads it). `workflow.md` (seq 02) and the template (seq 03) carry the detail; this file states the rule and the conditions once.

## Assumptions
- A1: Step 3a: the Core Execution Rules bullet "One target file = one procedure document" says a document "MUST NOT contain modification instructions for more than one file" and carries the `Partially implemented` remainder sentence (verified by Read, 2026-11-02); the "No duplicate work" bullet matches an existing document by `Source plan` and `Related target files` by `target_file_path` (verified by Read). The edit is located by those bullet titles, not line numbers.
- A2: The conditions are fixed by the Plan Design: a companion is a test file (path under `tests/`) that is a row of the same Plan, is named in the `Related Tests` cell of exactly one other row, and needs no design decision of its own. A test file tied to more than one row, or needing its own decisions, keeps a separate document (Plan A1, A4).
- A3: The companion section format is defined by the `seq` 03 procedure (template) and read by the `seq` 05, 07 and 09 tool procedures; this file only names the section (`### Companion test files`).
- A4: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02, Plan A7 to A11): this file is also targeted by flowimp008, flowimp011 and (already procedured) flowimp002, flowimp003, flowimp007. Judged compatible by content, a sequencing dependency by file: edits are anchored by text, not line number; whichever Plan lands later rebases. This file is targeted by this Plan only among the active Plans.
- A5: Step 3a: `skills/plan-to-implementation-procedure/SKILL.md` also states "one per target file" in its Purpose paragraph and "one per row" in the front matter description. Both remain true (each row is still covered by exactly one document, as target or companion) and are left unchanged; flagged here so the executor does not treat them as stale.

## Design decisions
- State the exception inside the existing rule bullet as one sub-list of four conditions, and add one clause to "No duplicate work": a row is also covered when an existing matching document lists its file as a companion.
- Keep the one-file rule for source files, docs, config, and standalone test files in the same bullet, so the exception cannot be read as general.

## Alternatives considered
- A separate rule bullet for companions: rejected; it would let the one-file bullet and the exception drift apart.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/SKILL.md`

### Procedure
1. Locate the bullet starting `**One target file = one procedure document**` by text.
2. Append the exception after its `Partially implemented` sentence: companions defined, the four conditions, and the statement that the rule is unchanged for every other file.
3. Locate the bullet starting `**No duplicate work**` and add the companion-coverage clause.
4. Leave every other section unchanged.

### Method
- Use Edit anchored on the last sentence of each bullet; keep each bullet's existing text.
- Refer to the section by name only (`### Companion test files`, defined in `templates/implementation-procedure.md`) and to the coverage command by name (`tools/check_workitem_traceability.py`), without restating either; this keeps `check_skills_heading_cycles.py` clean.

### Details
- Condition list wording: (1) the test file is a row of this Plan's `Implementation Target Files` table and lies under `tests/`; (2) exactly one other row names it in its `Related Tests` cell; (3) it needs no design decision of its own; (4) the document's `Related target files` lists the target first, then each companion.
- Add: a companion MUST NOT also be the target or a companion of another document; a row covered as a companion gets no document of its own.

## Compatibility considerations
- N/A: additive exception; documents without companions follow the unchanged rule.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`: no findings.
- `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- The Core Execution Rules state the companion exception, its four conditions, and that the rule is unchanged for other files (AC-1); both checkers pass.

## Out of Scope
- `workflow.md` Step 3c and Step 4 text (seq 02), the template (seq 03), the tools, and the Purpose and front matter wording (A5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the one-file rule and the no-duplicate-work rule in `SKILL.md` | Completed | 20261102-133556 | 20261102-133556 | edited SKILL.md (one-file rule, no-duplicate-work); stale check clean; full suite deferred to plan end |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-133556 | 20261102-133556 | check_skills_references and check_skills_heading_cycles: no issues |

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
- **Requirement ID**: REQ-001 (companion exception and conditions in the skill)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `skills/plan-to-implementation-procedure/SKILL.md`
