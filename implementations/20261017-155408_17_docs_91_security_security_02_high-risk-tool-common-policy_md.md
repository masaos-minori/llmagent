# Implementation Procedure — `docs/91_security/security_02_high-risk-tool-common-policy.md`

## Goal

Remove the "current coverage is uneven ... tracked as Known Issue MCP-006" language now
that coverage is resolved (`REQ-007`).

## Scope

Modify only `docs/91_security/security_02_high-risk-tool-common-policy.md`. Replace the
uneven-coverage paragraph (line 56) with language reflecting that each tool's current
coverage is documented in its own tool doc, and that MCP-006 is resolved.

## Assumptions

- Line 56 states the uneven-coverage gap and references MCP-006.
- This edit is done in Phase 6, after every category is implemented-or-not-applicable.

## Design decisions

- Replace the gap sentence with a pointer to each tool's own document for current coverage
  (which is what the plan already instructs readers to do), dropping the "not implemented
  for others / tracked as MCP-006" clause.
- Keep the rest of the policy (layer definitions, allowed paths) unchanged.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`docs/91_security/security_02_high-risk-tool-common-policy.md`

### Procedure

1. Locate the uneven-coverage paragraph (line 56).
2. Rewrite it to state coverage is now documented per tool and MCP-006 is closed; remove
   the "tracked as Known Issue MCP-006" reference.
3. Verify no other sentence depends on the open-gap framing.

### Method

- Edit line 56's paragraph in place.

### Details

- Do not alter the five-layer definition table; only the coverage-status prose.

## Compatibility considerations

This policy is referenced by other docs; ensure the removed MCP-006 reference is not
cited elsewhere as an open item (coordinate with row 18).

## Security considerations

N/A.

## Rollback considerations

Revert the commit to the doc.

## Validation plan

- Documentation-consistency check (`governance_04_documentation-checks.md`, GV-022 family)
  passes; confirm no dangling MCP-006 open-reference remains in security docs.

## Completion criteria

`security_02` no longer describes an open coverage gap and no longer references MCP-006 as
open.

## Out of scope

Other docs, code changes, the governance ledger (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove uneven-coverage/MCP-006 language from security_02 | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A (docs-only) | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | — | — | this doc |

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
- **Requirement ID**: `REQ-007` (policy no longer describes an open gap)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `docs/91_security/security_02_high-risk-tool-common-policy.md`
