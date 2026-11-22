## Goal

Give the Agent side its own approval-grant horizon field so grant lifetime stops being a module constant (REQ-002).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Field name/range per seq 05: `approval_grant_ttl_seconds` (new) — float, default 300.0, accepted range 60..3600 — confirmed against current source (no existing key mirrors it); the name propagates to seqs 06, 07, 08, 12, 38 in the same step.

## Design decisions
- Add `approval_grant_ttl_seconds` (new) with type `float` and default `300.0` on `AgentConfig` beside `pending_timeout_minutes` (line 378); the default equals the current `tool_approval._GRANT_TTL_SECONDS` (300.0) so behavior is identical until configured otherwise.

## Alternatives considered
- Reusing `pending_timeout_minutes` for the grant horizon: rejected — different lifecycles (stale-pending recovery vs grant expiry), the plan separates them (REQ-002).

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
1. Add the field `approval_grant_ttl_seconds: float = 300.0` (new) to `AgentConfig` with a one-line comment naming its consumer (`tool_approval._issue_grant`).
### Method
Single dataclass field; `dataclass_fields()`-based consumers (validator, seq 07) pick it up automatically.
### Details
- No rename of existing fields; `pending_timeout_minutes` stays the only stale-pending timeout (REQ-002).

### Companion test files
- `tests/agent/test_config_dataclasses.py`
  - Procedure: assert the new field's presence, default `300.0`, and that `dataclass_fields(AgentConfig)` includes it.
  - Validation: `uv run pytest tests/agent/test_config_dataclasses.py -q`.

## Compatibility considerations
- Adding a defaulted field is backward compatible for every existing `AgentConfig(...)` construction site.

## Security considerations
- Grant lifetime shortening/lengthening becomes configuration; range enforcement lives in seq 07 (validator), not the dataclass.

## Rollback considerations
- N/A: revert the commit (single field addition).

## Validation plan
- `uv run pytest tests/agent/test_config_dataclasses.py tests/agent/test_config_builders.py -q`; `uv run mypy scripts/agent/config_dataclasses.py`.

## Completion criteria
- `AgentConfig.approval_grant_ttl_seconds` exists with default 300.0 and is covered by the companion test.

## Out of Scope
- Builder read (seq 06), validator range (seq 07), `_issue_grant` consumption (seq 08), `agent.toml` entry (seq 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the new `AgentConfig` field | Pending | — | — | |
| 2 | Add or update companion tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_dataclasses.py`
