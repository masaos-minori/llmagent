## Goal

Follow the `check_workflow_schema` change in the workflow preflight behavior-lock tests
(`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/agent/services/workflow_schema.py` now validates via the generalized
  fingerprint instead of `REQUIRED_WORKFLOW_TABLES` + marker-table refusal (its row).
- `check_workflow_schema` keeps its signature (Reference Files: the caller
  `scripts/agent/startup_component_init.py` relies on it), so the test's name-based
  patches remain valid.

## Design decisions
- Keep the `patch()` calls that stub `check_workflow_schema`; the test only asserts the
  preflight aborts when the schema check raises, which is unchanged.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/agent/test_startup_workflow_preflight.py`

### Procedure
1. Keep the name-based patches of `agent.startup_component_init.check_workflow_schema`
   at lines 47, 56, 64; the signature is unchanged.
2. Update the module docstring at line 3 if desired to note the check now fingerprints;
   the "raises RuntimeError on schema failures" statement stays accurate.
3. No assertion changes: the preflight still aborts on any raised error.

### Method
- Confirm the patch targets with
  `rg -n 'check_workflow_schema|patch|_check_workflow_schema' tests/agent/test_startup_workflow_preflight.py`
  before editing.

### Details
- The valid-schema pass case at line 58-67 stays; the fingerprint path raises only on
  drift, which the passing fixture does not trigger.

## Compatibility considerations
The `patch` import and `ComponentInitializer` usage stay.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_startup_workflow_preflight.py -v` passes.

## Completion criteria
The preflight patches remain valid against the fingerprint-backed `check_workflow_schema`;
all cases pass.

## Out of Scope
Changing `check_workflow_schema` itself (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Follow the check_workflow_schema change | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` — follow the check_workflow_schema change
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/agent/test_startup_workflow_preflight.py`
