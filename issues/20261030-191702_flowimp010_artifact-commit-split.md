# Commit workflow artifacts separately from code without unstaging renames

## Priority
Medium

## Summary
Give `git-commit-and-sync` a documented way to split one working tree into a code commit and a workflow-artifact commit (issues, plans, implementation procedures, including their archival renames) that keeps the staged renames in place, and add a small read-only tool that classifies the changed paths into those groups and pairs the old and new names of every rename.

## Background
- `Operationally observed` (2026-10-30): after a batch, the index held 22 archival renames and additions staged by `--stage-only`, mixed with the code and test changes. The staged diff matched two commit types, so the skill's mixed-concerns step (Step 5b) applied. Splitting required unstaging 29 paths (old and new names of each rename) with `git restore --staged`, committing the code, and staging the artifacts again.
- `Explicit in code`: `skills/git-commit-and-sync/workflow.md` Phase 2 says archival renames staged by `manage_workitem_stage.py ... --stage-only` MUST NOT be unstaged and belong in the commit of their cycle; Phase 3 says that when an extra staged file is an archival rename, stop and ask; Step 5b offers "split into separate commits" as a choice. The split option and the no-unstage rule do not fit together, and the skill gives no way to split without unstaging.
- `Operationally observed` (run in a scratch repository, 2026-10-30): with a staged modification and a staged rename in the index, `git commit -m "<msg>" -- <code path>` committed only that path and left the rename staged; `git commit -m "<msg>" -- <old name> <new name>` then committed the rename. No unstaging was needed, and the rename pair must be named by both paths.
- `Explicit in code`: `skills/git-commit-and-sync/workflow.md` Phase 5 Step 5a defines a `plan` commit type for artifact-only commits, so the target split already has a message type.

## Problem
The skill prescribes keeping archival renames staged and also allows splitting commits, but a split by the usual means contradicts the first rule, and the rename-pair detail (both names) is easy to get wrong by hand. A mixed commit is the easy path, and it blurs the history of code and process changes.

## Reason for Change
Every batch of the `issue-to-plan` pipeline leaves staged renames beside code. The choice is between a mixed commit and a manual workaround that the skill itself forbids; a documented, tool-assisted path removes the conflict.

## Implementation Intent
Use pathspec commits instead of unstaging. The skill's Phase 2 classifies the changed paths into groups (code, tests, tools, docs, workflow artifacts), and Phase 5 plans one commit per group when the groups map to different commit types. A group is committed with `git commit -m ... -- <paths>`, with both names of every rename in the pathspec, so nothing is unstaged and the archival renames stay staged until their commit. A read-only tool prints the groups and the rename pairs as ready-to-use pathspec lists. The default remains one commit when the diff is a single concern; the split applies when Step 5b detects mixed concerns.

## Target Files or Areas
- `skills/git-commit-and-sync/workflow.md` (Phases 2, 3, 5, and 6) and `SKILL.md` (Core rules)
- `tools/classify_changes.py` (new) and `tests/tools/test_classify_changes.py` (new)
- `tools/TOOL_DESCRIPTIONS.md` and `routing.md`

## Required Changes
- Document the pathspec-commit split, including the rename-pair rule, and reconcile Phase 2's no-unstage rule and Phase 3's stop-and-ask rule with it.
- Add the classification tool: input is `git status --porcelain`, output is groups with pathspec lists, rename pairs kept together, and untracked files marked.
- State in Phase 6 how the post-commit status check treats the remaining staged group.
- Keep Phase 4's gate run, which sees the whole working tree, unchanged.

## Constraints
- No forbidden commands (`SKILL.md` Core rules): no `reset`, no `restore .`, no `commit --amend`.
- The tool is read-only and never stages, unstages, or commits.
- Each commit must still carry the session's attribution trailer and a message of the type that matches its group.

## Acceptance Criteria
- On a fixture repository with a staged modification and a staged rename, the documented procedure produces two commits, each containing only its group, and leaves no staged leftovers; the rename is recorded as a rename.
- The tool prints both names of every rename in the same group and refuses to split a pair.
- `skills/git-commit-and-sync/workflow.md` no longer contradicts itself between Phase 2, Phase 3, and Step 5b.
- `check_skills_references.py` and `check_skills_heading_cycles.py` pass, and the tool is registered (`check_tool_descriptions_sync.py`).

## Testing Expectations
- Unit tests of the classifier over fixture status outputs (modification, rename, untracked, deleted), run against temporary git repositories for the end-to-end split.
- `ruff`, `mypy <tool path>`, and `bandit` per "Adding a new tool".

## Documentation Impact
Yes. The skill states the split, the rename-pair rule, and the reconciled stop conditions. Intent and failure behavior only.

## Out of Scope
- Changing how `manage_workitem_stage.py` stages renames.
- Changing the gate runner or the push and sync phases.
- Automatic commit-type selection beyond grouping paths.

## Dependencies
Related, no ordering: `issues/20261030-191530_flowimp008_workitem-bulk-close.md` (it leaves renames staged, which this procedure then commits). No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether the pre-commit stash behavior (it stashes unstaged changes while hooks run) interacts with a pathspec commit that leaves other staged changes in the index; the scratch run covered the plain git behavior only.
- `不明`: whether the split should be the default when mixed concerns are detected or an option the user chooses (Step 5b currently asks).
- Assumption: archival renames can always be committed as a `plan` commit separate from the code they describe.

## AI Implementation Instruction
Edit the skill and add the read-only tool only. Do not run or document any forbidden command. Verify the pre-commit interaction on a scratch repository before documenting the procedure, and stop and report if a hook run loses or alters the staged group.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191702
- **Related target files**: `skills/git-commit-and-sync/workflow.md`, `skills/git-commit-and-sync/SKILL.md`, `tools/classify_changes.py`, `tests/tools/test_classify_changes.py`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`
