## Goal
Define FATAL in `mcp_06_09` as startup being aborted, identical to `agent_10_01` (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Current text: `A critical issue that prevents normal operation. The system may be partially functional.` The same document says FATAL findings block startup, and `agent_10_01` defines FATAL as `Condition preventing startup ... aborting startup` (checked).

## Design decisions
- Align wording with `agent_10_01`: FATAL is a condition that prevents startup; startup is aborted after the checks of the failing stage complete.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`

### Procedure
1. Replace the first FATAL sentence with `A condition that prevents startup: startup is aborted after the checks of the failing stage complete.`
2. Keep the `write_fatal()` and example lines.

### Method
- `rg -n 'partially functional' docs/` afterwards must not match this document.

### Details
- Cite ADR-004 for the policy rather than restating it.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- `mcp_06_09` and `agent_10_01` define FATAL identically.

## Out of Scope
- `agent_10_01` (no change needed); WARNING definition.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` — FATAL defined as startup aborted
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`
