## Goal
- Add a batch mode to `skills/issue-creator/workflow.md`: a shared pre-investigation pass with session notes (`REQ-001`, `REQ-002`), a two-tier sibling-issue check in Phase 4 (`REQ-003`), and a merge-edit procedure for integrating findings into an existing issue on user request (`REQ-004`), with per-issue evidence rules and Phases 9 and 10 unchanged.

## Scope
- New `## Batch mode` and `## Merge into an existing issue` sections, placed after `## Multi-file processing` (lines 3-11 at time of writing) and before `## Input from review findings`; a rewrite of the `Sibling-issue check` paragraph in Phase 4 (lines 133-152).
- Unchanged: the Multi-file processing paragraph, Phase 9c checklist items, Phase 10 steps, phase numbering.

## Assumptions
- Confirmed 2026-10-24: Phase 4's check lists candidates with `rg -l -F` and date-prefix narrowing but states no read depth; no "merge" or "integrate" text exists in `skills/issue-creator/`; `tools/check_skills_structure.sh` does not exist, so validation uses `check_skills_references.py`, `check_skills_heading_cycles.py`, and `check_workitem_structure.py`.
- Caveat (non-blocking `Needs confirmation`, Plan `REQ-004` and UNK-04): whether integrating into an existing issue is an intended capability is unconfirmed; the procedure applies only when the user asks, and the existing stop-and-report rule for a fully covering sibling stays unchanged.
- Overlap: `plans/20261024-234023_align-scaffold-policy-with-practice.md` edits Step 10.2 and 10.3 of this file; sequencing dependency, compatible. Re-anchor immediately before editing.
- Notes stay in the session context and are not a repository artifact (Plan UNK-01).

## Design decisions
- Entry condition: Phase 2 assigned the source's tasks to two or more issue groups; no numeric threshold (Plan UNK-02).
- The shared pass runs once between Phase 2 and Phase 3 of the first issue; Phases 3 to 10 remain per-issue and sequential.

## Alternatives considered
- A durable notes file or a notes section in each issue was rejected in the Plan Design (new artifact type; duplication against `skills/DESIGN.md`).

## Implementation
### Target file
`skills/issue-creator/workflow.md`

### Procedure
1. Add `## Batch mode`: entry condition; one shared verification pass of the batch's claims against current source once per file or claim group; notes record claim or file, evidence (path and symbol or command), and result (confirmed, refuted, `Needs confirmation`); each later draft cites the notes instead of re-reading a source, re-reading only for a claim the notes do not cover or a file changed since it was read; the notes are not a repository artifact; Phase 9a still runs per issue and each draft's Background cites the notes' evidence; after compaction, re-read the affected claim group once and re-note it.
2. Rewrite Phase 4's `Sibling-issue check` as two tiers: tier 1 lists candidates by filename, title, and summary from the `issues/` listing and `rg -l`; tier 2 reads the full body only of candidates sharing a target file or failure group; in batch mode tier 1 runs once for the union of the batch's target files and is reused per issue. Keep the Dependency format (repository-relative path, direction, order) and the stop-and-report rule.
3. Add `## Merge into an existing issue`: entry only on the user's request; one full read of the existing issue; all edits applied in one batch; one `uv run python tools/check_workitem_structure.py --file <issue>` after the batch; evidence labels of changed sections re-checked; state that the rule for a fully covering sibling (stop and report) is unchanged.

### Method
- Reference `rules/ai-execution.md` (Sequential Target Processing (Base), Tool Usage) and `skills/DESIGN.md` Evidence labels by section name; do not restate them.

### Details
- Keep every `templates/issue.md` section intact in the merge procedure.

## Compatibility considerations
- `issue-to-plan` looks Dependencies up by path or slug; the Phase 4 rewrite keeps that format. Single-issue runs are unaffected (batch mode needs two or more groups).

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `uv run python tools/check_workitem_structure.py --file <issue>` on one issue written in batch mode and on a merge-edited issue reports no findings.
- `git diff` shows the Multi-file processing paragraph, Phase 9c items, and Phase 10 steps unchanged and no phase renumbered.

## Completion criteria
- The two sections and the Phase 4 rewrite exist as specified, preserved sections are unchanged, and both checkers exit 0.

## Out of Scope
- Phase 9a and 10 changes, a new artifact type or tooling for notes, `rules/ai-execution.md`, and Step 10.2 and 10.3 (sibling Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `## Batch mode` with entry condition, shared pass, and notes rules | Completed | 20261025-003508 | 20261025-003514 |  |
| 2 | Rewrite Phase 4's sibling-issue check as two tiers | Completed | — | 20261025-003514 |  |
| 3 | Add `## Merge into an existing issue` | Completed | — | 20261025-003514 |  |
| 4 | Run both skills checkers, the structure checker on sample issues, and review `git diff` | Completed | — | 20261025-003514 |  |

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
- **Requirement ID**: `REQ-001` (batch pre-investigation pass), `REQ-002` (session notes and reuse), `REQ-003` (two-tier sibling check), `REQ-004` (merge-edit procedure)
- **Source issue**: issues/20261024-212502_perf006_amortize-preinvestigation-in-batch-drafting.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233702_amortize-preinvestigation-in-batch-drafting.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235959
- **Related target files**: `skills/issue-creator/workflow.md`