## Goal

Add missing H1 heading, add missing `## Keywords` section, and fix invalid `related` reference in `docs/04_mcp_05_01_access-control-and-allowlists.md` per REQ-003, REQ-004, REQ-002.

## Scope

Modify only `docs/04_mcp_05_01_access-control-and-allowlists.md` to add an H1 heading, add a missing structural section, and fix an invalid cross-reference in its YAML Front Matter.

## Assumptions

- The file exists with 0 H1 headings (confirmed by `check_docs_structure.py`)
- The file is missing the required `## Keywords` section (confirmed by `check_docs_structure.py`)
- The file has an invalid `related` reference (confirmed by `check_docs_structure.py`)
- All three changes are needed: adding H1, adding section, fixing reference

## Design decisions

- Add `# <Title>` as the first line after Front Matter to satisfy REQ-003
- Add `## Keywords\n<placeholder>` section as minimal valid content per Plan's Approach
- Fix the invalid `related` reference using git history to find the correct filename

## Alternatives considered

- Adding specific references to `## Keywords`: too speculative without knowing which documents are relevant
- Removing the invalid `related` reference entirely: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002

## Implementation

### Target file

`docs/04_mcp_05_01_access-control-and-allowlists.md`

### Procedure

1. Read the current Front Matter of `docs/04_mcp_05_01_access-control-and-allowlists.md`
2. Determine the document title from the filename/content
3. Insert `# <Title>` as the first line after Front Matter
4. Identify the invalid `related` reference
5. Fix the invalid `related` reference using git history
6. Insert `## Keywords\n<placeholder>` after the H1 heading (before the first `## ` heading)
7. Verify Markdown structure is not broken

### Method

Prepend an H1 heading after Front Matter; string replacement within the YAML Front Matter block for the reference fix; insert a new section between the H1 heading and the first `## Status` heading.

### Details

Current state (approximate):
```yaml
---
title: "Access Control and Allowlists"
area: mcp
tags: []
related:
  - <invalid-reference>
status: draft
---

<no H1 heading>
<document content begins>
```

After modification:
```yaml
---
title: "Access Control and Allowlists"
area: mcp
tags: []
related:
  - <corrected-filename>
status: draft
---

# Access Control and Allowlists

## Keywords
<placeholder>

<document content continues>
```

Steps:
1. Determine the document title from the filename (likely "Access Control and Allowlists")
2. Prepend `# Access Control and Allowlists` after the Front Matter closing `---`
3. Run `git log --all --diff-filter=D -- "**/<invalid-reference>"` to find the actual filename
4. Replace the invalid reference in the Front Matter with the actual filename
5. Insert `## Keywords\n<placeholder>` after the new H1 heading
6. Verify the YAML indentation and Markdown structure remain valid

## Compatibility considerations

- Adding an H1 heading changes visual hierarchy but is required by REQ-003
- Changing a cross-reference does not alter document content
- Adding a `## Keywords` section does not alter any existing content
- The new filename resolves to an existing file in the repository
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — adding metadata, headings, and documentation sections does not affect access control or authentication.

## Rollback considerations

1. Remove the added H1 heading to restore original state
2. Revert the string replacement to restore original reference
3. Remove the inserted `## Keywords\n<placeholder>` section to restore original structure
4. No data loss risk — changes are purely additive

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 count, missing sections, and invalid cross-references.

## Completion criteria

- Exactly one H1 heading present after modification
- `related` entry contains corrected filename instead of the invalid reference
- `## Keywords` section present after the H1 heading
- `<placeholder>` content present under the section
- YAML syntax remains valid
- Cross-reference resolves to an existing file in the repository
- Markdown structure not broken

## Out of scope

- Modifying any other file
- Determining whether additional references should be added to `## Keywords`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-133809 | 20260923-133809 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-133809 | 20260923-133809 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-133809 | 20260923-133809 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-133809 | 20260923-133809 |  |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/04_mcp_05_01_access-control-and-allowlists.md