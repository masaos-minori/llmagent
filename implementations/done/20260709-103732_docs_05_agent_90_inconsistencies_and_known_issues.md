# Implementation: L-4 — docs/05_agent_90_inconsistencies_and_known_issues.md DISC-05 entry

Source plan: `plans/20260709-102404_plan.md` (L-4, Implementation step 2).

## Goal

Add a cross-reference entry in the agent-layer known-issues doc, since the
code actually affected by the MCP reload bug (`config_reload.py`,
`config_dataclasses.py`, `config_builders.py`, `cmd_config_display.py`) is
agent-layer, not MCP-layer.

## Scope

**Target**: `docs/05_agent_90_inconsistencies_and_known_issues.md`,
"Document Inconsistencies" section, after the existing `DISC-04` entry
(around line 47, after its closing `---`).

Should land together with
`implementations/20260709-103731_docs_04_mcp_90_inconsistencies_and_known_issues.md`
(this entry cross-references `BUG-01` from that doc).

## Assumptions

1. `DISC-04` (lines 40-47) is the latest entry in the "Document
   Inconsistencies" section — verified by reading the file while planning
   L-4; this new entry continues the sequence as `DISC-05`.

## Implementation

### Target file

`docs/05_agent_90_inconsistencies_and_known_issues.md`

### Procedure

#### Step 1: Add the entry after `DISC-04`

Current (lines 40-48):
```markdown
### DISC-04: workflow_mode=required startup blocking scope

- **Type:** Needs confirmation
- **Impact scope:** `05_agent_08_configuration.md` (workflow_mode description)
- **Statement A:** `workflow_mode = "required"` raises `RuntimeError` when `WorkflowLoader` fails during `Orchestrator.__init__()`
- **Statement B:** Unclear whether failure is at agent startup or at first turn — depends on whether `StartupOrchestrator.run()` catches this
- **Current safe interpretation:** Failure occurs during agent boot (Orchestrator construction phase), not at the first turn

---
```

Insert after the `---`:
```markdown

### DISC-05: MCP reload/config docs describe soon-to-be-removed hot-reload and deferred behavior

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_08_configuration.md`, `05_agent_07_cli-and-commands.md` (MCP reload classification wording)
- **Statement A:** These docs currently describe MCP HTTP URL as
  hot-reloadable and `auth_token`/`startup_mode` as deferred.
- **Statement B:** Requirements H-1 through L-2
  (`requires/done/20260708_23_require.md` through
  `requires/done/20260708_40_require.md`) have approved plans to make all
  MCP server definition changes restart-required and remove
  `github_server_url`; see
  [MCP known issues: BUG-01](04_mcp_90_inconsistencies_and_known_issues.md)
  for the implementation-side tracking entry.
- **Current safe interpretation:** Treat the docs as describing the
  pre-change behavior until the linked plans are implemented and these docs
  are updated per their Design sections.

---
```

### Method

- Single block insertion; no existing entry modified.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New entry present | `grep -n "DISC-05" docs/05_agent_90_inconsistencies_and_known_issues.md` | 1 match |
| Cross-reference valid | confirm `04_mcp_90_inconsistencies_and_known_issues.md` contains `BUG-01` (see `implementations/20260709-103731_...md`) | present |
