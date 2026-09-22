## Goal

Fix invalid `related` references and add `## Keywords` section in `docs/adr/ADR-010-rag-fallback.md`: update invalid `related` refs per REQ-003, add missing section per REQ-005.

## Scope

Modify only `docs/adr/ADR-010-rag-fallback.md` to:
1. Update invalid `related` field references from ADR-style names to proper filenames
2. Add `## Keywords\n<placeholder>` section

## Assumptions

- The document has an invalid `related` reference pointing to a non-existent ADR file (confirmed by `check_docs_structure.py`)
- The document already has a `## Keywords` section with `<placeholder>` content — no addition needed
- Existing Front Matter values must not be changed except for updating the references

## Design decisions

- Update the invalid `related` reference to point to the correct filename — Plan's Approach states "If found under new name, update the reference"

## Alternatives considered

- Removing the invalid `related` entry entirely: rejected because it would lose existing cross-references
- Adding a new `source` field instead of fixing `related`: rejected because the issue is specific to `related`

## Implementation

### Target file

`docs/adr/ADR-010-rag-fallback.md`

### Procedure

1. Read the current document to identify the `related:` line in Front Matter containing the invalid ADR reference
2. Locate the `related:` line in Front Matter that contains the invalid reference (`ADR-002`)
3. Replace the invalid ADR name with its correct filename equivalent
4. Verify Markdown structure is not broken

### Method

Use string replacement on the `related:` line in Front Matter.

### Details

Current structure (actual):
```yaml
---
title: "ADR-010: RAGの外部実行失敗時のインプロセスフォールバック"
area: governance
tags:
  - rag
  - fallback
  - in-process
decision_scope:
  - rag
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-010: RAGの外部実行失敗時のインプロセスフォールバック

## Keywords
<placeholder>

## Status
...
```

After modification:
```yaml
---
title: "ADR-010: RAGの外部実行失敗時のインプロセスフォールバック"
area: governance
tags:
  - rag
  - fallback
  - in-process
decision_scope:
  - rag
related:
  - adr/ADR-002-git-mcp-server-side-write-enforcement.md
supersedes: []
superseded_by: null
---

# ADR-010: RAGの外部実行失敗時のインプロセスフォールバック

## Keywords
<placeholder>

## Status
...
```

Steps:
1. Replace `related:\n  - ADR-002` with `related:\n  - adr/ADR-002-git-mcp-server-side-write-enforcement.md` in Front Matter

## Compatibility considerations

- Updating invalid `related` references does not change existing section meanings or other Front Matter values
- Adding `## Keywords` section does not alter any existing content
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — updating documentation references does not affect access control or authentication.

## Rollback considerations

1. Revert the `related:` field to its original value in Front Matter
2. Remove the two inserted lines (`## Keywords` and `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references and missing sections.

## Completion criteria

- Invalid `related` references updated to correct filenames
- `## Keywords` section present after H1 heading
- `<placeholder>` content present under the section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260922-232136 | 20260922-232136 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260922-232138 | 20260922-232138 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260922-232140 | 20260922-232140 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260922-232142 | 20260922-232142 |  |

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
- **Requirement ID**: REQ-003, REQ-005
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/adr/ADR-010-rag-fallback.md