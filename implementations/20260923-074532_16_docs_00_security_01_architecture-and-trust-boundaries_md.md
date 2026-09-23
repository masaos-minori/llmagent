## Goal

Remove invalid `related` references to `agent/startup.py` and `shared/mcp_health.py` from `docs/00_security_01_architecture-and-trust-boundaries.md` per REQ-002.

## Scope

Modify only `docs/00_security_01_architecture-and-trust-boundaries.md` to remove two invalid cross-references in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with invalid `related` fields pointing to `agent/startup.py` and `shared/mcp_health.py` (confirmed by `check_docs_structure.py`)
- These are source code paths, not documentation paths — they violate REQ-002 (references must resolve to existing files in the repository)
- Two `related` references need removal in this file

## Design decisions

- Remove the invalid references entirely rather than trying to guess their intent
- Keep the same YAML structure — only modify values, not keys
- Use git history as the source of truth for deleted files

## Alternatives considered

- Updating references to point to existing files: rejected because these appear to be source code paths, not documentation paths — updating them would be speculative
- Keeping the old references: rejected because they violate REQ-002

## Implementation

### Target file

`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure

1. Read the current Front Matter of `docs/00_security_01_architecture-and-trust-boundaries.md`
2. Identify the `related` field entries referencing `agent/startup.py` and `shared/mcp_health.py`
3. Remove both invalid references from the `related` array
4. If the `related` array becomes empty, replace it with `[]`
5. Verify YAML syntax is correct after modification

### Method

String removal within the YAML Front Matter block — delete the lines containing invalid references.

### Details

Current state (approximate):
```yaml
---
title: "Architecture and Trust Boundaries"
area: security
tags: []
related:
  - agent/startup.py
  - shared/mcp_health.py
status: draft
---
```

After modification:
```yaml
---
title: "Architecture and Trust Boundaries"
area: security
tags: []
related: []
status: draft
---
```

Steps:
1. Locate the `related:` section in the YAML Front Matter
2. Delete the lines `- agent/startup.py` and `- shared/mcp_health.py`
3. If the `related` array is now empty, replace with `related: []` on a single line
4. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Removing invalid references does not alter document content
- Empty array `[]` is semantically neutral — indicates "no specific related documents" rather than "missing data"
- Schema validation will pass once the invalid references are removed
- This aligns with Plan's Approach: "remove references to intentionally deleted documents"

## Security considerations

No security impact — removing cross-references does not affect access control or authentication.

## Rollback considerations

1. Restore the removed references to their original values
2. No data loss risk — the change is purely a reference removal

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references.

## Completion criteria

- Both `agent/startup.py` and `shared/mcp_health.py` removed from `related` field
- `related` field is either empty `[]` or contains only valid references
- YAML syntax remains valid
- All remaining cross-references resolve to existing files in the repository
- No other fields modified

## Out of scope

- Modifying any other file
- Determining whether the removed references should have pointed to different files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-135308 | 20260923-135308 |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md