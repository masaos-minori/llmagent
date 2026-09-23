## Goal

Add missing Front Matter fields (`area`, `tags`, `related`) and H1 heading to `docs/databases/active_databases.md`, then add required `## Keywords` and `## Related Documents` sections per REQ-001, REQ-003, REQ-004.

## Scope

Modify only `docs/databases/active_databases.md` to:
1. Add YAML Front Matter with `title`, `area`, `tags`, `related` fields
2. Add exactly one H1 heading
3. Add `## Keywords` section with placeholder content
4. Add `## Related Documents` section with placeholder content

## Assumptions

- The file exists but lacks any Front Matter entirely (confirmed by `check_docs_structure.py`)
- Directory path `databases/` can be used to infer `area: databases`
- No specific cross-references exist, so `related: []` is appropriate
- File content must not change — only metadata and structural additions

## Design decisions

- Infer `area` value from directory path: `docs/databases/` → `area: databases`
- Use empty array `[]` for `related` since no specific references are known
- Add minimal valid Front Matter matching schema requirements from `schemas/doc_front_matter.json`
- Add both `## Keywords\n<placeholder>` and `## Related Documents\n<placeholder>` as required sections

## Alternatives considered

- Keeping the file without Front Matter: rejected because it violates REQ-001
- Deleting the file: blocked pending UNK-01 resolution — cannot decide without human judgment
- Inferring `tags` from content analysis: too speculative without knowing file purpose

## Implementation

### Target file

`docs/databases/active_databases.md`

### Procedure

1. Read the current document to understand its content and determine appropriate title
2. Insert YAML Front Matter before the document content:
   ```yaml
   ---
   title: "<document title inferred from content>"
   area: databases
   tags: []
   related: []
   status: draft
   ---
   ```
3. If no H1 heading exists after Front Matter, add `# <Title>` as the first line after Front Matter
4. Insert `## Keywords\n<placeholder>` before the first `## ` heading (or after the H1 if no headings exist)
5. Insert `## Related Documents\n<placeholder>` after the `## Keywords` section
6. Verify Markdown structure is not broken

### Method

Prepend YAML Front Matter block to the file, then insert structural sections between the H1 heading and the first `## Status` heading.

### Details

Current state (approximate):
```markdown
<no Front Matter>
<document content begins>
```

After modification:
```markdown
---
title: "Active Databases"
area: databases
tags: []
related: []
status: draft
---

# Active Databases

## Keywords
<placeholder>

## Related Documents
<placeholder>

<existing content continues>
```

Steps:
1. Determine the document title from the content (likely "Active Databases" based on filename)
2. Prepend the YAML Front Matter block shown above
3. Ensure exactly one `# ` heading exists after Front Matter (add if missing)
4. Insert `## Keywords\n<placeholder>` after the H1 heading
5. Insert `## Related Documents\n<placeholder>` after the `## Keywords` section

## Compatibility considerations

- Adding Front Matter does not alter existing document content
- Adding an H1 heading changes visual hierarchy but is required by REQ-003
- Adding `## Keywords` and `## Related Documents` sections does not alter any existing content
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — adding metadata and documentation sections does not affect access control or authentication.

## Rollback considerations

1. Remove the added YAML Front Matter block to restore original state
2. Remove the added H1 heading if it was newly created
3. Remove the eight inserted lines (`## Keywords`, `<placeholder>`, `## Related Documents`, `<placeholder>`) to restore original structure

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding missing required fields, H1 count, and missing sections.

## Completion criteria

- YAML Front Matter present with all four required fields: `title`, `area`, `tags`, `related`
- Exactly one H1 heading present after modification
- `## Keywords` section present after H1 heading
- `## Related Documents` section present after `## Keywords` section
- `<placeholder>` content present under each section
- All existing content preserved unchanged
- Markdown structure not broken

## Out of scope

- Modifying any other file
- Deciding whether this file should exist (blocked by UNK-01)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-084820 | 20260923-084820 | Blocked by UNK-01 |
| 2 | Add or update tests per Validation plan | Completed | 20260923-084844 | 20260923-084844 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-084844 | 20260923-084844 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-084844 | 20260923-084844 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: Should `docs/databases/active_databases.md` exist? Requires human judgment | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003, REQ-004
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/databases/active_databases.md