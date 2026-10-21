## Goal

Document the pre-approval dry-run execution boundary and the per-tool no-op contract in
the approval subsystem Known Limitations (REQ-004).

## Scope

- Add a Known Limitations subsection to `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
  describing: (a) the preview executes the tool before the approval decision, (b)
  whitelist membership requires a guaranteed no-op `dry_run=True`, and (c) the current
  dormant state (GitHub tools are not in `approval_dry_run_tools` by default).

## Assumptions

- The Known Limitations subsection fits under the existing "Dry Run Preview" area and
  the existing "Known Limitations" section (currently one bullet about the dormant
  GitHub path).
- This doc is not currently listed in `docs/00_index.md`'s inventory (line 40 lists
  only `agent_06_01`); registering it is out of scope unless the implementation
  naturally adds it.

## Design decisions
- Extend the existing "Known Limitations" bullet (L123-125) with the pre-approval
  execution-boundary and no-op-contract statements rather than creating a separate
  top-level section, matching the doc's existing heading convention.

## Alternatives considered
- A new top-level section: rejected; the boundary belongs next to the "Dry Run Preview"
  discussion and the doc's existing Known Limitations slot.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

### Procedure
1. Read the "Dry Run Preview" section (L94-97) and "Known Limitations" section (L123-125).
2. Extend the "Known Limitations" section with bullets documenting:
   - The preview is built by executing the tool with `dry_run=True` **before** the user
     approves (`check_approval` builds the preview at L172, prompts at L186 in
     `scripts/agent/tool_approval.py`).
   - Whitelist membership (`_KNOWN_DRY_RUN_CAPABLE_TOOLS`) requires the tool's server to
     honor `dry_run=True` as a hard no-op (no write/delete/network/database side
     effect); a tool that cannot guarantee this degrades to a text-only preview.
   - The current dormant state: GitHub tools are not in `approval_dry_run_tools` by
     default, so this path does not execute them today.

### Method
- Locate the sections with `grep -n "Dry Run Preview\|Known Limitations" docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`.
- Confirm the execution-path doc `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
  does not already cover the pre-approval dry-run boundary before duplicating it.
- Match the existing Known Limitations bullet style (single dash per statement).

### Details
- Current "Dry Run Preview" (L94-97): tools in `approval_dry_run_tools` run with
  `dry_run=True` before the prompt; `is_error=True` rejects HIGH-risk tools.
- Current "Known Limitations" (L123-125): single bullet — "Since GitHub tools are not
  included in `approval_dry_run_tools` by default, this path is currently dormant."

## Compatibility considerations
N/A: documentation-only change; no code, interface, or config impact.

## Security considerations
The statement must be precise: it documents that the pre-preview execution relies on
each whitelisted tool honoring `dry_run=True` as a no-op. It must not overstate coverage
(as if every tool is guaranteed no-op) — the no-op contract is per-tool and audited per
REQ-001.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Documentation consistency | repo doc-consistency checker for the target doc | Checker passes; no new findings |

## Completion criteria
- The Known Limitations section states the pre-approval dry-run execution boundary and
  the per-tool no-op contract (REQ-004).
- The doc-consistency checker passes with no new findings.

## Out of Scope
- Changing which tools require approval or their risk classification.
- Changing the interactive approval UX / prompt flow.
- Masking of preview args.
- Registering this doc in `docs/00_index.md` unless the implementation naturally adds it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Known Limitations bullets (REQ-004) | Pending | — | — | |
| 2 | Run the documentation consistency checker | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261021-161803_dryrun_preapproval_tool_execution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261021-201654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-204811
- **Related target files**: docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md
