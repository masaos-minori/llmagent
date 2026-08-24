# Traceability Template (Canonical)

Use this structure in all applicable workflow output documents. Leave fields that do not apply as `N/A: {short reason}`.

## Traceability

- **Workflow phase**: {phase name, e.g., issue-to-plan}
- **Source issue**: {path to source issue file or N/A}
- **Source requirement**: {path to source requirement file or N/A}
- **Source plan**: {path to source plan file or N/A}
- **Source implementation procedure**: {path to source implementation procedure file or N/A}
- **Generated at**: {timestamp from date +%Y%m%d-%H%M%S}
- **Related target files**: {target files from the current workflow context or N/A}

## Field Value Sources by Workflow

| Workflow | Phase | Source Issue | Source Requirement | Source Plan | Source Impl Procedure | Related Target Files |
|----------|-------|--------------|-------------------|-------------|----------------------|---------------------|
| 01_issue-to-plan | issue-to-plan | {input issue path} | N/A: no standalone requirement document is generated | N/A: this document is the generated plan | N/A | {target files from issue} |
| 02_plan-to-impl-proc | plan-to-implementation-procedure | N/A | N/A: no standalone requirement document is generated | {input plan path} | N/A | {target_file_name} |
| 03_implementation | implementation | N/A | N/A | N/A | {input impl proc path} | {changed files} |

## Notes

- Do not add Traceability sections to source code or existing documentation files where the original workflow prohibits them.
- For 03_implementation, include a one-line traceability summary in the final report instead of a full section.
- Use `N/A: {short reason}` for non-applicable fields (e.g., `N/A: not a document-generation phase`).
- For requirement-level (not workflow-phase-level) traceability — one row per
  Requirement ID rather than one block per document — see
  `templates/requirement-traceability.md`.