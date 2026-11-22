## Goal

Extend production key validation so the new Agent-side horizon key is accepted and range-checked, closing REQ-006's production posture for the ownership move.

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Verified 2026-11-22: the validator never reads `*_mcp_server.toml` or `mcp_dedup.toml` (only an explanatory comment), so the row's "per-server `[dedup]` tables" clause is satisfied by `load_dedup_section()` at injection (seqs 01/04) — no additional file is needed here, and no additional-target-file discovery applies.

## Design decisions
- The valid-keys set is derived from `dataclass_fields(AgentConfig)` (lines 155-167), so seq 05's field automatically whitelists the key; the change here is the range check: flag `approval_grant_ttl_seconds` outside `60..3600` (UNK-02 range) through the existing `_record(errors, ...)` pattern.

## Alternatives considered
- A hand-maintained key table entry: rejected — the dataclass-derived set is the existing mechanism (line 173 site).

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
1. Add a numeric-range check for `approval_grant_ttl_seconds` (sibling seq 05) in `validate()` beside the existing not-false/risk-floor checks, error text naming the key and accepted range.
### Method
Follow `_check_approval_risk_floor`-style helper or an inline `_record` branch, consistent with neighbors.
### Details
- Module is 14,043 B: ample headroom.

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: accept-case for `approval_grant_ttl_seconds = 300.0`; reject-cases for `59` and `3601`; keep the existing unknown-key tests passing with the field-derived whitelist.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -q`.

## Compatibility considerations
- Existing production configs without the key: no error (default path), so behavior-lock holds.

## Security considerations
- Range floor 60s prevents a degenerate near-zero grant horizon in production posture.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py tests/shared/test_config_validator.py -q`; `uv run mypy scripts/agent/production_config_validator.py`.

## Completion criteria
- Out-of-range values produce a validator error naming key and range; in-range and absent values validate clean.

## Out of Scope
- Per-server `[dedup]` validation (implemented at injection, seqs 01/04; verified out of this validator's file scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the range check | Pending | — | — | |
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
- **Requirement ID**: REQ-006; AC-006
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`
