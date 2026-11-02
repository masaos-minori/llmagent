## Goal
- Rewrite the additional target file discovery bullet of Step 3c to call `tools/amend_plan.py` and follow the approval classes instead of a manual Plan edit (`REQ-005`).

## Scope
- In scope: that one bullet and one Toolchain list line for the tool. Out of scope: all other steps and bullets, and the `code-implementation` stop rule (seq 05).

## Assumptions
- Step 3a verification: Step 3c's bullet beginning `If investigation reveals that implementing this row requires modifying a file not listed` states `Blocked: additional target file discovered` and the manual amendment (row appended after the last row, evidence, Requirement link, re-freeze, resume at the same row); verified by Read of the current file, 2026-11-02. The `Toolchain` section lists the repository tools.
- Overlap (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `skills/plan-to-implementation-procedure/workflow.md` is also a target of `plans/20261102-080631_flowimp008_workitem-bulk-close.md` and `plans/20261102-080828_flowimp009_test-row-grouping.md`, and of the already generated procedures of flowimp002, 003, and 007. Judged compatible (Plan A6): this row edits the additional-target-discovery bullet of Step 3c and one Toolchain line; the others edit different steps. Whichever lands later rebases; locate anchors by text, not by line number.
- `tools/amend_plan.py` and the heading `Plan Amendment Approval Classes (proposed)` in `rules/workflow-lifecycle.md` are created by the seq 01 and seq 03 procedures; stale-detector reports for them are the acceptable earlier-`seq` kind.

## Design decisions
- First class (fallout): amend through the tool, report afterward (file, class, reason), resume this cycle at the same row. Second class (scope or behavior change, new requirement, removed row): stop `Blocked: additional target file discovered — {path}` and ask first. If the owner's policy is not accepted, treat every amendment as the second class.
- Keep the existing prohibition: no further procedure document until the Plan is amended and re-frozen; append-only seq rule stays stated.

## Alternatives considered
N/A: wording fixed by the Plan (`REQ-005`).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Re-read Step 3c at execution time and locate the bullet by its first words.
2. Replace its manual-amendment clause with the tool call (`uv run python tools/amend_plan.py {plan_path} --file {path} ... --class fallout` or `scope`, described by flag names) and the two-class behavior; keep every other sentence.
3. Add the tool as one line in the Toolchain list with Step 3c.

### Method
- Edit anchored on the unique text `the Plan has been amended (the new file added as its own` and its continuation; reference the rules by file and heading only (`rules/workflow-lifecycle.md` Plan Amendment Approval Classes (proposed)); do not restate the class definitions.

### Details
- Keep the resume rule: after re-freeze, resume at the discovering row, not Step 2 and not row 1.

## Compatibility considerations
- Plans without an additional discovery are unaffected. The `Blocked` message for the second class is unchanged.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`: no findings (AC-6).

## Completion criteria
- Step 3c calls the tool and follows both classes with the pending-policy default, the resume rule is intact, and both checkers pass (AC-6).

## Out of Scope
- Other steps, `skills/code-implementation/workflow.md`, the rule text, and edits made by other Plans to this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the additional-discovery bullet in Step 3c and add the Toolchain line | Pending | — | — |  |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — |  |

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
- **Requirement ID**: `REQ-005` (Step 3c calls the tool and follows the classes)
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081027_flowimp011_plan-amend-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085611
- **Related target files**: skills/plan-to-implementation-procedure/workflow.md
