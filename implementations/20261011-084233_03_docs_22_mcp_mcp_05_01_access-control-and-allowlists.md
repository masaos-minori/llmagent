## Goal

Update the cicd-mcp workflow allowlist documentation to the file-name form and remove the dangling MCP-003 reference (`REQ-003`: documentation reflects the file-name form).

## Scope

- Modify only `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`.

## Assumptions

- The accepted form is now a file name (e.g. `ci.yml`), consistent with `REQ-001` / `REQ-002`.

## Design decisions

- Change the "To allow specific workflows" example (lines 216-219) from full-path entries to file-name entries.
- Remove/update the sentence on line 211 that references MCP-003 and states the config/guard form mismatch, since the mismatch is resolved by this change.

## Alternatives considered

- Leave the MCP-003 sentence: rejected — MCP-003 is removed from the ledger (`REQ-003` row 4), so a dangling reference would remain.

## Implementation

### Target file

`docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`

### Procedure

1. Line 211: remove the clause tracking the form mismatch as MCP-003 (the mismatch no longer exists after `REQ-001` / `REQ-002`); rephrase to state the accepted form is a file name.
2. Lines 216-219: change the example to file-name form:

```toml
workflow_allowlist = [
    "deploy.yml",
    "ci.yml",
]
```

### Method

Edit the two locations; leave other servers' sections untouched.

### Details

- Current evidence: line 211 references MCP-003 and the current form mismatch; lines 216-219 show full-path examples.

## Compatibility considerations

- Documents the migration from full-path to file-name form for operators.

## Security considerations

- Documentation-only; no behavior change. Ensure examples do not imply widening the allow-list.

## Rollback considerations

- Revert the two edits.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/22_mcp/mcp_05_01_access-control-and-allowlists.md | Documentation review | manual | Examples use file-name form; no dangling MCP-003 reference |

## Completion criteria

- Examples use file-name form; no remaining reference to a removed MCP-003 entry; doc parses as valid Markdown.

## Out of scope

- Config (`REQ-001`), guard (`REQ-002`), governance ledger (`REQ-003` row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update mcp_05_01 examples to file-name form and drop MCP-003 reference (REQ-003) | Completed | — | 20261011-091023 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261011-091023 | N/A: documentation review only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261011-091023 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261011-091023 |  |

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
- **Requirement ID**: REQ-003 — update documentation so it reflects the file-name form
- **Source issue**: issues/done/20261007-154047_cicdallow01_unify-cicd-mcp-workflow_allowlist-to-file-name-form.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162442_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-084233
- **Related target files**: docs/22_mcp/mcp_05_01_access-control-and-allowlists.md