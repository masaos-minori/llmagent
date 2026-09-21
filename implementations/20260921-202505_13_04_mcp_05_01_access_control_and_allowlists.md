## Goal

Correct file path from `service_pull_requests.py` to `github_service_pull_requests.py` in the access control and allowlists document.

## Scope

- Update the incorrect file path to point to the correct location
- Verify the change against actual source files

## Assumptions

- The module was renamed during restructuring and the current name should be used
- The document currently contains a reference to a non-existent file that needs correction

## Design decisions

- Directly update the filename rather than adding a deprecation notice — the old file no longer exists
- Preserve any context about what the module does if documented elsewhere

## Alternatives considered

- Adding `[CORRECTED]` prefix to the reference instead of updating it — rejected because the current value is incorrect, not deprecated
- Keeping both values with explanation — rejected because this adds confusion without actionable information

## Implementation

### Target file

`docs/04_mcp_05_01_access-control-and-allowlists.md`

### Procedure

1. Locate all occurrences of `service_pull_requests.py` in the document
2. Replace each occurrence with the correct filename `github_service_pull_requests.py`
3. Verify the change against actual source files

### Method

Read the file, identify the exact line numbers containing the incorrect filename, replace them with the correct value, and verify against the source file.

### Details

**Module verification:**
- Current content references `scripts/mcp_servers/github/service_pull_requests.py` which does not exist
- Action: Replace with `scripts/mcp_servers/github/github_service_pull_requests.py` which is the actual configuration file
- The configuration file explicitly states its purpose and location

**Verification steps:**
1. Confirm `github_service_pull_requests.py` exists in the scripts/mcp_servers/github/ directory
2. Search for all occurrences of `service_pull_requests.py` in the document
3. Replace each occurrence with `github_service_pull_requests.py`
4. Verify no other references to `service_pull_requests.py` remain in the document

## Compatibility considerations

- Updating the filename may break connections from developers who have configured their systems based on the old documentation
- Mitigation: The change aligns with the actual configuration, so it will help developers connect correctly

## Security considerations

- Correct filenames are important for security — using the wrong file could lead to connecting to unintended services
- This fix improves security by ensuring developers connect to the correct service

## Rollback considerations

- If the filename needs to be reverted later, they can be recovered from Git history using `git log --all -- docs/<filename>`
- The Migration Notes section already documents this restoration method

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| docs/04_mcp_05_01_access-control-and-allowlists.md | Manual review | Correct file path shown |
| docs/04_mcp_05_01_access-control-and-allowlists.md | Automated check | `uv run python tools/check_docs_consistency.py --domain mcp` passes without WARNING-level findings for missing files |

## Completion criteria

- [ ] All references to `service_pull_requests.py` replaced with `github_service_pull_requests.py`
- [ ] Filename matches actual source file
- [ ] No broken internal links introduced by the change
- [ ] Consistency checker passes without WARNING-level findings for this file

## Out of scope

- Modifying other files that reference this filename
- Restructuring the configuration section
- Adding new documentation about the configuration file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace service_pull_requests.py with github_service_pull_requests.py | Pending | — | — | REQ-004 |
| 2 | Validate with consistency checker | Pending | — | — | REQ-004 |

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
- **Requirement ID**: REQ-004 — Update or remove references to non-existent Python modules
- **Source issue**: issues/20260921-193416_doc_critical_inconsistencies.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260921-201621_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-202505
- **Related target files**: docs/04_mcp_05_01_access-control-and-allowlists.md
