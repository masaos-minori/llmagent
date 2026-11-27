# Implementation Procedure — scripts/mcp_servers/cicd/cicd_models.py

## Goal

Make `cicd_models.py` the single strict request-model source: adopt the shared strict base with `extra="forbid"`, keep the CI/CD numeric and non-empty constraints, add the canonical workflow-identifier function, the hard maximum constants, and the shared `owner/repo` normalization for allowlist entries.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-004 (schemas generated from strict models), REQ-005 (canonical workflow identifier), REQ-006 (allowlist normalization and hard maximum size), REQ-007 (`max_log_size_kb` bounds via shared strict numeric parsing). Acceptance criteria: AC-3, AC-5.

## Assumptions
- The hard maximums (`max_log_size_kb` 1..1024, allowlist size 1..100) are Plan decisions approved by the user on 20261126 (UNK-03); no repository convention exists, so they are recorded as module constants here.
- `scripts/mcp_servers/request_contract.py` (`StrictRequestModel` at line 34, `build_input_schema()` at line 44) and `scripts/shared/repo_identity.py` (`normalize_repo_key()` at line 21, `is_canonical_repo_key()` at line 34) are read-only references; this document does not modify them.

## Design decisions
- Request models inherit `StrictRequestModel` instead of carrying their own `model_config`, so the published schema and the runtime contract come from one source.
- The canonical workflow-identifier function lives in this module because both the request path (`cicd_service_business.py`) and the allowlist comparison (`cicd_service_guards.py`) call the same function (Plan D5).
- Hard maximums are module constants, not configuration values, so the config row can state them and the docs cross-check can compare against them.

## Alternatives considered
- Enforce the bounds in `from_dict()` only: rejected — REQ-004 requires the model itself to carry the constraints so the published schema matches the enforced contract.
- Define a cicd-local normalization instead of reusing `repo_identity.py`: rejected per REQ-006, which names the shared normalization policy as the policy to reuse.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_models.py`

### Procedure
- Make every request model inherit `StrictRequestModel` from `scripts/mcp_servers/request_contract.py` (`extra="forbid"`).
- Keep `run_id >= 1` and `limit` 1..50; add non-empty constraints for `repo`, `workflow`, `ref`.
- Add the constants `MAX_LOG_SIZE_KB` (new) = 1024 and `MAX_ALLOWLIST_SIZE` (new) = 100.
- Add `canonical_workflow_id(value: str) -> str` (new): accept a validated file name or a positive numeric id and return the canonical form; reject separators, percent-encoding, blank, and wildcard values.
- In `CicdConfig.from_dict()`, validate allowlist entries through `normalize_repo_key()` / `is_canonical_repo_key()` from `scripts/shared/repo_identity.py`, reject wildcard and oversized entries, and parse `max_log_size_kb` through `get_non_negative_number()` from `scripts/shared/config_utils.py` with the lower bound 1 and the hard maximum.

### Method
- The request models at lines 88-137 currently have no `model_config` and no shared strict base; change the base class only, keep field names and descriptions so the pinned schema-shape tests can be re-pinned by the sibling test row.
- `from_dict()` already uses `get_typed()` for lists (which raises `ValueError` for a non-integer, verified at `scripts/shared/config_utils.py:56`); switch the `max_log_size_kb` branch to `get_non_negative_number()` and add the upper bound.

### Details
- Newly rejected inputs (recorded in the Plan's change record): extra request fields, blank `repo`/`workflow`/`ref`, `limit` outside 1..50, `run_id` below 1, wildcard allowlist entries, allowlist entries above the hard maximum, `max_log_size_kb` below 1 or above 1024.
- `CicdConfig` has the widest blast radius in the area (11 direct consumers, 25 test references); run the `rules/toolchain.md` impact-radius check before changing its validation.

## Compatibility considerations
- Values that are already canonical are unchanged; values that differ only by case or leading separators are now normalized or rejected (Plan D5).
- Deny-all behavior for an empty allowlist stays unchanged.

## Security considerations
- Stricter validation is the intent (REQ-009): malformed configuration fails before bind through the existing posture gate.

## Rollback considerations
- N/A: revert the commit; the phase is covered by its own tests.

## Validation plan
- Unit: model validation and schema shape — `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` (re-pinned by the sibling row).
- Full sequence per `rules/toolchain.md`, including the import-linter contract that keeps this module inside `mcp_servers`.

## Completion criteria
- `extra="forbid"` and the CI/CD constraints are enforced by the models (AC-3); the hard maximums and normalization reject the listed inputs before bind (AC-5); the canonical function is the only identifier normalizer used by request and allowlist paths (AC-4).

## Out of Scope
- Publishing the schemas from the models (`cicd_tools.py` row); guard matching at call time (`cicd_service_guards.py` and `cicd_service_business.py` rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006, REQ-007 (strict models, canonical identifier, allowlist normalization and maximums, `max_log_size_kb` bounds)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`
