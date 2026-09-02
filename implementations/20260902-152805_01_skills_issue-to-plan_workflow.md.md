## Goal
Satisfy `REQ-001`/`REQ-002`/`REQ-003` (itp001): replace `skills/issue-to-plan/workflow.md`
Step 1.5's non-functional filename-glob duplicate-plan check with a content-based check against
Plans' `Source issue` Traceability field.

## Scope
Modify exactly Step 1.5 (current lines 97-119) of `skills/issue-to-plan/workflow.md`. No other
Step in this file is touched.

## Assumptions
- Re-verified 2026-09-02: Step 1.5 still reads exactly as the Plan's evidence describes (lines
  97-119, matching the Plan's cited "line 100-117" range) — the bug is real and unfixed. Every
  sampled Plan filename (`plans/{generation-timestamp}_plan.md`) carries no ID/timestamp trace
  of its source Issue; that link exists only in the Plan's own `## Traceability` `Source issue`
  field.
- The canonical current field format is `- **Source issue**: {path}`, confirmed against
  `templates/plan.md` line 147 and recent Plans (e.g. `plans/done/20260902-*.md`). A small
  number of pre-convention Plans use an older, non-bolded `Source issue: {path}` format and
  will not match this exact pattern — accepted as out of scope (see Plan `Design`).

## Design decisions
Content-based `grep` search over the `Source issue` Traceability field, replacing the two
filename-glob branches with one check (Plan `Design`, corrected 2026-09-02 after this session
found the Plan's original Design section was copy-pasted from an unrelated sibling plan,
itp007). The old three-way filename-shape branch (ID present / timestamp-only / neither) is
collapsed, since that distinction only existed to pick a glob pattern that never matched
anything real.

## Alternatives considered
Keeping the filename-glob branches as a fallback alongside a new content-based check —
rejected: the glob branches have never produced a real match (Plan `Problem`, Repository
Evidence), so keeping them adds dead-code complexity without any benefit; `REQ-003` also
requires removing the filename ID/timestamp-globbing description entirely.

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Replace Step 1.5's two glob-based bullets with one content-based search bullet; keep the
existing "if match found" / "if no match" / "only check plans/ and plans/done/" bullets, since
those describe post-search behavior that remains meaningful under the new check.

### Method
1. Locate current lines 102-112 (the two glob branches):
   ```
   - **If the Issue filename contains an ID** (format: `{timestamp}_{id}_{slug}.md`, e.g.
     `20260828-155804_nc019_git_mcp_command_specific_guards.md`): extract the ID portion
     (`nc019`), then glob `plans/*{issue_id}*plan.md` (case-insensitive match on the ID).
   - **If the Issue filename does NOT contain an ID but has a timestamp prefix** (e.g.
     `20260717-171259_nuitka_onefile_packaging_proposal.md`): extract the timestamp portion
     (`20260717-171259`), then glob both `plans/*{timestamp}*plan.md` and
     `plans/done/*{timestamp}*plan.md` (case-insensitive match on the timestamp). A plan
     may exist in `plans/` (active) or `plans/done/` (archived after implementation).
   - **If the Issue filename does NOT contain an ID or timestamp** (plain descriptive name,
     e.g. `multi-agent-orchestration-design-plan.md`): this case is outside the scope of
     the issue-creator skill. Do not attempt dedup; proceed to Step 2 normally.
   ```
2. Replace with:
   ```
   - **Corrected 2026-09-02**: the ID/timestamp filename-glob check below was previously
     non-functional — Plan filenames use the Plan-*generation* timestamp
     (`plans/{generation-timestamp}_plan.md`), never the source Issue's own ID or timestamp,
     so no real Plan filename was ever matched by a glob on the Issue's filename. Use a
     content-based check instead: for the current Issue's repository-relative path
     (`{issue_path}`), search for an exact `- **Source issue**: {issue_path}` line inside the
     `## Traceability` section of any file in `plans/*.md` or `plans/done/*.md` (e.g.
     `grep -rl -- "- \*\*Source issue\*\*: {issue_path}" plans/*.md plans/done/*.md`).
   ```
3. Keep current lines 113-118 unchanged (the "if a matching plan exists" / "if no matching
   plan exists" / "only check plans/ and plans/done/" bullets) — these describe post-search
   behavior that is unaffected by how the match was found.

### Details
This is a pure text replacement of the search *mechanism*; the post-match behavior (record the
existing plan's path, skip Plan creation, proceed to Step 9/10; or proceed to Step 2 normally)
is unchanged, per Plan Scope In-Scope ("keeping the existing... behavior once a match is
found").

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected. Behaviorally, this *fixes* a previously-always-failing check — a future
run against an Issue with an existing Plan will now correctly detect it, where it previously
never could.

## Security considerations
N/A: no security-relevant content in a workflow-procedure duplicate-detection fix.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — but reverting
restores the confirmed non-functional glob check.

## Validation plan
- Manual verification: re-run the corrected procedure against at least one Issue with a known existing Plan (e.g. `issues/20260901-170327_itp001_step1_5_duplicate_plan_detection_broken.md` against `plans/20260901-214449_plan.md`, its own generated Plan) and one without, and confirm the outcome matches Acceptance Criteria (Plan `Tests`).

## Completion criteria
Step 1.5 no longer describes filename ID/timestamp globbing as its detection mechanism; it
describes the content-based `Source issue` Traceability field search instead, and explicitly
notes it corrects a previously non-functional check.

## Out of scope
Changing how Plans record their `Source issue` field (Plan Scope Out-of-Scope). Adding an ID or
timestamp to Plan filenames (Plan Scope Out-of-Scope). Special-casing the small number of
pre-convention Plans using the older, non-bolded `Source issue: {path}` format (Plan `Design`).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace Step 1.5's glob branches with content-based check per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 102-112 matched exactly (2-line shift from cited 97-119, within tolerance) |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual verification per Validation plan | Completed | 2026-09-02 | 2026-09-02 | Ran `grep -rl -- "- \*\*Source issue\*\*: {issue_path}" plans/*.md plans/done/*.md` for `issues/20260901-170327_itp001_...md`: correctly found `plans/done/20260901-214449_plan.md`; negative control (nonexistent issue path) correctly found nothing |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (content-based duplicate-plan detection)
- **Source issue**: `issues/20260901-170327_itp001_step1_5_duplicate_plan_detection_broken.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-214449_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152805
- **Related target files**: `skills/issue-to-plan/workflow.md`
