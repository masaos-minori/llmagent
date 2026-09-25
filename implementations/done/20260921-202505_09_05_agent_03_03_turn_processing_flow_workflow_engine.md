## Goal

Update or remove reference to non-existent configuration file (`config/workflows/production.json`) in the turn processing flow workflow engine document, and clarify CLI command references (subcommands vs top-level).

## Scope

- Update references to `config/workflows/production.json` to point to the correct location or remove them if they no longer exist
- Clarify CLI command references — distinguish between top-level commands and subcommands where the consistency checker flagged false positives

## Assumptions

- The configuration file was deleted during restructuring and the current name should be used
- The document currently contains a reference to a non-existent file that needs correction
- CLI command references need clarification to distinguish between top-level commands and subcommands

## Design decisions

- Directly update the filename rather than adding a deprecation notice — the old file no longer exists
- Preserve any context about what the configuration file does if documented elsewhere
- Clarify CLI command references without removing valid references

## Alternatives considered

- Adding `[CORRECTED]` prefix to the reference instead of updating it — rejected because the current value is incorrect, not deprecated
- Keeping both values with explanation — rejected because this adds confusion without actionable information

## Implementation

### Target file

`docs/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure

1. Locate all occurrences of `production.json` in the document
2. Determine if the file still exists under a different name or has been deleted entirely
3. Update the reference accordingly or remove it if the file no longer exists
4. Clarify CLI command references — distinguish between top-level commands and subcommands

### Method

Read the file, identify the exact line numbers containing the incorrect filenames, replace them with the correct values, and verify against the source files.

### Details

**Configuration file verification:**
- Current content references `config/workflows/production.json` which does not exist
- Action: Replace with the correct filename if the file still exists under a different name, or remove the reference if the file has been deleted entirely
- The configuration file explicitly states its purpose and location

**CLI command verification:**
- Current content may suggest CLI commands are top-level when they are actually subcommands
- Action: Clarify the distinction between top-level commands and subcommands
- The configuration file explicitly states its purpose and location

**Verification steps:**
1. Confirm whether `production.json` exists in the config/workflows/ directory
2. Search for all occurrences of these filenames in the document
3. Replace each occurrence with the correct filename if the file still exists, or remove the reference if the file has been deleted entirely
4. Verify no other references to these files remain in the document

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
| docs/agent_03_03_turn-processing-flow-workflow-engine.md | Manual review | No reference to non-existent config file |
| docs/agent_03_03_turn-processing-flow-workflow-engine.md | Automated check | `uv run python tools/check_docs_consistency.py --domain agent` passes without WARNING-level findings for missing files |

## Completion criteria

- [ ] All references to `production.json` replaced with correct filename or removed
- [ ] Filename matches actual config file
- [ ] No broken internal links introduced by the change
- [ ] Consistency checker passes without WARNING-level findings for this file

## Out of scope

- Modifying other files that reference this filename
- Restructuring the configuration section
- Adding new documentation about the configuration files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace production.json with correct filename or remove reference | Completed | 20260921-220720 | 20260921-220720 | REQ-003 |
| 2 | Clarify CLI command references | Completed | 20260921-220721 | 20260921-220721 | REQ-005 |
| 3 | Validate with consistency checker | Completed | 20260921-220721 | 20260921-220721 | REQ-003 + REQ-005 |

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
- **Requirement ID**: REQ-003 — Update or remove references to non-existent configuration files; REQ-005 — Clarify CLI command references
- **Source issue**: issues/20260921-193416_doc_critical_inconsistencies.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260921-201621_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-202505
- **Related target files**: docs/agent_03_03_turn-processing-flow-workflow-engine.md