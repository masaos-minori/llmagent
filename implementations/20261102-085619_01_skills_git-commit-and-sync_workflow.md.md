## Goal
- Document the pathspec-commit split in the git-commit workflow and reconcile Phase 2, Phase 3, and Step 5b so the skill no longer contradicts itself (`REQ-001`: split procedure and rename-pair rule; `REQ-002`: Phase 6 treatment of the remaining staged group, trailer, and group-matching type).

## Scope
- In scope: `skills/git-commit-and-sync/workflow.md` Phase 2, Phase 3, Step 5b, Phase 6, plus one new subsection for the split. Phase 1, Phase 4 (gate run), and Phases 7 to 9 are unchanged.
- Gate (`REQ-004`, `AC-7`): this row's text MUST NOT be written until Plan step 1 (the scratch-repository hook check) has recorded that the remaining staged group stayed intact after a hook run. That step is an unmapped gate step carried out by the implementer; this document only states the precondition.

## Assumptions
- Step 3a verification (current text of the file, 462 lines): Phase 2 lines 44-48 say archival renames staged by `manage_workitem_stage.py ... --stage-only` MUST NOT be unstaged and belong in that cycle's commit; Phase 3 lines 80-84 stop and ask when an extra staged file is an archival rename or of unclear origin; Step 5b (lines 148-153) allows "split into separate commits" without saying how; Phase 6 lines 200-204 describe the pre-commit stash and the status comparison with Phase 1. The `plan` commit type lives in Step 5a (Phase 5, line 141), not in Phase 4; the Plan's Background was corrected on that point in Step 3a.
- Pathspec behavior (Plan Background, verified in scratch repositories during planning): `git commit -m <msg> -- <paths>` commits only the named paths, leaves other staged paths staged, records the working-tree content of a named path (an unstaged edit of an `MM` path is committed silently), and a rename must be named by both paths or the old name's deletion stays staged.
- Decision A2 (Plan): the split stays a choice at Step 5b; one commit remains the default for a single concern.
- The text refers to `tools/classify_changes.py` (new, row 03) and to its contract below. Rows run in `seq` order under `code-implementation`, so row 03 exists before this row is executed; if Plan phase order (tool first, then skill text) is followed, the same holds. `tools/` paths are not checked by `check_skills_references.py`, which only resolves `rules/`, `skills/`, and `templates/` references.
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`, judged and recorded): no other Frozen Plan targets this file (Plan A7). Judged compatible; see the Plan's Assumptions A6, A6b, and A7.
- Tool contract (shared by rows 01, 03, 04, 06, 07; row 03 owns the implementation):
  - Command: `uv run python tools/classify_changes.py [--status-file <path>] [--group <name> | --verify-pathspec <path> ...]`.
    Input is `git status --porcelain=v1 -z` bytes: read from `--status-file <path>` (`-` means stdin), otherwise obtained by running that exact git command in the current directory.
  - Groups, first match wins, in this print order: `artifacts` (`issues/`, `plans/`, `implementations/`, including `done/`), `code` (`scripts/`, `config/`, `deploy/`), `tests` (`tests/`), `tools` (`tools/`), `docs` (`docs/`, `skills/`, `rules/`, `templates/`, `prompts/`, `routing.md`, `AGENTS.md`, `CLAUDE.md`), `other`.
  - Default output, one block per non-empty group: `[<group>]`, then `pathspec: <shell-quoted staged paths, rename pairs adjacent as new name then old name>`, then optional `unstaged: <paths with a working-tree-only change>` and `untracked: <paths>` lines (neither is part of the pathspec). A `warnings:` section follows when needed, with `WARN partly-staged: <path>`, `WARN unmerged: <path>`, and `NOTE cross-group-rename: <old> -> <new> (grouped under <new>)`.
  - Exit codes: 0 normal; 1 when any `partly-staged` or `unmerged` warning exists (or, with `--verify-pathspec`, when a candidate pathspec names only one name of a staged rename); 2 for a usage error or a failed git call.
  - `--group <name>` prints only that group's pathspec line value (empty output when the group is empty); `--verify-pathspec` reads the candidate paths and prints `split-rename: <path> needs <partner>` for each half-named pair.

## Design decisions
- Pathspec commits, not unstaging: nothing is unstaged, so Phase 2's "MUST NOT unstage archival renames" stays true and the renames stay staged until their own commit.
- Reconciliation is by narrowing, not by deleting rules: Phase 2 and Phase 3 keep their rules and add the split case; Step 5b says how the acknowledged split is executed; Phase 6 says how to read the status afterward.

## Alternatives considered
- Unstage, commit, re-stage (the manual workaround): rejected, contradicts Phase 2 and the `SKILL.md` Core rules.
- One mixed commit: rejected as the only option, it blurs code and process history; it remains the default for a single concern.

## Implementation
### Target file
`skills/git-commit-and-sync/workflow.md`

### Procedure
1. Phase 2: after the archival-rename paragraph, add a paragraph that when the changed paths span more than one group, the executor runs `uv run python tools/classify_changes.py` (read-only) to see the groups, and that pre-staged archival renames are committed with the `artifacts` group by pathspec, never unstaged.
2. Phase 3: extend the closing stop rule: when Step 5b's split was acknowledged, an extra staged archival rename is the `artifacts` group of that split, not a mismatch. The "completed when" comparison is made against the union of all groups. Add that a path flagged `partly-staged` must be resolved first by explicit path: stage it fully with `git add <path>`, or, if the unstaged part must not be committed, stop and ask the user (this skill does not discard work); a pathspec commit records working-tree content.
3. Step 5b: after "Proceed to 5c with the user's choice", state that a split is executed as in the new subsection and that the default is one commit for a single concern.
4. New subsection `### Split commit by pathspec` at the end of Phase 6 (before Phase 7): the numbered steps below.
5. Phase 6 status check: state that after the first split commit the remaining staged group is expected, and that the comparison with Phase 1 uses the groups still to be committed (the paths already committed leave the status; the rest stay staged).
6. Record in the new subsection one sentence stating the pre-commit result taken from the Plan step 1 record (hook run on a pathspec commit left the remaining staged group intact, scratch repository, date).

### Method
New subsection steps (write them as the skill's own numbered list):
1. Run `uv run python tools/classify_changes.py`; exit 1 means a `partly-staged` or `unmerged` path: resolve it by explicit path or stop and ask, then re-run.
2. For each group in print order, commit with `git commit -m "<type>[(<scope>)]: <summary>" -m "<body>" -m "<trailer>" -- <the group's pathspec line>`; the pathspec always names both the new and the old name of every rename (the tool prints them adjacent). Optionally check a hand-built pathspec with `--verify-pathspec`.
3. The type matches the group: `plan` for `artifacts` (Step 5a), `feat`/`fix`/`refactor` for `code`, `test` for `tests`, `chore` or `feat` for `tools`, `docs` for `docs`; the session's attribution trailer is the last `-m` of every commit (Step 5c), omitted only when the session has none.
4. After each commit run `git status --short` and `git rev-parse HEAD`; record every SHA for Phase 7 and Phase 9. Hook failure recovery is Phase 6's, per group; each repeat counts toward the Attempt Limit.
5. When the last group is committed, `git status --short` shows only unstaged and untracked work from other sessions, if any.
Wording note: where this text lists forbidden commands it refers to `SKILL.md` Core rules instead of repeating them.

### Details
- Keep each reconciled paragraph short; the file is a procedure, so use MUST/MUST NOT in the file's existing style.
- Do not mention `--no-verify`; `rules/coding.md` already forbids it and Phase 6 refers to it.
- `untracked:` paths from the tool are not committed by pathspec (git rejects an unknown pathspec); they need an explicit `git add` first, which moves them into a group on the next tool run.

## Compatibility considerations
- Behavior change only on the opt-in split path; the default flow (one commit) and every command in it stay as they are. Phase 4's gate run is unchanged and runs once on the whole staged set before the first commit.

## Security considerations
- No forbidden command is introduced (`reset`, `restore .`, `restore --staged .`, `commit --amend` stay forbidden). The pathspec commit never uses `-a` or `--no-verify`. A partly staged path is a data-leak vector for unreviewed edits, which is why the text requires resolving it first.

## Rollback considerations
- N/A: revert the commit; no data or runtime behavior is involved.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.
- `uv run python tools/run_validation_gates.py` over the diff: no `Fail`.
- Read-through: Phase 2, Phase 3, Step 5b, Phase 6 no longer contradict one another (`AC-1`, `AC-2`).

## Completion criteria
- The split procedure, the both-names rename rule, and the reconciled Phase 2, Phase 3, Step 5b, and Phase 6 text are present; each split commit requires the trailer and a group-matching type; the pre-commit result sentence is present and traceable to the Plan step 1 record.

## Out of Scope
- Any change to Phase 1, Phase 4, or Phases 7 to 9; changing how `manage_workitem_stage.py` stages renames; automatic type selection beyond grouping; `SKILL.md` (row 02); docs under `docs/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the Plan step 1 (scratch-repository hook check) result is recorded and intact; stop and report if not (`REQ-004`) | Pending | — | — | precondition, not a file change |
| 2 | Edit `skills/git-commit-and-sync/workflow.md`: Phase 2, Phase 3, Step 5b, Phase 6, and the new split subsection (Implementation > Procedure 1-6) | Pending | — | — |  |
| 3 | Run `check_skills_references.py`, `check_skills_heading_cycles.py`, and `run_validation_gates.py` | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001`, `REQ-002` (gate: `REQ-004`); acceptance `AC-1`, `AC-2`, `AC-7`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: skills/git-commit-and-sync/workflow.md
