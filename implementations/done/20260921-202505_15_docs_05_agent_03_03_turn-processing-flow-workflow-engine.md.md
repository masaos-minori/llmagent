## Goal

Clarify CLI command references in the document — distinguish between top-level commands and subcommands where the consistency checker flagged false positives.

## Scope

- Clarify that /stats is registered as a subcommand in _COMMANDS
- Add documentation explaining the distinction between top-level commands and subcommands

## Assumptions

- The CLI command is registered as a subcommand in the _COMMANDS dictionary
- The document currently contains references suggesting it is a top-level command that needs correction

## Design decisions

- Directly clarify the distinction rather than adding a deprecation notice — the current value is incorrect, not deprecated
- Preserve any context about what the CLI command does if documented elsewhere

## Alternatives considered

- Adding [CORRECTED] prefix to the reference instead of updating it — rejected because the current value is incorrect, not deprecated
- Keeping both values with explanation — rejected because this adds confusion without actionable information

## Implementation

### Target file

docs/05_agent_03_03_turn-processing-flow-workflow-engine.md

### Procedure

1. Locate all occurrences of /stats in the document
2. Determine if the references suggest they are top-level commands when they are actually subcommands
3. Update the references to clarify they are subcommands

### Method

Read the file, identify the exact line numbers containing the incorrect references, replace them with the correct values, and verify against the source files.

### Details

**CLI command verification:**
- Current content may suggest /stats is a top-level command
- Action: Clarify that it is registered as a subcommand in _COMMANDS
- The configuration file explicitly states its purpose and location

**Verification steps:**
1. Confirm /stats exists in the scripts/agent/commands/command_defs_list.py file
2. Search for all occurrences of this command in the document
3. Replace each occurrence with the correct filename if the module still exists, or remove the reference if the module has been deleted entirely
4. Verify no other references to this command remain in the document

## Compatibility considerations

- Updating the filename may break connections from developers who have configured their systems based on the old documentation
- Mitigation: The change aligns with the actual configuration, so it will help developers connect correctly

## Security considerations

- Correct filenames are important for security — using the wrong file could lead to connecting to unintended services
- This fix improves security by ensuring developers connect to the correct service

## Rollback considerations

- If the filename needs to be reverted later, they can be recovered from Git history using git log --all -- docs/<filename>
- The Migration Notes section already documents this restoration method

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| docs/05_agent_03_03_turn-processing-flow-workflow-engine.md | Manual review | CLI cmd refs clarified |
| docs/05_agent_03_03_turn-processing-flow-workflow-engine.md | Automated check | uv run python tools/check_docs_consistency.py passes without WARNING-level findings for missing files |

## Completion criteria

- [ ] All references to /stats replaced with correct function names or removed
- [ ] Function names match actual source files
- [ ] No broken internal links introduced by the change
- [ ] Consistency checker passes without WARNING-level findings for this file

## Out of scope

- Modifying other files that reference these function names
- Restructuring the configuration section
- Adding new documentation about the configuration files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Clarify CLI command references | Completed | 20260922-055028 | 20260922-055028 | REQ-005 |
| 2 | Validate with consistency checker | Completed | 20260922-055028 | 20260922-055028 | REQ-005 |

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
- **Requirement ID**: REQ-005 — Clarify CLI command references (subcommands vs top-level)
- **Source issue**: issues/20260921-193416_doc_critical_inconsistencies.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260921-201621_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-202505
- **Related target files**: docs/05_agent_03_03_turn-processing-flow-workflow-engine.md