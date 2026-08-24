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

Status options: Pending / In Progress / Blocked / Completed

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

Type options: Test / Code Change / Doc Change / Issue
```

## Notes

- Update the Execution Status table's Status column as each step starts and finishes.
- Pre-populate the Execution Status table with the actual steps or items the
  consuming document requires when it is first created — never leave a single
  placeholder row for a document that already knows its concrete steps.
- Resolved column in Blocker Log: use `N/A: {short reason}` when a blocker does not
  apply to a resolution date (e.g. a structural non-issue), rather than leaving it
  blank.
