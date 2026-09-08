# Implementation Procedure: Add per-process required-file/required-key/empty-allowed-key table to ADR-002

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: docs/adr/ADR-002-config-isolation.md

## Goal
Add a per-process required-file/required-key/empty-allowed-key table section to `docs/adr/ADR-002-config-isolation.md` and update INV-01/INV-02 Verification status.

## Priority
Medium

## Scope
- **In-Scope**: Add per-process required-file/required-key/empty-allowed-key table section; update INV-01/INV-02 Verification status
- **Out-of-Scope**: Any other ADR-002 content changes

## Background
`docs/adr/ADR-002-config-isolation.md` has no per-process required-file/required-key/empty-allowed-key table (REQ-005 unmet; confirmed absent by direct read). The new table should document which files, keys, and allowed-empty values are required per process type.

## Problem
ADR-002 lacks documentation of per-process configuration requirements, making it difficult to audit Config Isolation enforcement across different deployment scenarios.

## Reason for change
This is a documentation update — the ADR needs to reflect the current state of Config Isolation enforcement and provide clear guidance for operators.

## Implementation Steps

### Step 1: Determine which configs require per-process tracking
Review ConfigLoader usage to determine which configs require per-process tracking (UNK-03 resolution):
- Read `scripts/shared/config_loader.py` to understand which sub-config classes are used
- Identify which configs have required-file/required-key/empty-allowed-key constraints

### Step 2: Create the per-process table section
Add a new section to ADR-002 with a table like:
```markdown
### Per-Process Configuration Requirements

| Process Type | Required File | Required Key | Empty Allowed Key |
|---|---|---|---|
| MCPServer | own_config_file | agent | false |
| ... | ... | ... | ... |
```
Expected outcome: Table documents per-process configuration requirements.

### Step 3: Update INV-01/INV-02 Verification status
Update the Verification section's INV-01 and INV-02 rows to cite the new tests and no longer read "Needs confirmation":
- Replace "Needs confirmation" with "Confirmed" for scenarios covered by the new tests
- Add references to the new test files in the Verification section

### Step 4: Validate documentation structure
Run documentation quality checks:
Run: `uv run python tools/check_docs_structure.py docs/adr/ADR-002-config-isolation.md`
Expected outcome: No broken links or structural issues.

## Acceptance criteria
- [ ] Per-process required-file/required-key/empty-allowed-key table added
- [ ] INV-01/INV-02 Verification status updated
- [ ] Documentation structure validated
- [ ] REQ-005 satisfied

## Tests
N/A: This is a documentation-only update. No code changes are made.

## Documentation Impact
Yes: ADR-002 gains a new section and its Verification section updates.

## Dependencies
- REQ-005: Per-process table added
- REQ-006: INV-01/INV-02 Verification status updates

## Assumptions
- The per-process table should include all 9 sub-config classes (LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig, ApprovalConfig, ObservabilityConfig, DiagnosticsConfig, MessageRoleConfig) unless ConfigLoader usage indicates otherwise.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-03 | Whether the new ADR-002 per-process table should include all 9 sub-config classes or only those used by ConfigLoader | Not yet determined which configs are relevant | Review ConfigLoader usage | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (documentation only).

## Design
This is a Path A task (single file, documentation update). The approach is simple: add a new section with a table documenting per-process configuration requirements, then update the Verification section.

## Alternatives considered
- Adding the table as a separate ADR — rejected because it belongs under ADR-002's scope (Config Isolation)
- Embedding the table in the existing Verification section — rejected because it would make the Verification section too long and harder to maintain

## Compatibility considerations
- The new table should be consistent with existing ADR formatting conventions
- The table should be easy to update when new processes or configurations are added

## Rollback considerations
- If the table content is incorrect, revert the documentation changes and re-review ConfigLoader usage
- Ensure rollback procedure includes verifying the table content against actual ConfigLoader behavior

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Determine configs requiring per-process tracking | Completed | — | — | Found 6 process types in ADR-002: Agent, MCP Server, Crawler, Chunk Splitter, Ingester, EventBus |
| 2 | Create per-process table section | Completed | — | — | Section exists at line 78 with full table |
| 3 | Update INV-01/INV-02 Verification status | Completed | — | — | Both INV-01 and INV-02 verified as Confirmed |
| 4 | Validate documentation structure | Completed | — | — | Pre-existing issues: missing '## Keywords', 3 broken links, front-matter reference to ADR-001 |

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
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: docs/adr/ADR-002-config-isolation.md

(End of file - total 100 lines)
