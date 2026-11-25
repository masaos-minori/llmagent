## Goal

Extend the removed-key rejection to the reload path, so a removed or moved configuration key is rejected
by both paths rather than only by startup (REQ-002, reload candidate through the startup parser;
REQ-010, registry completeness).

## Scope
**Release unit**: R3-shared-candidate

## Assumptions
- Verified against current source: this file covers the startup path only today — every case calls
  `build_agent_config(merged)` and none calls the reload service. Its `REMOVED_KEYS` frozenset
  (`tests/agent/test_removed_config_keys_rejected.py:29`) is `use_semantic_cache`,
  `semantic_cache_threshold`, `semantic_cache_max_size`.
- Verified against current source: the keys the Plan names as removed-or-moved reload-payload keys,
  `tool_safety_tiers` and `approval_risk_rules`, are declared in
  `ProductionConfigValidator` (`scripts/agent/production_config_validator.py:68-69`) and are covered on the
  startup side by `tests/integration/test_production_security_regression.py:45` and
  `tests/integration/test_standard_config_integration.py:273`, not by this file. The reload-path cases
  here cover both sets.
- The reload path rejects the key because the candidate is built through `build_agent_config(cfg_override=...)`
  (row 13), which runs `_check_unknown_production_keys`; no new check is added here.

## Design decisions
- The same key list is run through both paths, so the file shows the two paths agree rather than asserting
  two separate behaviors.

## Alternatives considered
- Adding a reload-specific key check in the reload service — rejected: that would be a second source of the
  key set (OD-01 option a).

## Implementation
### Target file
`tests/agent/test_removed_config_keys_rejected.py`

### Procedure
Add the reload-path cases to this startup-only file, per the Plan's Phase 3 step 1, so each removed or
moved key is rejected by both paths.

### Method
- Add the reload-path cases for every key in this file's `REMOVED_KEYS` set and for
  `tool_safety_tiers` and `approval_risk_rules` from the production validator's removed-key list.
- Assert the rejection happens before any live change, which is the candidate-phase contract.

### Details
- The assertion is the rejection itself, not the message wording, so the message shape is covered by row 38.

## Compatibility considerations
- Blast radius: this file is the AC-6 pin; it does not change production behavior.

## Security considerations
- N/A: the tests assert accept and reject results, not output.

## Rollback considerations
- Revert the Phase 3 commit.

## Validation plan
- `uv run pytest tests/agent/test_removed_config_keys_rejected.py -q`

## Completion criteria
- Every removed or moved key has a case on both paths, and the reload case shows no live mutation occurred.

## Out of Scope
- The candidate build itself (rows 6, 13).
- The CLI error reporting (row 38).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-184431 | 20261125-184431 | Reload-path cases added for REMOVED_KEYS plus tool_safety_tiers and approval_risk_rules; asserts nothing live mutates |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-184431 | 20261125-184431 | 11 passed; R3 unit gate clean |

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
- **Requirement ID**: REQ-002 (reload candidate through the startup parser), REQ-010 (registry completeness); AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/test_removed_config_keys_rejected.py`