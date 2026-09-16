## Goal

Update `docs/adr/ADR-002-config-isolation.md` to reflect that `AGENT_RESTRICT_CONFIG` is now obsolete per REQ-001.

## Scope

- Modify `docs/adr/ADR-002-config-isolation.md`: update the ADR to remove references to the environment variable guard.

## Assumptions

- The ADR currently documents the `AGENT_RESTRICT_CONFIG` environment variable as a deliberate test-isolation decision.
- The ADR should be updated to reflect the new unconditional behavior.

## Design decisions

- Remove the paragraph about `AGENT_RESTRICT_CONFIG` being a deliberate test-isolation decision.
- Replace it with a note that the restriction is now unconditional.

## Alternatives considered

- Creating a new ADR for this change — rejected: out of scope for REQ-008.
- Keeping the old text and adding a "Changes Since" section — rejected: would leave stale information.

## Implementation

### Target file

`docs/adr/ADR-002-config-isolation.md`

### Procedure

1. Find the paragraph mentioning `AGENT_RESTRICT_CONFIG` and replace it.

### Method

- **Step 1**: In the ADR, find the paragraph about `AGENT_RESTRICT_CONFIG`:

```markdown
# Before:
The `AGENT_RESTRICT_CONFIG` environment variable was added as a deliberate test-isolation decision. It allows tests to load non-`agent.toml` files by skipping the restriction call. However, this means production Agent processes can still load unintended configuration files if the env var is unset.

# After:
The restriction is now unconditional. Every process entry point calls `ConfigLoader.restrict_to("agent.toml")` regardless of environment variables. The `AGENT_RESTRICT_CONFIG` environment variable is obsolete and has been removed.
```

### Details

**Step 1 — Update the ADR:**

Replace lines ~20-30 in `docs/adr/ADR-002-config-isolation.md`:

```markdown
The restriction is now unconditional. Every process entry point calls `ConfigLoader.restrict_to("agent.toml")` regardless of environment variables. The `AGENT_RESTRICT_CONFIG` environment variable is obsolete and has been removed.
```

This replaces the previous paragraph about the environment variable being a deliberate test-isolation decision.

## Compatibility considerations

- No behavioral change. This is a documentation update reflecting the new unconditional behavior.
- Existing references to `AGENT_RESTRICT_CONFIG` in the ADR will be replaced with the new unconditional description.

## Security considerations

- No security impact. This is a documentation update reflecting the new unconditional behavior.

## Rollback considerations

- Reverting restores the pre-fix documentation but does not affect source code.

## Validation plan

- Read the updated ADR to verify the replacement is accurate.
- No automated validation needed for documentation-only changes.

## Completion criteria

- `AGENT_RESTRICT_CONFIG` paragraph removed from the ADR.
- New paragraph reflects the unconditional restriction behavior.
- Documentation accurately describes the current state.

## Out of scope

- Modifying any source code — covered in previous rows (REQ-001).
- Modifying `tests/conftest.py` — covered in previous row (REQ-001).
- Modifying `tests/agent/test_context.py` — covered in previous row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update ADR to remove AGENT_RESTRICT_CONFIG reference | Pending | — | — | |
| 2 | Verify documentation accuracy | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: docs/adr/ADR-002-config-isolation.md
