## Goal

Record the rules-authoritative posture (DT-01 Option A) in the validator module and verify the
existing floor guard covers it (REQ-004, REQ-012) — no new guard is added.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_check_approval_risk_floor()` (`scripts/agent/production_config_validator.py:88`) already rejects
  git write tools resolving below `HIGH`; Option A explicitly declined to add a tier/rule-redundancy
  guard, so this row changes no validation logic.

## Design decisions
- Comment-only clarification naming where config-level policy is enforced; future guards (if ever
  decided) belong here rather than in `classify_risk()` — recorded as a design note, not an action.

## Alternatives considered
DT-01 Option B (new guard rejecting unreachable tier entries) — rejected by the maintainer decision.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
Add a short comment block adjacent to `_check_approval_risk_floor()` (`:88`) stating: rules are
authoritative for approval risk; tier entries for rule-eligible tools are intentional
defense-in-depth for plan-mode blocking and the tier-vs-write classification; no redundancy guard
exists by decision.
### Method
Comment only; no function or error-path changes.
### Details
N/A: the guard's behavior is unchanged and already characterized by the companion tests.

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: add a characterization test asserting a rule overrides its tool's tier (e.g. a
    `medium`-ruled tool keeps `MEDIUM` despite a `WRITE_DANGEROUS` tier); existing
    `TestProductionConfigValidatorApprovalRiskFloor` (`:114-204`) cases stay unchanged.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -q`.

## Compatibility considerations
No new startup failure mode — the key property of the approved posture.

## Security considerations
The floor guard must keep rejecting sub-`HIGH` git write tools; the comment must not soften that.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py -q`
- Verification correction 2026-11-19: `tools/check_production_config_validator.py` does not exist;
  production-config validity is covered by this same test module and the integration suite
  (`tests/integration/test_production_security_regression.py`).

## Completion criteria
Comment present adjacent to the floor guard; the companion characterization test passes; every
pre-existing validator test passes unchanged.

## Out of Scope
Any new validation rule or error code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the posture comment per Procedure | Completed | 20261119-073858 | 20261119-073858 | Comment block above `_check_approval_risk_floor()` (:88 verified); floor guard logic untouched |
| 2 | Add the characterization test in the companion file | Completed | 20261119-073858 | 20261119-073858 | `test_rule_takes_precedence_over_tier` added to `TestProductionConfigValidatorApprovalRiskFloor`; procedure's "medium rule keeps MEDIUM" example re-scoped to the guard's distinguishing case (high rule + sub-HIGH tier passes) since medium/`WRITE_DANGEROUS` both resolve to MEDIUM |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-073858 | 20261119-073858 | ruff/mypy pass; 45 tests pass (all pre-existing cases unchanged + 1 new) |

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
- **Requirement ID**: `REQ-004` (DT-01 decision: no guard), `REQ-012` (existing guard verified in the full gate run)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`
