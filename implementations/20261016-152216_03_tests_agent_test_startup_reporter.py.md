## Goal

Add a regression test asserting that a pipeline whose RAG consistency check is SKIPPED renders the skipped indicator in the reported readiness line, and that a non-skipped RAG check is unaffected (`REQ-004`).

## Scope

One new test function in `tests/agent/test_startup_reporter.py`. No changes to existing tests.

## Assumptions

- Tests build a fake pipeline whose `rag_consistency` outcome status is `SKIPPED` and drive `ReadinessReporter.report_readiness()`, then inspect the single `write_warning` message.
- The existing helpers (`_empty_pipeline()`, the `MagicMock` ctx/view setup in `test_report_readiness_emits_readiness_summary`) can be reused to populate `pipeline.outcomes`.

## Design decisions

- Build a fake pipeline whose `outcomes` include a `rag_consistency` outcome with `.status == StartupCheckStatus.SKIPPED`, assert the rendered line contains `, N skipped`, and add a case with a non-SKIPPED RAG outcome asserting no spurious skipped count.

## Alternatives considered

- Assert on `display_pipeline_results` instead: rejected — the skipped-count column lives in `report_readiness()`, which is what the Plan changes. `N/A: exercise report_readiness()`.

## Implementation
### Target file
`tests/agent/test_startup_reporter.py`

### Procedure
Append a new test that drives `report_readiness()` with a SKIPPED RAG outcome and asserts the skipped indicator appears; add one asserting a non-skipped RAG check is unaffected.

### Method
1. Import `StartupCheckStatus` from `agent.shared.health_models`.
2. Build a small fake pipeline: a `pipeline.outcomes` list of objects each with a `.source` string and a `.status` enum value, where one outcome has `source == "rag_consistency"` and `.status == StartupCheckStatus.SKIPPED`.
3. Drive `report_readiness(fake_pipeline)` with a `MagicMock` view, capture the single `write_warning` message, and assert it contains the RAG line with `, 1 skipped` (the skipped indicator is present, not a bare "WARN" with zero counts).
4. Add a second case with a non-SKIPPED RAG outcome and assert the RAG line still renders correctly and gains no spurious skipped count.

### Details
- `report_readiness()` aggregates by calling `_count_by_status(pipeline, "rag_consistency")`, so each fake outcome needs `.source` (str) and `.status.name` matching the real `StartupCheckStatus` enum names (`"OK"`, `"SKIPPED"`, ...). Assign `.status = StartupCheckStatus.SKIPPED` so `.status.name == "SKIPPED"`.
- Reuse the `ctx`/`view` setup shape from `test_report_readiness_emits_readiness_summary`, but populate `pipeline.outcomes` with the fake outcomes above instead of leaving them empty.
- Assert on the rendered string (the source of truth for AC-001), not on internal counts.

## Compatibility considerations
Purely additive test; no existing test or production signature changes.

## Security considerations
`N/A: test-only addition`.

## Rollback considerations
`N/A: revert the commit`.

## Validation plan
- `pytest tests/agent/test_startup_reporter.py` — new assertions pass; existing `test_report_readiness_emits_readiness_summary` and `test_report_readiness_propagates_when_services_uninitialized` still pass.

## Completion criteria
The new test asserts the SKIPPED RAG line contains the skipped indicator and a non-skipped RAG line is unaffected, and the whole `test_startup_reporter.py` suite passes.

## Out of scope
Changing production reporter behavior; altering existing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261016-134010_startup002_clarify-startup-status-reporting-for-skipped-checks-and-shutdown-during-startup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-141320_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-152216
- **Related target files**: `tests/agent/test_startup_reporter.py`
