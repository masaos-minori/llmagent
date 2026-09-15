## Goal
Add an explicit "Completed when" line to each of Phase 3, 6, 7, 8, 10, 11, and 12 in
`skills/python-implementation/workflow.md` (REQ-001 through REQ-007), with Phase 8's
line explicitly gating progression on resolved/justified security findings.

## Scope
In scope: one "Completed when" line appended to each of Phase 3, 6, 7, 8, 10, 11, and
12. Out of scope: Phase 1, 2, 4, 5, 9 (already adequate); a separate Plan
(`skillqa02`, already implemented as `implementations/20260915-094354_04_skills_
python-implementation_workflow.md.md`) already added a cross-reference clause to
Step 5b's "sufficient context" bullet inside Phase 5 — that edit is in a different
Phase (5) from this document's scope (3, 6, 7, 8, 10, 11, 12), confirmed
non-overlapping; any other section of this file.

## Assumptions
- Adding 7 short lines will not push this file (300+ lines) over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.
- The cross-references each new line makes (`rules/coding.md` Bandit priority
  findings / Suppression governance; `rules/toolchain.md` section 5 / section 7 /
  Completion checklist; `skills/mcp-server-add/workflow.md`; `docs/00_index.md`) were
  re-confirmed present during this document's own Step 3a verification, matching the
  Plan's Reference Files citations exactly.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each new line reuses Phase 1/4/5/9's existing "**Completed when**: ..."
phrasing pattern. Phase 8's line additionally mirrors Phase 9's proven failure-triage
gating phrasing ("do not proceed to Phase 9 with an unresolved, unjustified
high/medium finding"), per the Plan's own Design section and the Issue's Constraint.

## Alternatives considered
- Writing Phase 8's completion condition without an explicit gate (e.g. "bandit has
  been run") — rejected: the Plan's AC-2 and the Issue's Reason for change require the
  line to explicitly block progression on an unresolved finding, not merely confirm
  the tool ran.

## Implementation
### Target file
skills/python-implementation/workflow.md

### Procedure
1. Locate the end of each of Phase 3 (after line 112), Phase 6 (after line 211),
   Phase 7 (after line 233), Phase 8 (after line 241), Phase 10 (after line 279),
   Phase 11 (after line 290), and Phase 12 (after line 300) — each immediately before
   that Phase's trailing `---` separator.
2. Insert the corresponding "Completed when" line (REQ-001 through REQ-007) at each
   location.
3. Leave Phase 1, 2, 4, 5, 9, and all other content unchanged.

### Method
Use `Edit` with 7 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence of the corresponding Phase (unique in the file), appending the new
"Completed when" line as a new paragraph after it, before the `---` separator.

### Details
- Phase 3 (after "Run \`lint-imports\` after every change that touches import
  statements."): add `**Completed when**: \`lint-imports\` passes, or any new
  violation is resolved by an explicit, documented contract change in
  \`.importlinter\` rather than a suppressed failure.`
- Phase 6 (after "Run before each MCP server change is considered complete."): add
  `**Completed when**: new module-boundary data is validated at a Pydantic boundary
  where the codebase convention calls for one, and Schemathesis has been run for any
  changed MCP endpoint (or this Phase does not apply, since no boundary/endpoint
  changed).`
- Phase 7 (after "Do not log at \`DEBUG\` without a corresponding \`if
  logger.isEnabledFor(logging.DEBUG)\` guard."): add `**Completed when**: new
  I/O-bound or cross-service code paths use the \`key=value\` log format, or this
  Phase was correctly skipped (no OTel request, no new I/O-bound/cross-service
  path).`
- Phase 8 (after "Priority findings: see \`rules/coding.md\` Bandit priority
  findings."): add `**Completed when**: \`bandit\` has been run and every
  high/medium-severity finding (per \`rules/coding.md\` Bandit priority findings) is
  either resolved or suppressed with an inline justification (per \`rules/coding.md\`
  Suppression governance) — do not proceed to Phase 9 with an unresolved, unjustified
  high/medium finding.`
- Phase 10 (after the \`pytest tests/ --benchmark-compare=baseline
  --benchmark-compare-fail=mean:10%\` code block): add `**Completed when**:
  \`diff-cover\`'s reported coverage meets the threshold in \`rules/toolchain.md\`
  Completion checklist, and a \`pytest-benchmark\` regression check has been run for
  any performance-sensitive change (or this Phase does not apply).`
- Phase 11 (after "...follows \`skills/mcp-server-add/workflow.md\` — do not
  re-derive that checklist here."): add `**Completed when**: the \`rg\` search for
  the old module/symbol name (when renaming/removing) returns no remaining reference,
  and the MCP-server checklist in \`skills/mcp-server-add/workflow.md\` is satisfied
  when a new server was added.`
- Phase 12 (after "When removing a module: remove its entry from the above, delete
  the file, run \`rg\` for dangling imports."): add `**Completed when**:
  \`routing.md\` and the affected doc (per \`docs/00_index.md\`'s task mapping) are
  updated, or the task is confirmed to need no documentation update.`

Do not alter any Phase's existing content, heading, or `---` separator placement,
including Phase 5 (already amended by the separate `skillqa02` Plan).

## Compatibility considerations
This file is referenced by 6+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file). A separate Plan (`skillqa02`) already edited this same file's Phase 5 — this
document's 7 insertions are confined to Phase 3/6/7/8/10/11/12 and do not touch Phase
5, so the two Plans' edits do not conflict when both are applied.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only. Phase 8's new gating line strengthens (does not weaken) the existing
security-validation requirement by making the pass condition explicit.

## Rollback considerations
Single-file edit adding 7 independent lines; revertable via `git checkout --
skills/python-implementation/workflow.md` (pre-commit) or a follow-up commit
reverting this file only. If `skillqa02`'s Phase 5 edit has already landed in the same
file by the time of a revert, verify the revert does not also remove that unrelated
change.

## Validation plan
- `git diff skills/python-implementation/workflow.md` — confirm exactly 7 new lines
  added, one per Phase 3/6/7/8/10/11/12, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new lines reference
  `rules/coding.md`, `rules/toolchain.md`, `skills/mcp-server-add/workflow.md`).

## Completion criteria
Each of Phase 3, 6, 7, 8, 10, 11, and 12 has an explicit "Completed when" line worded
per REQ-001 through REQ-007; Phase 8's line explicitly gates on resolved/justified
findings; Phase 1, 2, 4, 5, 9 are unchanged; `tools/check_skills_references.py` passes
(Plan AC-1, AC-2, AC-3).

## Out of scope
Phase 1, 2, 4, 5 (Phase 5 tracked separately by `skillqa02`), and 9 of this same file;
any other file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-104254 | 20260915-104254 | 7 insertions, one per Phase 3/6/7/8/10/11/12 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-104254 | 20260915-104254 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-104254 | 20260915-104254 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-104254 | 20260915-104254 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-007 (add "Completed when" to Phase 3/6/7/8/10/11/12)
- **Source issue**: issues/20260914-115049_skillqa05_python-implementation-workflow-phase-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095107
- **Related target files**: skills/python-implementation/workflow.md