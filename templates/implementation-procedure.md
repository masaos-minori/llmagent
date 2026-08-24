# Implementation Procedure Output Template (Canonical)

Use this exact Markdown structure when generating
`implementations/{timestamp}_{target_file_slug}.md` in the
`plan-to-implementation-procedure` workflow (see
`skills/plan-to-implementation-procedure/workflow.md` Step 3). Do not omit any section.

Keep each section concise and file-level (a few bullets each) — this is not a broad
architecture document. Use `N/A: {short reason}` for any section that does not apply
to the item.

```markdown
## Goal

## Scope

## Assumptions

## Design decisions

## Alternatives considered

## Implementation
### Target file
### Procedure
### Method
### Details

## Compatibility considerations

## Security considerations

## Rollback considerations

## Validation plan

## Out of scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
```

## Notes on filling sections

- For "Design decisions" / "Alternatives considered" / "Compatibility considerations" /
  "Security considerations" / "Rollback considerations", apply
  `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` for how to
  reason about them — draw only the few relevant bullets from that skill's broader
  12-section template; do not produce its full architecture output here.
- "Execution Status" / "Blocker Log" / "Work Items Created" table structure and
  status/type vocabulary: see `templates/execution-status.md`. The rows above are this
  document's default starting set — pre-populate with the actual steps the item
  requires when the document is first created; split further if Method/Details call
  for multiple distinct sub-steps. Do not leave a single placeholder row.
- "Source issue" must carry forward the value from the target plan's own Traceability
  section — set to N/A only if the Plan's own Traceability section genuinely records
  N/A itself; never default to N/A when the Plan carries a concrete value.
- "Related target files" uses `target_file_path` (the repository-relative path), not
  `target_file_name` (its base name) — this is also what the "already implemented"
  check matches against.
