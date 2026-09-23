## Goal

Truncate the malformed `related` entry in `docs/04_mcp_02_03_audit-logging-and-errors.md`
per REQ-002. The `## Related Documents` section already exists (confirmed present at
line 92 of the current file) and is out of scope for this document.

## Scope

Modify only `docs/04_mcp_02_03_audit-logging-and-errors.md`'s YAML Front Matter to
truncate one malformed `related` list entry — remove the trailing description text,
keep the filename.

## Assumptions

- The file's `related` field's last entry is
  `00_security_01_architecture-and-trust-boundaries.md — System architecture / trust
  boundaries / threat modeling / authentication & authorization / auditing / local vs
  production / Fail-open/Fail-closed / prompt injection responsibility boundaries`
  (confirmed via Read) — a real, existing filename with a long description string
  incorrectly appended after it
- Every other `related` entry in this and every other document in the repository is a
  bare filename with no trailing text, confirming this is a malformed reference, not
  an intentional description field
- The fix is a truncation only — remove everything from ` — ` onward, keep the
  filename `00_security_01_architecture-and-trust-boundaries.md` unchanged

## Design decisions

- Truncate the entry at the filename boundary (remove everything from ` — ` onward)
  rather than looking up a "corrected" filename via git history — the filename itself
  is already correct; only the appended description text is the defect
- Keep the same YAML structure — only modify this one list entry's value

## Alternatives considered

- Removing the entry entirely: rejected — the filename itself is valid and the
  reference should be preserved, only the malformed suffix removed
- Treating this as a renamed-file lookup (git history search): rejected — the
  filename `00_security_01_architecture-and-trust-boundaries.md` already exists in
  the repository; this is not a stale short-name reference like the 6 ADR files

## Implementation

### Target file

`docs/04_mcp_02_03_audit-logging-and-errors.md`

### Procedure

1. Read the current Front Matter of `docs/04_mcp_02_03_audit-logging-and-errors.md`
2. Locate the last `related` list entry containing
   ` — System architecture / trust boundaries / ...`
3. Truncate the entry at the filename boundary, keeping only
   `00_security_01_architecture-and-trust-boundaries.md`
4. Verify YAML syntax is correct after modification

### Method

String replacement within the YAML Front Matter block: truncate one `related` list
entry's value at ` — `. No other section of the file is touched.

### Details

Current state (confirmed via Read):
```yaml
---
title: "MCP Audit Log Format and Common Error Handling"
area: mcp
tags:
  - mcp
  - audit
  - logging
  - errors
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_02_02_startup-modes-and-health.md
  - 00_security_01_architecture-and-trust-boundaries.md — System architecture / trust boundaries / threat modeling / authentication & authorization / auditing / local vs production / Fail-open/Fail-closed / prompt injection responsibility boundaries
---
```

After modification:
```yaml
---
title: "MCP Audit Log Format and Common Error Handling"
area: mcp
tags:
  - mcp
  - audit
  - logging
  - errors
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_02_02_startup-modes-and-health.md
  - 00_security_01_architecture-and-trust-boundaries.md
---
```

Steps:
1. Replace the malformed last `related` entry with the bare filename
   `00_security_01_architecture-and-trust-boundaries.md`
2. Verify the YAML indentation and Markdown structure remain valid

## Compatibility considerations

- Truncating the cross-reference does not alter document content
- The filename portion already resolves to an existing file in the repository

## Security considerations

No security impact — truncating a cross-reference string does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacement to restore the original (malformed) reference; no
   other content was touched

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/04_mcp_02_03_audit-logging-and-errors.md" --schema schemas/doc_front_matter.json` — expect zero findings for this file.

## Completion criteria

- `related`'s last entry is the bare filename `00_security_01_architecture-and-trust-boundaries.md`
  with no trailing text
- YAML syntax remains valid
- Cross-reference resolves to an existing file in the repository
- Markdown structure not broken

## Out of scope

- Modifying any other file
- The `## Related Documents` section (already present)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-133747 | 20260923-133747 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-133747 | 20260923-133747 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-133747 | 20260923-133747 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-133747 | 20260923-133747 |  |

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
- **Source issue**: issues/done/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/04_mcp_02_03_audit-logging-and-errors.md