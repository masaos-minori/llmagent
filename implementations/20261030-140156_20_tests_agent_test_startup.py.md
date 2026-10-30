# Implementation Procedure: `tests/agent/test_startup.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-006, REQ-007)

## Goal
Startup behavior per severity: fatal aborts, degraded warns with the repair action named,
timeout/failure marks identity-unverified without aborting.

## Scope
- Harness: `_make_startup_ctx` `:145`, `_run_check_services` `:158`; severity precedent
  class `TestCheckServicesSeverityClassification` `:232` (fatal/warning patterns for
  other subsystems to mirror).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- `TestRagConsistencySeverityStartup` (new class), mirroring the `:232` patterns with a
  stubbed `RagMaintenanceService.consistency` result:
  - `test_fatal_finding_aborts_startup` (new): findings containing one FATAL →
    `pipeline.add_fatal("rag_consistency", ...)` recorded, message names the repair
    action.
  - `test_degraded_findings_warn_with_repair_action` (new): DEGRADED-only → warnings,
    each message contains its `repair_action` verb.
  - `test_timeout_marks_unverified_not_fatal` (new): `TimeoutError` from consistency →
    warning text contains `identity-unverified`, startup continues, no `add_skipped`
    (doc 07 removed that path).
  - `test_unexpected_exception_marks_unverified` (new): exception path → same
    unverified warning, category from `_classify_rag_failure` retained in the message.
  - `test_consistent_ok` (new): unchanged `add_ok` path.

1. Append the class; stub the service via monkeypatch using the existing `:158` harness
   pattern. No product code assumptions beyond docs 05-07 contracts.

## Compatibility considerations
**Dependencies**: upstream: docs 05, 06, 07
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/agent/test_startup.py`

## Completion criteria
- REQ-006/REQ-007 startup contract locked; existing 855-line suite green.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_05_scripts_db_models.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `TestRagConsistencySeverityStartup`,
  `test_fatal_finding_aborts_startup`, `test_degraded_findings_warn_with_repair_action`,
  `test_timeout_marks_unverified_not_fatal`,
  `test_unexpected_exception_marks_unverified`, `test_consistent_ok` (Test cases
  section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 20
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/agent/test_startup.py`
