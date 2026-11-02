## Goal
- Make `code-implementation` point at the existing row and archive tools and call the new batch command for the Plan update, replacing the manual Plan-update text in Step 7 (`REQ-001`: reference `tools/set_execution_status.py` and `tools/close_procedure.sh`; `REQ-006`: Step 7 calls `tools/close_procedures_batch.py`).

## Scope
- In scope: two new rows in the Toolchain table, and the "Plan Execution Status update (after the move)" subsection of Step 7 plus the pointer in the `close-batch` prohibition bullet that refers to it.
- Out of scope: Step 1, Step 2, Step 4, Multi-file processing, scope rules (edited by sibling Plans).

## Assumptions
- Plan A3, A4, A5, A9 apply. Step 3a verified (2026-11-02): the Toolchain table lists only `close-implementation` and `set-step-status` among the work-item tools; a search of `skills/`, `routing.md`, `rules/`, `AGENTS.md`, and `prompts/` finds no reference to either tool by name; Step 7 forbids `close-batch` and describes the Plan update as manual `set-step-status plan` calls (the mapping rule: map by step number, mark `Completed` only when every file the step modifies has its procedure archived).
- Overlap (Step 2, `check_plan_target_overlaps.py`, Plan A5 and A9): this file is also targeted by the Plans filed from flowimp002 (a batch-mode subsection and a one-sentence pointer at the start of Step 7), flowimp003 (a Step 1 bullet and a Toolchain row), flowimp007 (Step 2 stale-detection text), flowimp009 (Step 2, Step 3d, and the Step 7 mapping for companion files), and flowimp011 (a stop rule in the scope rules). Judged compatible except sequencing: flowimp009 edits the same Step 7 mapping paragraph this row replaces, and flowimp003 adds a Toolchain row next to these rows; whichever lands later rebases adjacent text. This procedure keeps the mapping rule as the command's documented behavior, so flowimp009's companion wording can be merged into the same paragraph.
- The command exists when this row executes (row 01 procedure, earlier `seq`).

## Design decisions
- Keep the mapping rule in the skill text as documentation of what the command verifies, but make the command the default path; the manual `set-step-status` call remains as the fallback when the tool is unavailable or refuses.
- The skill text states that rows are never completed implicitly: `--complete-rows` needs `--note`, and `close_procedure.sh` completes every row, so it is for a procedure whose steps all landed.

## Alternatives considered
- Deleting the manual Plan-update text: rejected, it is the fallback and the mapping rule's statement.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
- Toolchain table: add a row for `tools/set_execution_status.py` (Step 3-6 or 7: marks selected rows of one procedure `Completed`, never invents notes) and a row for `tools/close_procedure.sh` (Step 7: marks every row `Completed` for a date and archives; use only when every step of the procedure was carried out), and a row for `tools/close_procedures_batch.py` (Step 7: verified batch archive and Plan update).
- Step 7 "Plan Execution Status update (after the move)": state that for a batch the command `uv run python tools/close_procedures_batch.py {procedure paths...} --plan {plan_path} --plan-steps N,M` archives with renames staged, updates `Work Items Created`, and marks the named steps `Completed` only when every file the step cites has an archived procedure; list candidate steps with no `--plan-steps`; keep the existing mapping rule as the command's documented behavior and the manual `set-step-status plan` call as the fallback.
- In the `close-batch` prohibition bullet, replace "update the Plan as described under Plan Execution Status update below" with a pointer to the command.

### Method
- Edit only the rows and paragraphs named above; keep the `Source plan` is `N/A` and Plan-not-found Note handling text unchanged.
- Use backticked repository paths only for files that exist or are created by this Plan (`tools/close_procedures_batch.py` is a row of this Plan).

### Details
- The caller names the steps (Plan A4): a check-only verification step can cite the same files, so the skill text says the executor decides which steps modify files and passes only those to `--plan-steps`.

## Compatibility considerations
- N/A: skill text; the existing commands stay valid and referenced.

## Security considerations
- N/A: skill text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no findings.
- Read-through: the Toolchain table names the three tools with their roles; Step 7 calls the command and keeps the mapping rule.

## Completion criteria
- The Toolchain table references `tools/set_execution_status.py` and `tools/close_procedure.sh` (stating that `close_procedure.sh` completes every row) and the new command; Step 7 calls the command in place of the manual Plan update; both checkers pass.

## Out of Scope
- Changing `close-batch`, `set_execution_status.py`, or `close_procedure.sh`; any other section of this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Toolchain rows and rewrite the Step 7 Plan-update subsection per Implementation > Procedure | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` (`routing.md` Tools "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (reference the two existing tools), `REQ-006` (Step 7 calls the command)
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080631_flowimp008_workitem-bulk-close.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085613
- **Related target files**: skills/code-implementation/workflow.md
