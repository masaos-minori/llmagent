## Goal
Add an explicit "Completed when" pass condition and an "If any check fails" recovery
reference to `skills/deploy/workflow.md` Phase 4 (Verify deployment) (REQ-001,
REQ-002).

## Scope
In scope: Phase 4's content (lines 135-148), specifically appending the 2 new lines
after the existing `/mcp` verification paragraph. Out of scope: any other Phase in
this file (all already adequate per the Plan); Step 3d's own failure-recovery
content, which is referenced, not duplicated.

## Assumptions
- Adding 2 short lines will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- Step 3d (lines 116-132) still exists as the correct failure-recovery target,
  confirmed by re-reading it during this document's own Step 3a verification.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), REQ-002 references Step 3d by name rather than repeating its
`tail -50`/common-causes procedure, per the Plan's own Constraint and Design section
modeling this on Step 3c's existing "proceed to Step 3d" cross-reference style.

## Alternatives considered
- Writing Phase 4's own independent failure-recovery steps — rejected: the Plan's
  Constraint explicitly forbids duplicating Step 3d's content; a reference is
  required instead.

## Implementation
### Target file
skills/deploy/workflow.md

### Procedure
1. Locate the end of Phase 4's content (after "...confirm all MCP servers show
   healthy.", line 147), before the `---` separator (line 149).
2. Insert the "Completed when" line (REQ-001).
3. Insert the "If any check fails" line (REQ-002) immediately after it.
4. Leave the rest of Phase 4 and all other Phases unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair anchored on the paragraph ending
"...confirm all MCP servers show healthy." (unique in the file), appending both new
lines after it.

### Details
After:
`If the agent was restarted, verify basic operation: start the agent REPL per
\`rules/env.md\` (see \`rules/toolchain.md\`, section 'Environment setup'), then in
the REPL run \`/mcp\` and confirm all MCP servers show healthy.`
add:
`**Completed when**: every restarted service's \`/health\` endpoint returns OK, the
log tail shows no new error timestamped after the restart, and (if the agent was
restarted) \`/mcp\` shows every MCP server healthy.
**If any check fails**: return to Phase 3d's failure-recovery procedure for the
affected service rather than repeating ad hoc troubleshooting here.`

Do not alter the Gate statement, the `curl`/`tail` commands, or any other Phase.

## Compatibility considerations
This file is referenced by 15+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected — this is a skill instruction
file describing a deployment procedure, not the deployment scripts themselves
(`deploy/deploy.sh` is unaffected).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to Phase 4; revertable via `git checkout --
skills/deploy/workflow.md` (pre-commit) or a follow-up commit reverting this file
only.

## Validation plan
- `git diff skills/deploy/workflow.md` — confirm only the 2 new lines were added at
  the end of Phase 4, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new line references
  "Phase 3d" — this check does not validate in-file section references, but a manual
  read confirms Step 3d exists at lines 116-132).

## Completion criteria
Phase 4 has an explicit "Completed when" line matching its Gate statement and an
explicit failure path referencing Phase 3d by name, not duplicating its content;
`tools/check_skills_references.py` passes (Plan AC-1, AC-2).

## Out of scope
Any other Phase in `skills/deploy/workflow.md`; Step 3d's own content (referenced
only); any other file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-103734 | 20260915-103734 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-103734 | 20260915-103734 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-103734 | 20260915-103734 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-103734 | 20260915-103734 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001, REQ-002 (Phase 4 completion condition and failure-routing line)
- **Source issue**: issues/20260914-115009_skillqa04_deploy-workflow-phase4-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094944
- **Related target files**: skills/deploy/workflow.md