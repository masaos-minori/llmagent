## Goal

Remove reference to deleted file (`04_mcp_04_06_browser.md`) from the web-search-mcp document guide and update the browser-mcp merge note to reflect current state.

## Scope

- Remove stale file reference in the File Index section
- Update the browser-mcp merge note to clarify that old _06 was deleted during restructuring

## Assumptions

- The browser-mcp merge note already exists and can be referenced instead of keeping the deleted file reference
- Migration Notes already document the deletion history

## Design decisions

- Remove the reference entirely rather than adding deprecation notices — Migration Notes already explain deletion
- Preserve the existing migration note about browser-mcp merging into web-search-mcp under _01 on 2026-07-20

## Alternatives considered

- Adding `[DELETED]` prefix to references instead of removing them — rejected because Migration Notes already explain deletion
- Keeping references but marking them as historical — rejected because this adds noise without actionable information

## Implementation

### Target file

`docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Locate the File Index section (lines ~13-17)
2. Remove or update the bullet point referencing `04_mcp_04_06_browser.md`
3. Verify the browser-mcp merge note already exists (line ~92 mentions old _06 was deleted)
4. Update the Legacy Source Document Policy section if needed to clarify that the old _06 was deleted during restructuring

### Method

Read the file, identify the exact line numbers containing the reference, remove the bullet point, and update the Legacy Source Document Policy section to explicitly state the deletion date and git restoration method.

### Details

**File Index section (lines ~13-17):**
- Current content lists three files including `04_mcp_04_06_browser.md`
- Action: Remove the bullet point referencing `04_mcp_04_06_browser.md` since the file no longer exists
- The policy statement "If there is a discrepancy between old and new files, trust the newly restructured files" should remain as it provides useful guidance

**Migration Note verification:**
- Line ~92 mentions "browser-mcp was merged into web-search-mcp under _01 on 2026-07-20; old _06 was deleted"
- This confirms the pattern of documenting deletions in File Index notes rather than keeping broken references

## Compatibility considerations

- Removing references may break bookmarks or links from developers who have saved URLs pointing to these deleted files
- Mitigation: The Migration Notes section already explains where content was moved, so developers can find the current locations

## Security considerations

None — this is a documentation cleanup task with no security implications.

## Rollback considerations

- If references need to be restored later, they can be recovered from Git history using `git log --all -- docs/<filename>`
- The Migration Notes section already documents this restoration method

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| docs/04_mcp_04_01_web-search-file-read-github.md | Manual review | No references to deleted files remain in File Index section |
| docs/04_mcp_04_01_web-search-file-read-github.md | Manual review | Browser-mcp merge note accurately describes deletion status |
| docs/04_mcp_04_01_web-search-file-read-github.md | Automated check | `uv run python tools/check_docs_consistency.py --domain mcp` passes without ERROR-level findings |

## Completion criteria

- [ ] All references to `04_mcp_04_06_browser.md` removed from File Index section
- [ ] Browser-mcp merge note accurately reflects deletion status
- [ ] No broken internal links introduced by the removal
- [ ] Consistency checker passes without ERROR-level findings for this file

## Out of scope

- Modifying other files that reference this deleted file
- Restructuring the Migration Notes section
- Adding new documentation about the deleted file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove deleted file reference from File Index section | Completed | 20260921-204813 | 20260921-204813 | REQ-001 |
| 2 | Update browser-mcp merge note if needed | Completed | 20260921-204822 | 20260921-204822 | REQ-001 |
| 3 | Validate with consistency checker | Completed | 20260921-204822 | 20260921-204822 | REQ-001 |

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
- **Requirement ID**: REQ-001 — Remove references to deleted files
- **Source issue**: issues/20260921-193416_doc_critical_inconsistencies.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260921-201621_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-202505
- **Related target files**: docs/04_mcp_04_01_web-search-file-read-github.md