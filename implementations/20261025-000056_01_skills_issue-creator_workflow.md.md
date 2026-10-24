## Goal
- Replace the criteria-free "Prefer" in Step 10.2 of `skills/issue-creator/workflow.md` with one explicit policy: the scaffold tool by default, direct writing from the `templates/issue.md` skeleton only under four conditions (`REQ-001`), list the guarantees the direct path must reproduce (`REQ-002`), and widen Step 10.3 to both paths (`REQ-003`).

## Scope
- Step 10.2 (line 319 onward at time of writing: the `Prefer` line, the tool notes, and the manual procedure) and Step 10.3's opening sentence (line 360 onward).
- Unchanged: Step 10.2a, Step 10.4, the Traceability field rules, `tools/generate_workitem.py`.

## Assumptions
- Confirmed 2026-10-24: line 321 is `Prefer uv run python tools/generate_workitem.py --kind issue --id {id} --title {slug}.` and is the only `Prefer` hit in the file; the tool refuses when the exact path exists in `issues/` or `issues/done/` (`tools/generate_workitem.py` `check_collision`); the manual procedure's item 3 checks the exact path, not a `{timestamp}_*` glob.
- Overlap and order: `implementations/20261024-235959_01_skills_issue-creator_workflow.md.md` (Batch mode, merge-edit, Phase 4 of the same file) is executed first by `code-implementation` (Plan Scope fix order); this row edits only Phase 10. Sequencing dependency, compatible. Re-read the file and re-anchor immediately before editing.
- The direct-write path applies verbatim to batch drafting: each issue is written completely before the next, so prior files already exist when the next path is checked.

## Design decisions
- Policy (user decision, Option B): the tool is the default; direct writing is allowed only when all hold — (a) the fenced skeleton of `templates/issue.md` was read this session and the template has not changed since, (b) the exact target path was verified absent from `issues/` and `issues/done/` immediately before the write, (c) the filename passed the name checks (pattern and at most 4 slug words) before the write, (d) Step 10.4 verification runs on the written file and passes. Otherwise, and whenever the tool is unavailable, the tool path or its stated fallback applies.
- The existing manual fallback is folded into the direct-write conditions, not removed.

## Alternatives considered
- Option A (the tool required for every issue) was rejected by the user's decision (Plan Design).

## Implementation
### Target file
`skills/issue-creator/workflow.md`

### Procedure
1. Step 10.2: replace the `Prefer ...` line with the policy above, keeping the tool command as the default path.
2. Step 10.2: state the guarantees the direct path reproduces — exact-path absence check in `issues/` and `issues/done/` (not a glob), verbatim skeleton (every heading of the fenced block, in template order, none dropped), and the name verification — and state that the name verification (the two `rg` checks) and Step 10.2a apply to both paths.
3. Merge the manual procedure's items into the direct-write conditions without dropping the `date +%Y%m%d-%H%M%S` timestamp or the `issues/` existence check.
4. Step 10.3: change "into the scaffold" to cover "the file created by either path"; leave the Traceability bullets untouched.

### Method
- Keep the tool notes (normalized `{slug}`, verbatim skeleton, refusal, `0`-exit verification) under the tool path; reference `rules/ai-execution.md` Repository Tool Usage and `rules/filename-collision.md` by name only.

### Details
- After the edit `rg -n "Prefer" skills/issue-creator/workflow.md` shows no hit in Step 10.2.

## Compatibility considerations
- The written file is identical for callers; the tool path is unchanged. Step 10.4 stays the common mandatory gate.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `rg -n "Prefer" skills/issue-creator/workflow.md` shows no Step 10.2 hit.
- Write one issue by each path under the new text and run `uv run python tools/check_workitem_structure.py --file <issue>` on both.
- `git diff` shows Step 10.2a, Step 10.4, and `tools/` unchanged.

## Completion criteria
- Step 10.2 states the default tool path, conditions (a) to (d), and the reproduced guarantees; Step 10.3 covers both paths; Step 10.2a and Step 10.4 are unchanged; both checkers exit 0.

## Out of Scope
- `tools/generate_workitem.py`, Step 10.2a, Step 10.4, phase numbering, and the batch-mode sections of the sibling Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace Step 10.2's `Prefer` line with the conditional policy and conditions (a) to (d) | Pending | — | — | |
| 2 | Add the reproduced-guarantees list and fold in the manual procedure | Pending | — | — | |
| 3 | Widen Step 10.3 to both paths | Pending | — | — | |
| 4 | Run both skills checkers, the `rg` check, and the structure checker on one issue per path | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (conditional scaffold policy), `REQ-002` (reproduced guarantees), `REQ-003` (Step 10.3 covers both paths)
- **Source issue**: issues/20261024-212657_perf007_align-scaffold-policy-with-practice.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-234023_align-scaffold-policy-with-practice.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-000056
- **Related target files**: `skills/issue-creator/workflow.md`
