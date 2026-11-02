## Goal
- Give `git-commit-and-sync` a documented way to split one working tree into a code commit and a workflow-artifact commit (issues, plans, implementation procedures, including their archival renames) that keeps staged renames in place, and add a small read-only tool that classifies changed paths into those groups and keeps the old and new names of every rename together.

## Priority
Medium

## Scope
- **In-Scope**:
  - A documented pathspec-commit split in `skills/git-commit-and-sync/workflow.md` (Phases 2, 3, and 6, and Phase 5's Steps 5a and 5b; Phase 4 is unchanged) and `SKILL.md` (Core rules), including the rename-pair rule and the reconciliation of Phase 2's no-unstage rule and Phase 3's stop-and-ask rule with Step 5b's split option.
  - A new read-only tool, `tools/classify_changes.py`, that reads `git status` porcelain output and prints groups with ready-to-use pathspec lists, rename pairs kept together, untracked files marked, and partly staged paths flagged.
  - Registration in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping.
  - A scratch-repository verification of the pre-commit interaction before the procedure is documented.
- **Out-of-Scope**:
  - Changing how `manage_workitem_stage.py` stages renames, the gate runner, or the push and sync phases.
  - Automatic commit-type selection beyond grouping paths.
  - Any forbidden command (`reset`, `restore .`, `commit --amend`).
- **Dependencies**: Related, no ordering: `plans/20261102-080631_flowimp008_workitem-bulk-close.md` (its tool leaves renames staged, which this procedure then commits). Overlap judgments are in Assumptions A6 and A7.

## Background
- `Operationally observed` (2026-10-30, from the Issue): after a batch, the index held 22 archival renames and additions staged by `--stage-only`, mixed with code and test changes. Splitting required unstaging 29 paths (old and new names of each rename) with `git restore --staged`, committing the code, and staging the artifacts again.
- `Explicit in code` (checked in Step 3): `skills/git-commit-and-sync/workflow.md` Phase 2 says archival renames staged by `manage_workitem_stage.py ... --stage-only` MUST NOT be unstaged and belong in the commit of their cycle; Phase 3 says that an extra staged file that is an archival rename, or of unclear origin, means stop and ask; Step 5b offers "split into separate commits" as a choice. The split option and the no-unstage rule do not fit together, and the skill gives no way to split without unstaging.
- Corrected in Step 3a (2026-11-02, plan-to-implementation-procedure): the `plan` commit type is defined in Step 5a (Classify the staged diff by type) under Phase 5 (Make Commit Message) of `skills/git-commit-and-sync/workflow.md`; Phase 4 (Check Staged) holds no type list, so an earlier correction naming Phase 4 was itself wrong. Step 5b (mixed concerns) is in the same Phase 5. The split target already has a message type.
- `Operationally observed` (Step 2, scratch repositories, 2026-11-02): with a staged modification and a staged rename, `git commit -m "<msg>" -- <code path>` committed only that path and left the rename staged; `git commit -m "<msg>" -- <old name> <new name>` then committed the rename as a rename, with no staged leftovers. Committing only the new name recorded an addition and left the old name's deletion staged, so a rename pair must be named by both paths. A pathspec commit records the working-tree content of the named path: an unstaged edit of a partly staged (`MM`) path was committed silently.
- `Explicit in code` (checked in Step 3): Phase 6 notes that a `pre-commit` run stashes unstaged tracked changes and restores them afterwards. Whether that interacts with a pathspec commit that leaves other staged changes in the index is unverified: a pre-commit hook could not be installed in a scratch repository during planning (the attempt was denied by the environment), so the plain git behavior is the only verified part.
- `Explicit in code` (checked in Step 3): `skills/git-commit-and-sync/SKILL.md` Core rules forbid `reset --hard`, `clean`, `checkout -- .`, `restore .`, `restore --staged .`, history rewriting, and `commit --amend`, and the skill pushes automatically only after commit, sync, and validation succeed.

## Problem
The skill prescribes keeping archival renames staged and also allows splitting commits, but a split by the usual means contradicts the first rule, and the rename-pair detail (both names) is easy to get wrong by hand. A mixed commit is the easy path, and it blurs the history of code and process changes.

## Reason for Change
Every batch of the `issue-to-plan` pipeline leaves staged renames beside code. The choice is between a mixed commit and a manual workaround that the skill itself forbids; a documented, tool-assisted path removes the conflict.

## Implementation Intent
Use pathspec commits instead of unstaging. Phase 2 classifies the changed paths into groups; when the groups map to different commit types and Step 5b's mixed-concern report is acknowledged as a split, one commit per group is made with `git commit -m ... -- <paths>`, with both names of every rename in the pathspec, so nothing is unstaged and the archival renames stay staged until their commit. A read-only tool prints the groups and the rename pairs as pathspec lists. The default remains one commit when the diff is a single concern.

## Requirements
- `REQ-001`: `skills/git-commit-and-sync/workflow.md` and `SKILL.md` MUST document the pathspec-commit split, including the rule that both names of every rename are in the pathspec, and MUST reconcile Phase 2's no-unstage rule, Phase 3's stop-and-ask rule, and Step 5b's split option so the skill no longer contradicts itself; Phase 4's gate run MUST stay unchanged.
- `REQ-002`: `skills/git-commit-and-sync/workflow.md` Phase 6 MUST state how the post-commit status check treats the remaining staged group, and each split commit MUST still carry the session's attribution trailer and a message of the type that matches its group.
- `REQ-003`: `tools/classify_changes.py` MUST be read-only (never stage, unstage, or commit), MUST take `git status` porcelain output, MUST print groups with pathspec lists, MUST keep both names of every rename in the same group and refuse to split a pair, MUST mark untracked files, and MUST flag a path that is both staged and unstaged because a pathspec commit would include the unstaged part.
- `REQ-004`: The pre-commit interaction MUST be verified on a scratch repository before the procedure is documented; if a hook run loses or alters the staged group, the work MUST stop and report instead of documenting the procedure.
- `REQ-005`: The tool MUST be registered in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping so the drift check passes.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/git-commit-and-sync/workflow.md` | Split procedure and reconciled stop rules | Phase 2, Phase 3, and Step 5b contradict each other for a split; Phase 6 does not cover a remaining staged group | REQ-001, REQ-002 / AC-1, AC-2 | Phase 2 "MUST NOT unstage" text; Phase 3 stop-and-ask; Step 5b; Phase 6 stash note (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/git-commit-and-sync/SKILL.md` | Core rules entry for the split | Core rules list forbidden commands and no split path | REQ-001 / AC-1 | "Core rules" section (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/classify_changes.py` | New file: the classifier | New file; nothing groups changed paths or pairs renames (`tools/` exists) | REQ-003 / AC-3, AC-4 | `TOOL_DESCRIPTIONS.md` lists no such tool (checked in Step 3) | `tests/tools/test_classify_changes.py` | Verified |
| `tests/tools/test_classify_changes.py` | New file: unit tests and temporary-repository tests | New file for the new tool (`tests/tools/` exists) | REQ-003, REQ-001 / AC-3, AC-4, AC-5 | one test module per tool in `tests/tools/` (checked in Step 3) | itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the tool | Every `tools/*.py` needs a row | REQ-005 / AC-6 | `check_tool_descriptions_sync.py` hook (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `routing.md` | Row in "When to run which tool" | The classifier has no routing entry | REQ-005 / AC-6 | table "When to run which tool" (checked in Step 3) | `tools/run_validation_gates.py drift` | Verified |
| `tools/run_validation_gates.py` | Gate mapping entry for the new routing row | `drift_report()` fails for a routing checker without a mapping | REQ-005 / AC-6 | `drift_report`, `ROUTING_GATES` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/manage_workitem_stage.py` | Source of `--stage-only` renames the procedure must preserve | REQ-001 |
| `skills/git-commit-and-sync/SKILL.md` | Forbidden-command list the procedure must respect (also a target; read first) | REQ-001 |
| `.pre-commit-config.yaml` | Hooks that run on a pathspec commit, for the interaction check | REQ-004 |
| `rules/coding.md` | `--no-verify` prohibition and staging rules the procedure must follow | REQ-001 |
| `AGENTS.md` | Execution policy on push and destructive commands | REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`): `skills/git-commit-and-sync/workflow.md` and `SKILL.md` document the pathspec-commit split and the rename-pair rule, and Phase 2, Phase 3, and Step 5b no longer contradict each other.
- AC-2 (`REQ-002`): Phase 6 states how the remaining staged group is treated, and the procedure requires the attribution trailer and a group-matching type on each commit.
- AC-3 (`REQ-003`): On a fixture repository with a staged modification and a staged rename, the documented procedure produces two commits, each containing only its group, leaves no staged leftovers, and records the rename as a rename.
- AC-4 (`REQ-003`): The tool prints both names of every rename in the same group and refuses to split a pair; untracked files are marked; a path that is both staged and unstaged is flagged.
- AC-5 (`REQ-003`): Unit tests over fixture status outputs (modification, rename, untracked, deleted, partly staged) pass, and an end-to-end split runs against temporary git repositories.
- AC-6 (`REQ-005`): `check_tool_descriptions_sync.py` and `tools/run_validation_gates.py drift` pass with the tool registered, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-7 (`REQ-004`): The pre-commit interaction result on a scratch repository is recorded in the implementing change before the procedure text is written.

## Tests
- `REQ-003`: unit tests of the classifier over fixture porcelain output (modification, rename, untracked, deleted, partly staged, rename across groups).
- `REQ-001`, `REQ-003`: end-to-end tests in temporary git repositories for the split and the rename pair.
- `REQ-004`: a scratch-repository run with the project's hook framework before documenting.
- `REQ-001`, `REQ-002`: skill checkers for the changed `skills/*.md` files.

## Documentation Impact
- Yes. The skill states the split, the rename-pair rule, and the reconciled stop conditions (REQ-001, REQ-002); `tools/TOOL_DESCRIPTIONS.md` and `routing.md` list the tool. No `docs/*.md` change: workflow rules and tooling.

## Assumptions
- A1: Archival renames can always be committed as a `plan` commit separate from the code they describe (from the Issue). Falsifiable by a rename that crosses groups.
- A2: Decision (Unresolved Question): the split stays a choice at Step 5b (the user acknowledges the mixed-concern report); the default remains one commit for a single concern. Falsifiable by the owner wanting the split to be automatic.
- A3: Decision: the tool's groups are workflow artifacts (`issues/`, `plans/`, `implementations/`, including `done/`), code (`scripts/`, `config/`, `deploy/`), tests (`tests/`), tools (`tools/`), docs (`docs/`, `skills/`, `rules/`, `templates/`, `prompts/`, `routing.md`, `AGENTS.md`, `CLAUDE.md`), and `other` for the remainder. A rename whose two names fall in different groups stays in one pathspec and is reported as a cross-group rename.
- A4: The pathspec commit records the working-tree content of the named paths (verified in Step 2), so the tool flags `MM` paths and the procedure tells the executor to stage or discard the unstaged part first by explicit path.
- A5: The porcelain `-z` form gives both names of a rename unambiguously; the tool parses that form. Falsifiable by a path containing characters the parser mishandles.
- A6: Overlap judgment (Step 8b): `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `tools/run_validation_gates.py` are also targets of the Plans filed from `flowimp001`, `flowimp003`, `flowimp004`, `flowimp005`, and `flowimp011`. Judged compatible: each adds its own row or mapping entry.
- A7: Overlap judgment (Step 8b): no other Frozen Plan targets `skills/git-commit-and-sync/workflow.md` or `SKILL.md`.
- A6b: Overlap judgment (Step 2 of plan-to-implementation-procedure, 2026-11-02): `tools/check_plan_target_overlaps.py` also lists `plans/20261102-080631_flowimp008_workitem-bulk-close.md` for `tools/TOOL_DESCRIPTIONS.md`. Judged compatible: it adds its own row for `tools/close_procedures_batch.py`; no ordering needed.
- A8: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the pre-commit hook run (which stashes unstaged tracked changes) loses or alters the remaining staged group during a pathspec commit | Planning could not install a hook in a scratch repository; only plain git behavior was verified | Phase 1 verifies on a scratch repository (hook installed inside the scratch repository only) before any procedure text is written; if the staged group is lost or altered, stop and report (REQ-004) | False |
| UNK-02 | Whether the owner wants the split to be the default for mixed concerns | Step 5b currently asks | Keep the ask (A2); revisit on owner feedback | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/git-commit-and-sync/workflow.md` | Modify | High (every commit follows it) | 9 | N/A | not applicable (rsynced) |
| `skills/git-commit-and-sync/SKILL.md` | Modify | High | 5 | N/A | not applicable (rsynced) |
| `tools/classify_changes.py` | Create | Low (new, read-only) | 0 | N/A | not applicable (rsynced) |
| `tests/tools/test_classify_changes.py` | Create | Low | 0 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |

## Design
- Procedure: Phase 2 runs the classifier on the porcelain status and shows the groups. When Step 5b's mixed-concern report is acknowledged as a split, each group is committed in turn with `git commit -m ... -- {pathspec}`, naming both names of every rename; the attribution trailer is the last `-m` of each commit; each type matches its group (`plan` for the artifact group). Nothing is unstaged and no forbidden command is used.
- Reconciliation: Phase 2 keeps "MUST NOT unstage archival renames" and adds that they are committed with the artifact group by pathspec; Phase 3's stop-and-ask for an extra staged archival rename becomes "this is the artifact group of a split" when a split was acknowledged; Step 5b states how the split is executed; Phase 6 states that after the first commit the remaining staged group is expected and the status comparison uses the groups still to be committed.
- Partly staged paths: a path that is both staged and unstaged is flagged by the tool; the procedure requires resolving it by explicit path (stage it fully or leave the unstaged part out) before the pathspec commit, because the pathspec commit records working-tree content (A4).
- Tool: input is `git status --porcelain=v1 -z` output (stdin or an internal call to the same command); output is groups with shell-quoted pathspec lists, rename pairs in one group, untracked marked (they need an explicit add and are not committed by pathspec), and warnings. It never stages, unstages, or commits.
- Pre-commit verification (REQ-004): before text is written, a scratch repository with the project's hook framework installed inside that repository only is used to run the split and confirm the remaining staged group is intact after each hook run. The outcome is recorded in the implementing change.
- Registration: the routing row carries placeholder arguments, so the gate mapping is reported `Not available` at run time but keeps its mapping.
- Alternatives rejected: unstaging and re-staging (contradicts Phase 2 and Core rules); one mixed commit (blurs history).

## Implementation steps
1. **Phase 1: Verify the pre-commit interaction (gate)**
   - [ ] On a scratch repository with the project's hook framework installed inside it only, run the pathspec split with a hook active and record whether the remaining staged group stays intact; stop and report if it is lost or altered (`REQ-004`; no repository file is changed in this phase, recorded in the implementing change)
2. **Phase 2: Classifier and tests**
   - [ ] Implement `tools/classify_changes.py` (`REQ-003`; `tools/classify_changes.py`)
   - [ ] Write unit tests over fixture porcelain output and end-to-end tests in temporary git repositories (`REQ-001`, `REQ-003`; `tests/tools/test_classify_changes.py`)
3. **Phase 3: Skill text**
   - [ ] Document the split, the rename-pair rule, and the reconciled Phase 2, Phase 3, Step 5b, and Phase 6 text (`REQ-001`, `REQ-002`; `skills/git-commit-and-sync/workflow.md`)
   - [ ] Add the Core rules entry (`REQ-001`; `skills/git-commit-and-sync/SKILL.md`)
4. **Phase 4: Registration**
   - [ ] Add the tool row, routing row, and gate mapping entry (`REQ-005`; `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py`)
5. **Phase 5: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on the new tool and the checkers in the Validation plan (`REQ-001` to `REQ-005`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/classify_changes.py` | Unit and temporary-repository end-to-end | `uv run pytest tests/tools/test_classify_changes.py -v` | all pass |
| `tools/classify_changes.py`, `tools/run_validation_gates.py` | Lint, type, security | `uv run ruff format <file>`; `uv run ruff check <file>`; `uv run mypy <file>`; `uv run bandit <file>` per file | clean |
| `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Registration and drift | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/run_validation_gates.py drift`; `uv run pytest tests/tools/test_run_validation_gates.py -v` | pass |
| `skills/git-commit-and-sync/workflow.md`, `SKILL.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |
| Scratch repository | Pre-commit interaction (AC-7) | scratch run with a hook active | staged group intact, recorded |

## Risks
- **Risk**: A hook run loses or alters the remaining staged group during a pathspec commit, losing the renames. → **Mitigation**: Phase 1 verifies this on a scratch repository first and stops the work if it fails (REQ-004, UNK-01); the renames are recoverable from the working tree, and no forbidden command is used.
- **Risk**: A pathspec commit silently includes an unstaged edit of a partly staged path. → **Mitigation**: the tool flags `MM` paths and the procedure requires resolving them by explicit path first (A4); verified in Step 2.
- **Risk**: A rename pair is split by hand. → **Mitigation**: the tool keeps both names in one pathspec and refuses to split a pair; committing only one name was shown to leave a staged deletion.
- **Risk**: The skill edits change commit behavior for every session. → **Mitigation**: the default stays one commit for a single concern; the split applies only after Step 5b's acknowledgement.
- **Risk**: Shared registration files are edited by sibling Plans. → **Mitigation**: A6; row-additive edits.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the pre-commit interaction on a scratch repository (gate; no repository file changed) | Pending | — | — |  |
| 2 | Classifier and tests: `tools/classify_changes.py`, `tests/tools/test_classify_changes.py` | In Progress | — | — |  |
| 3 | Skill text: `skills/git-commit-and-sync/workflow.md`, `skills/git-commit-and-sync/SKILL.md` | In Progress | — | — |  |
| 4 | Registration: `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | In Progress | — | — |  |
| 5 | Verification: lint sequence and checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-085619_01_skills_git-commit-and-sync_workflow.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085619_02_skills_git-commit-and-sync_SKILL.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085619_03_tools_classify_changes.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085619_04_tests_tools_test_classify_changes.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085619_05_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261102-085619_06_routing.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261102-085619_07_tools_run_validation_gates.py.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-081312
- **Related target files**: `skills/git-commit-and-sync/workflow.md`, `skills/git-commit-and-sync/SKILL.md`, `tools/classify_changes.py`, `tests/tools/test_classify_changes.py`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (document the split and rename-pair rule; reconcile Phase 2 and Phase 3) | `skills/git-commit-and-sync/workflow.md` | Phase 3 | AC-1 | reference and heading checkers | Confirmed by repository evidence |
| REQ-001 | Target Files (`SKILL.md` Core rules) | `skills/git-commit-and-sync/SKILL.md` | Phase 3 | AC-1 | reference and heading checkers | Explicit in issue |
| REQ-002 | Required Changes (Phase 6 treatment of the remaining staged group); Constraints (trailer, type per group) | `skills/git-commit-and-sync/workflow.md` | Phase 3 | AC-2 | reference and heading checkers | Explicit in issue |
| REQ-003 | Required Changes (classification tool); Step 2 (rename-pair and MM findings) | `tools/classify_changes.py` | Phase 2 | AC-3, AC-4 | classifier unit tests | Confirmed by repository evidence |
| REQ-003 | Testing Expectations (classifier and temporary-repository tests) | `tests/tools/test_classify_changes.py` | Phase 2 | AC-3, AC-4, AC-5 | unit and end-to-end tests | Explicit in issue |
| REQ-004 | AI Implementation Instruction (verify pre-commit interaction first); Unresolved Questions | `skills/git-commit-and-sync/workflow.md` | Phase 1, Phase 3 | AC-7 | scratch-repository run | Needs confirmation |
| REQ-005 | Required Changes (register the tool) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-005 | Target Files (`routing.md`) | `routing.md` | Phase 4 | AC-6 | drift check | Explicit in issue |
| REQ-005 | Step 3 (drift needs a gate mapping for a routing row) | `tools/run_validation_gates.py` | Phase 4 | AC-6 | drift check | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085619 -->