## Goal

Update the `GV-017` matrix row (L333) and its implementation note (L352) in
`docs/00_governance/governance_04_documentation-checks.md` to reflect the four new
removed-name patterns added to `GV-017` (`REQ-007`, command-surface reduction).

## Scope

In scope: update the `GV-017` matrix row (L333) and implementation note (L352) in
`docs/00_governance/governance_04_documentation-checks.md`. Out of scope: adding the
patterns themselves (`tools/check_compat_shims.py`, `REQ-005`, separate document), the
command/handler/mixin deletions (`REQ-001`–`REQ-004`), and the other docs changes
(`REQ-007`, separate documents).

## Assumptions

- The `GV-017` matrix row and implementation note describe the removed-name pattern guard;
  they should be updated to record the four new patterns.

## Design decisions

- **Update the two references only.** Keep the surrounding governance structure intact;
  do not restructure the document.

## Alternatives considered

`N/A`: the goal requires documenting the extended guard; leaving the doc stale would drift
from the code it describes.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the `GV-017` matrix row (L333) and implementation note (L352) with `rg`.
2. Update the matrix row to record the four new removed-name patterns
   (`/diff`, `/system`, `/audit`, `/workflow`).
3. Update the implementation note (L352) to match.

### Method

Edit the two locations as whole lines/blocks, preserving document structure.

### Details

- Align the doc wording with the pattern keys added in `tools/check_compat_shims.py`
  (separate document) so docs and code agree.

## Compatibility considerations

Docs-only change; production behavior is unaffected.

## Security considerations

`N/A`: documentation change; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- Run the governance/docs checker named in `routing.md` — clean.

## Completion criteria

The `GV-017` matrix row and implementation note record the four new removed-name patterns,
and the rest of the document is unchanged.

## Out of scope

`tools/check_compat_shims.py` (`REQ-005`), `command_defs_list.py` (`REQ-001`),
`cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py` (`REQ-003`),
`conversation_service.py` (`REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `GV-017` matrix row (L333) and implementation note (L352) in `docs/00_governance/governance_04_documentation-checks.md` (`REQ-007`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 3 | Run the docs checkers named in `routing.md` | Completed | 20261017-100006 | 20261017-100006 |  |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`