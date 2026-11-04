## Goal

State in the "SIGINT/SIGTERM Interruption During Startup" section of
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` that a
startup interrupted by a shutdown request ends the process with exit status 0 and no
traceback. Implements REQ-005 of the source plan.

## Scope

- Add one sentence to the end of the "SIGINT/SIGTERM Interruption During Startup"
  section (L90-92), after the existing sentence about the health polling loop being
  interrupted.
- Do not edit any other section of this document (the `mcp_auth` bullet and the
  design-intent / severity text are edited by other Plans; verified compatible in Step 3a).

## Assumptions

- The interrupted-startup outcome is produced by `agent.repl.main` returning normally
  (row 01), so this sentence describes the process-level effect of that change.
- No other document lists agent exit statuses (plan Background item 3); this is the only
  place the interrupted-startup outcome belongs.

## Design decisions

- Extend the existing interruption section rather than adding a new one: the outcome is
  the terminal clause of the same scenario already described there.

## Alternatives considered

- Add a separate subsection: rejected — the outcome is a single clause of the
  interruption scenario already covered here; a new section would duplicate it.

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

Append one sentence to the end of the "SIGINT/SIGTERM Interruption During Startup"
section (after L92):

> Because `agent.repl.main` catches `StartupInterrupted` and returns normally, the
> process ends with exit status 0 and no traceback; a requested shutdown during startup
> is reported as a normal stop, not a crash.

### Method

One sentence appended to an existing section; no new headings, tables, or links.

### Details

- Keep the sentence factual and tied to row 01's behavior; do not restate the rollback
  or polling details already present.
- The sentence must not contradict the "Resource Cleanup on Shutdown" section (L76-88),
  which describes cleanup order, not the process exit status.

## Compatibility considerations

- Only the interruption section changes; the `mcp_auth` bullet and severity text edited
  by the disabled-auth and validation-order Plans are untouched (Step 3a overlap
  judgement).

## Security considerations

- N/A: documentation only.

## Rollback considerations

- Revert the commit (`git checkout -- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`).

## Validation plan

- Docs checkers per `routing.md`: `tools/check_docs_quality.py`,
  `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`,
  `tools/check_docs_consistency.py --domain agent` — no findings.
- Reference-table drift: `uv run python tools/generate_reference_table.py --check` — exit 0.

## Completion criteria

- The interruption section states the process exits with status 0 and no traceback
  (AC-5).
- All docs checkers report no findings.

## Out of Scope

- Any other section of this document.
- Adding a global agent exit-status table (none exists; out of scope per plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers + generate_reference_table --check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | One sentence in the interruption section |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-103359_interruptexit001_startup-interrupt-exits-traceback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-201335
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md
