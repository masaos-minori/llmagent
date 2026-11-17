# Execution Status Template (Canonical)

Shared table structure for tracking in-progress work. Used by `templates/plan.md`,
`templates/implementation-procedure.md`, and the Final Report of the implementation
workflow. Each consuming document supplies its own default rows (the concrete steps or
items for that document); the column structure and status/type vocabulary below do not
vary and must not be redefined locally.

```markdown
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | {step-specific — see the consuming document for its default set} | Pending | — | — | |

Status options: Pending / In Progress / Blocked / Completed / Superseded

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

Type options: Test / Code Change / Doc Change / Procedure / Issue
```

## Notes

- Update the Execution Status table's Status column as each step starts and finishes.
- Pre-populate the Execution Status table with the actual steps or items the
  consuming document requires when it is first created — never leave a single
  placeholder row for a document that already knows its concrete steps.
- Resolved column in Blocker Log: use `N/A: {short reason}` when a blocker does not
  apply to a resolution date (e.g. a structural non-issue), rather than leaving it
  blank.
- Gated marker (procedure rows only): a procedure of a gated Plan (a Plan with an open
  dependency, as reported by `tools/plan_dependency_order.py`) carries
  `Gated: {blocking path} phase {N or all} - {reason}` as the start of the Notes cell of
  its pending rows. Status stays `Pending` and no Status value is added: `Blocked` is for a
  row that started and hit a blocker. `plan-to-implementation-procedure` writes the
  marker; only the owner clears it, and `code-implementation` never does. The tool
  recomputes readiness, so a stale marker never overrides it.
- Superseded (procedure rows only): the terminal state of a row of a procedure that will
  not be implemented, because another change made its design obsolete or a duplicate
  covers it. Its Notes start with `Superseded: {reason}`. Use
  `close-implementation --superseded --reason "{why}"` (`tools/manage_workitem_stage.py`):
  it marks every unfinished row and archives the procedure. A procedure with an unfinished
  row enters `implementations/done/` only this way; moving it by hand leaves `Pending`
  rows in the archive, which `tools/check_workitem_structure.py --archived-status`
  reports. `Superseded` is not `Completed`: the work was not done.
- Started/Completed (Execution Status) and Resolution Date (Blocker Log) record actual
  work execution/completion times. Use the same timestamp format as Traceability's
  "Generated at" (`templates/traceability.md`): determine it by running
  `date +%Y%m%d-%H%M%S`.
