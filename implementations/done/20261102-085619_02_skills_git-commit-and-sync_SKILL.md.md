## Goal
- Add the split entry to the `SKILL.md` Core rules and align its Phase 2 to Phase 6 summary rows (`REQ-001`: document the pathspec-commit split and the rename-pair rule).

## Scope
- In scope: the Core rules list and the Phase overview rows for Phases 2, 3, 5, and 6 of `skills/git-commit-and-sync/SKILL.md`. Out of scope: the detailed procedure (row 01) and the forbidden-command list itself.

## Assumptions
- Step 3a verification: Core rules forbid `reset --hard`, `clean`, `checkout -- .`, `restore .`, `restore --staged .`, history rewriting, and `commit --amend`, and permit only `git restore --staged <explicit path>` for a single unexpected file; the Phase overview table describes Phase 2 as "explicit paths by default" and Phase 6 as `git commit -m`.
- Churn (30d) for this file is 5 per the Plan; the file is loaded by every commit session, so wording stays minimal.
- Row 01's text and this row's entry must agree; row 01 is the detailed source.
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`, judged and recorded): no other Frozen Plan targets this file (Plan A7). Judged compatible; see the Plan's Assumptions A6, A6b, and A7.

## Design decisions
- One new Core rules bullet states the split as a permitted alternative to a mixed commit, with the both-names rule, and points to `workflow.md` for the steps (no duplication of them).
- Corrected in Step 3b (2026-11-02): the pointer is a bare `workflow.md` file reference, not `workflow.md` Phase 6 heading. A heading reference closes the cycle `rules/coding.md` Prohibited behavior -> `SKILL.md` Core rules -> `workflow.md` Phase 6 -> `rules/coding.md`, which `check_skills_heading_cycles.py` rejects.
- The Phase overview rows get a short clause each, not new rows.

## Alternatives considered
N/A: documentation-only row with a single reasonable placement.

## Implementation
### Target file
`skills/git-commit-and-sync/SKILL.md`

### Procedure
1. Add a Core rules bullet after the forbidden-commands bullets: after Step 5b's acknowledgement, a mixed diff may be committed as one commit per group with `git commit ... -- <pathspec>`; every rename names both its old and new path; nothing is unstaged; each commit carries the attribution trailer and a type matching its group; details and the read-only classifier are in `workflow.md`.
2. Phase overview: append to Phase 2 "pre-staged archival renames stay staged and ride with their group", to Phase 3 "partly staged paths resolved by explicit path first", to Phase 5 "5b may end in a split by group", to Phase 6 "split commits use pathspecs; remaining staged group is expected after the first".
3. In the "only permitted unstaging" sentence of the existing rule, leave the text unchanged (the split does not unstage).

### Method
- Edit the Markdown in place; keep the bullet style and the MUST/never wording of the surrounding rules.

### Details
- Do not restate the forbidden list or the command steps; refer to `workflow.md` (see `AGENTS.md` Global Rule 5 for scope discipline).

## Compatibility considerations
N/A: the default flow is unchanged; the split is opt-in.

## Security considerations
N/A: no command beyond those already allowed; no forbidden command is introduced.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings; `uv run python tools/run_validation_gates.py`: no `Fail`.

## Completion criteria
- The Core rules bullet and the four Phase overview clauses are present and consistent with `workflow.md` (`AC-1`).

## Out of Scope
- `workflow.md` edits (row 01); the tool; registration rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `skills/git-commit-and-sync/SKILL.md`: Core rules bullet and Phase overview clauses (Implementation > Procedure 1-3) | Completed | 20261102-141314 | 2026-11-02 | Core rules bullet and 4 Phase overview clauses added; file: skills/git-commit-and-sync/SKILL.md; procedure corrected in 3b (bare workflow.md pointer to avoid heading cycle); full suite deferred to plan end (no code) |
| 2 | Run `check_skills_references.py`, `check_skills_heading_cycles.py`, and `run_validation_gates.py` | Completed | 2026-11-02 | 2026-11-02 | check_skills_references, check_skills_heading_cycles, run_validation_gates fast: pass |

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
- **Requirement ID**: `REQ-001`; acceptance `AC-1`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: skills/git-commit-and-sync/SKILL.md
