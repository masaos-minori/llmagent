## Goal

Read the new Agent-side grant-horizon key when building `AgentConfig` (REQ-002).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Field name/range per seq 05 (`approval_grant_ttl_seconds`, default 300.0); sibling declares it.

## Design decisions
- Follow the existing pattern beside `pending_timeout_minutes` (lines 145-146): `_get_or_default(cfg, "approval_grant_ttl_seconds", _get_float, 300.0)` (float getter; add `_get_float` only if the module lacks one).

## Alternatives considered
- Validating the range in the builder: rejected — the plan assigns range enforcement to `ProductionConfigValidator` (seq 07); the builder stays lenient like its siblings.

## Implementation
### Target file
`scripts/agent/config_builders.py`
### Procedure
1. In the `AgentConfig` builder, add the read of `approval_grant_ttl_seconds` (sibling seq 05) beside the `pending_timeout_minutes` read.
### Method
One additional `_get_or_default(...)` argument line.
### Details
- Builder is 5,640 B: no size concern.

## Compatibility considerations
- Absent key → default 300.0, identical to today's constant.

## Security considerations
- N/A: value range is enforced by the validator (seq 07), not here.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q` (row 38's document covers the test edit); `uv run mypy scripts/agent/config_builders.py`.

## Completion criteria
- A config file carrying `approval_grant_ttl_seconds = 900` produces `AgentConfig.approval_grant_ttl_seconds == 900.0`; absence produces 300.0.

## Out of Scope
- Validator range checks (seq 07); grant usage (seq 08); test file itself (row 38).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the builder read | Completed | 2026-11-22 | 2026-11-22—builder read + _get_float import added|
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—builder read + _get_float import added|

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
- **Requirement ID**: REQ-002; AC-005
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/agent/config_builders.py`
