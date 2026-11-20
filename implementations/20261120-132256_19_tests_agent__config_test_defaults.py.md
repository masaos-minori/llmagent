## Goal

Reconcile the comment in `_config_test_defaults.py` that documents the old unconditional empty-list rejection, so it reflects the mode-aware contract (`plan` maintenance row).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lines 86-89 currently state that an empty `allowed_tools` disables every tool at runtime and that `ProductionConfigValidator` rejects `allowed_tools=[]`; both are absolute claims the Plan removes.
- The `ALL_TOOL_NAMES` value itself is correct and unchanged.

## Design decisions
- Rewrite lines 86-89 to state that an empty `allowed_tools` disables every tool only in `explicit_allowlist` mode and is valid in `discovered` mode, and that `ProductionConfigValidator` no longer rejects an empty list unconditionally.

## Alternatives considered
- Deleting the comment: rejected because it explains why `ALL_TOOL_NAMES` covers every registered tool.

## Implementation
### Target file
`tests/agent/_config_test_defaults.py`

### Procedure
Rewrite the comment block at lines 86-89 to remove the two absolute claims.

### Method
Replace the two sentences with mode-aware wording; leave `ALL_TOOL_NAMES` untouched.

### Details
- Replace "an empty allowed_tools now disables every tool at runtime (RuntimeToolRegistry.apply_policy) and ProductionConfigValidator rejects allowed_tools=[]" with wording stating emptiness is mode-dependent (valid in `discovered`, denying in `explicit_allowlist`).

## Compatibility considerations
Comment-only; no behavior change.

## Security considerations
No security impact: documentation of test-helper semantics only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
The comment no longer states the removed absolute claims; the file still defines `ALL_TOOL_NAMES`.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`) and production validation (`production_config_validator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `tests/agent/_config_test_defaults.py`
