## Goal

Correct git-mcp port number from 8000 to 8014 in the auth profiles and sandboxing document to match the actual configuration.

## Scope

- Update git-mcp port number from 8000 to 8014 in the document
- Verify the change against config/agent.toml line 369

## Assumptions

- The port number in config/agent.toml is authoritative and should be used as the source of truth
- The document currently contains an incorrect port number that needs correction

## Design decisions

- Directly update the port number rather than adding a deprecation notice — the current value is simply wrong
- Preserve any context about why the port was set to 8014 if documented elsewhere

## Alternatives considered

- Adding `[CORRECTED]` prefix to the reference instead of updating it — rejected because the current value is incorrect, not deprecated
- Keeping both values with explanation — rejected because this adds confusion without actionable information

## Implementation

### Target file

`docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure

1. Locate all occurrences of git-mcp port 8000 in the document
2. Replace each occurrence with the correct port number 8014
3. Verify the change against config/agent.toml line 369 which shows `url = "http://127.0.0.1:8014"` for git-mcp

### Method

Read the file, identify the exact line numbers containing the incorrect port number, replace them with the correct value, and verify against the configuration file.

### Details

**Port number verification:**
- Current content shows git-mcp running on port 8000
- Action: Replace with port 8014 to match config/agent.toml line 369
- The configuration file explicitly states `url = "http://127.0.0.1:8014"` for git-mcp

**Verification steps:**
1. Read config/agent.toml and confirm git-mcp section has `url = "http://127.0.0.1:8014"`
2. Search for all occurrences of port 8000 related to git-mcp in the document
3. Replace each occurrence with 8014
4. Verify no other references to port 8000 remain in the document

## Compatibility considerations

- Updating the port number may break connections from developers who have configured their systems based on the old documentation
- Mitigation: The change aligns with the actual configuration, so it will help developers connect correctly

## Security considerations

- Correct port numbers are important for security — using the wrong port could lead to connecting to unintended services
- This fix improves security by ensuring developers connect to the correct service

## Rollback considerations

- If the port number needs to be reverted later, they can be recovered from Git history using `git log --all -- docs/<filename>`
- The Migration Notes section already documents this restoration method

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| docs/04_mcp_05_02_auth-profiles-and-sandboxing.md | Manual review | git-mcp port shows 8014 |
| docs/04_mcp_05_02_auth-profiles-and-sandboxing.md | Automated check | `uv run python tools/check_docs_consistency.py --domain mcp` passes without ERROR-level findings |

## Completion criteria

- [ ] All references to git-mcp port 8000 replaced with 8014
- [ ] Port number matches config/agent.toml line 369
- [ ] No broken internal links introduced by the change
- [ ] Consistency checker passes without ERROR-level findings for this file

## Out of scope

- Modifying other files that reference this port number
- Restructuring the authentication section
- Adding new documentation about the port number

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace git-mcp port 8000 with 8014 | Completed | 20260921-215308 | 20260921-215308 | REQ-002 |
| 2 | Validate with consistency checker | Completed | 20260921-215308 | 20260921-215308 | REQ-002 |

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
- **Requirement ID**: REQ-002 — Correct git-mcp port number from 8000 to 8014
- **Source issue**: issues/20260921-193416_doc_critical_inconsistencies.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260921-201621_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-202505
- **Related target files**: docs/04_mcp_05_02_auth-profiles-and-sandboxing.md