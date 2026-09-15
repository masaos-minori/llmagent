## Goal
Add an explicit "Completed when" line to Step 2 (Update deploy.sh), Step 3 (Update
config/agent.toml), Step 4 (Update tool routing), and Step 5 (Deploy) in
`skills/mcp-server-add/workflow.md` (REQ-001 through REQ-004).

## Scope
In scope: one "Completed when" line appended to each of Step 2, 3, 4, and 5. Out of
scope: Steps 1, 6, 7, 8, 9 (already adequate); duplicating the `deploy` skill's own
Phase 2 completion logic inside Step 5.

## Assumptions
- Adding 4 short lines will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- `skills/deploy/workflow.md` Phase 2's Gate wording ("**Gate**: `bash
  deploy/deploy.sh` exits 0", confirmed via Reference Files below) is the correct,
  current cross-reference target for REQ-004 — it is a "Gate", not a "Completed when"
  line, so this document's Step 5 line references it by that accurate label.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), Step 1 (line 104) and Step 6 (line 163) model the phrasing pattern for
REQ-001 through REQ-003. REQ-004 explicitly names `deploy/workflow.md` Phase 2's
actual "Gate" wording rather than the Issue's Required Changes text, which implies a
"Completed when" line exists there verbatim — the Plan's own Problem/Design sections
already identified and corrected this discrepancy; this document reproduces that
corrected wording.

## Alternatives considered
- Quoting Step 5's line as "the deploy skill's own Phase 2 'Completed when' is met" —
  rejected: this would misattribute a phrase ("Completed when") to a file
  (`deploy/workflow.md`) that actually uses "Gate" instead, per the Plan's own
  correction.

## Implementation
### Target file
skills/mcp-server-add/workflow.md

### Procedure
1. Locate the end of Step 2 (after the `cp` command example), insert the "Completed
   when" line (REQ-001) before the `---` separator.
2. Locate the end of Step 3 (after "Also add tool definitions..."), insert the
   "Completed when" line (REQ-002) before the `---` separator.
3. Locate the end of Step 4 (after "...add them to `tool_names`..."), insert the
   "Completed when" line (REQ-003) before the `---` separator.
4. Locate the end of Step 5 (after the `bash deploy/deploy.sh` code block), insert
   the "Completed when" line (REQ-004) before the `---` separator.
5. Leave Steps 1, 6, 7, 8, 9 unchanged.

### Method
Use `Edit` with 4 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence/code block of the corresponding Step (unique in the file).

### Details
- Step 2 (after the `cp config/<name>_mcp_server.toml ...` code block): add
  `**Completed when**: \`deploy/deploy.sh\` contains a \`cp\` line for
  \`config/<name>_mcp_server.toml\` and the path matches the file actually created.`
- Step 3 (after "Also add tool definitions to the \`tool_definitions\` array so the
  agent knows about the new tools."): add `**Completed when**:
  \`config/agent.toml\` has both the new \`[mcp_servers.<name>]\` entry and a
  corresponding \`tool_definitions\` array entry for each of the new server's
  tools.`
- Step 4 (after "If the new server's tools do not use a unique prefix, add them to
  \`tool_names\` in \`config/agent.toml\`."): add `**Completed when**: either the new
  server's tools already resolve via the existing static prefix fallback (no change
  needed), or \`tool_names\` in \`config/agent.toml\` explicitly lists them.`
- Step 5 (after the `bash deploy/deploy.sh` code block): add `**Completed when**: the
  \`deploy\` skill's Phase 2 Gate is met (\`bash deploy/deploy.sh\` exits 0) — this
  Step's completion is that Gate's completion, not a separate check.`

Do not alter Steps 1, 6, 7, 8, 9, and do not duplicate `deploy/workflow.md` Phase 2's
own content inside Step 5.

## Compatibility considerations
This file is referenced by 5+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 4 independent lines; revertable via `git checkout --
skills/mcp-server-add/workflow.md` (pre-commit) or a follow-up commit reverting this
file only.

## Validation plan
- `git diff skills/mcp-server-add/workflow.md` — confirm exactly 4 new lines added,
  one per Step 2-5, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Step 2, 3, 4, and 5 each have an explicit "Completed when" line worded per REQ-001
through REQ-004; Step 5's line accurately references `deploy/workflow.md` Phase 2's
actual "Gate" wording, not a nonexistent "Completed when" line there;
`tools/check_skills_references.py` passes (Plan AC-1, AC-2).

## Out of scope
Steps 1, 6, 7, 8, 9 of this same file; `deploy/workflow.md`'s own content (referenced
only); any other file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110002 | 20260915-110002 | 4 insertions, one per Step 2/3/4/5 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110002 | 20260915-110002 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110002 | 20260915-110002 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110002 | 20260915-110002 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-004 (add "Completed when" to Step 2/3/4/5)
- **Source issue**: issues/20260914-115424_skillqa10_mcp-server-add-workflow-step-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090222_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095712
- **Related target files**: skills/mcp-server-add/workflow.md