## Goal

Align the shared approval-test fixture constants with the approved posture so every approval suite
builds configs from the same source of truth (REQ-003, REQ-012).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `tests/agent/_config_test_defaults.py` exports `PERMISSIVE_ALLOWED_ROOT` (`:18`),
  `ALL_APPROVAL_RISK_RULES` (`:42`), `ALL_TOOL_SAFETY_TIERS` (`:74`), consumed by
  `tests/agent/test_tool_approval_paths.py:18-22` and the other approval suites.
- DT-01/DT-03 Option A change no shipped key, so the constants must keep mirroring
  `config/agent.toml` (`approval_risk_rules` 19 entries, `tool_safety_tiers` 64 entries) rather than
  encode a hypothetical posture.

## Design decisions
- Keep the constants a mirror of the shipped config, and state that mirror relationship in the module
  docstring so a config edit surfaces as a fixture drift, not a silent test divergence.
- No new guard-related constants: Option A adds no validator guard.

## Alternatives considered
Freezing a synthetic posture in the fixtures — rejected; the characterization tests must pin the
shipped posture (AC-003).

## Implementation
### Target file
`tests/agent/_config_test_defaults.py`
### Procedure
1. Verify `ALL_APPROVAL_RISK_RULES` and `ALL_TOOL_SAFETY_TIERS` match
   `config/agent.toml:252-271` and `:287-351` entry-for-entry and add any missing entry.
2. Record in the module docstring that these constants mirror the shipped config, and that a rule and a
   tier may both exist for one tool by design (rules are authoritative for risk; tiers drive plan-mode
   blocking).
### Method
Constant verification plus a docstring note; no helper or signature changes.
### Details
N/A: nothing beyond the mirror relationship is not inferable from REQ-003/REQ-012.

## Compatibility considerations
Any added entry must keep the existing approval suites green; a mismatch would surface in rows 11/12/14/15.

## Security considerations
N/A: test fixture alignment.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_paths.py tests/agent/test_tool_approval_risk.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_production_config_validator.py -q`

## Completion criteria
The exported constants equal the shipped config's rules and tiers, and the approval suites pass
unchanged (AC-012).

## Out of Scope
`config/agent.toml` (row 08), the approval suites' own new tests (rows 11/12/14/15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align and document the fixture constants per Procedure | Pending | — | — | Phase 3 |
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
- **Requirement ID**: `REQ-003` (characterization fixtures), `REQ-012` (no pre-existing test regressed)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/_config_test_defaults.py`
