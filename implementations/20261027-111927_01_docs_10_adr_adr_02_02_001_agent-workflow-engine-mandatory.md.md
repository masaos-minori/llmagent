## Goal

Fill or honestly mark every empty Implementation cell of the ADR-001 `### Automated Tests` table, citing only test node IDs verified to exist (`REQ-001`: INV-01, INV-03, INV-05, INV-06 cited, INV-02 not verified; `REQ-004`: no Invariant, Decision, Gate or Approval text changed).

## Scope

- Edit the Implementation cells of the INV-01, INV-02, INV-03, INV-05 and INV-06 rows of the table under `## Verification` / `### Automated Tests`.
- Do not edit any other row, the Blocking column, or any Invariant, Decision, Gate or Approval text.

## Assumptions

- Order: this row follows `plans/20261027-104411_govrev003_partial-verification-gate-rules.md`, whose vocabulary (`Confirmed`, `Partial`, `Manual`, `Not verified`) is implemented first. If that vocabulary is not yet in `docs/10_adr/adr_01_index.md`, stop and report `Blocked` (UNK-04).
- Step 3a corrected the Plan: `test_aborts_on_invalid_workflow_schema` verifies INV-06 (startup abort on an invalid DB schema), not INV-05. All cited node IDs were collected and the cited tests passed in Step 3a (53 passed).
- Evidence per row: INV-01 `tests/agent/test_startup_workflow_preflight.py::TestComponentInitializerWorkflowPreflight::test_aborts_on_missing_workflow_definition` and `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal` (identical to the index row); INV-03 `tests/agent/workflow/test_workflow_engine.py::TestRunStageWithRetryGeneralization::test_execute_success_verify_failure_marks_task_failed`; INV-05 `tests/agent/test_startup_workflow_preflight.py::TestComponentInitializerWorkflowPreflight::test_aborts_on_invalid_workflow_json` and `tests/agent/test_repl_health.py::TestCheckWorkflowDefinition`; INV-06 `tests/agent/test_startup_workflow_preflight.py::TestComponentInitializerWorkflowPreflight::test_aborts_on_invalid_workflow_schema` and `tests/agent/test_repl_health.py::TestCheckWorkflowSchema`.
- INV-02 (no external state-change path bypasses the Workflow Engine): no test found (`rg` over `tests/` in Step 3a). Its Blocking column stays `Yes`; whether a Blocking invariant may stay Blocking while recorded as `Not verified` is UNK-02 (non-blocking), to be decided with the repository owner under the govrev003 vocabulary. Record this as `Needs confirmation` in the progress report.
- Size gate: the file is 19141 B against the 24576 B default limit with no per-file exception (headroom 5435 B), so the edit fits.
- Overlap with `plans/20261027-104127_govrev002_adr-001-diff-command.md` (same file, Negative Consequences sentence): compatible, no required order. Overlap with `plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md`: none.

## Design decisions

- Cite full node IDs (file::class::test); a class-level ID is acceptable where the index already cites the class.
- Write `Not verified` for INV-02 with a short reason; invent no citation.

## Alternatives considered

N/A: the Plan (Design section) already decided that an invariant with no verifying test is recorded as not verified, never given an invented citation.

## Implementation
### Target file

`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure

1. Phase 1 re-check (read-only): collect the node IDs listed in Assumptions (`uv run pytest --collect-only -q <ids>`), run them, and `rg` once more for a test of INV-02. If a node ID no longer exists, stop and report `Plan Gap`.
2. In the `### Automated Tests` table, replace the `-` in the Implementation column of the INV-01, INV-03, INV-05 and INV-06 rows with the node IDs from Assumptions, each in backticks and separated by `, `.
3. For the INV-02 row, replace `-` with `Not verified (no automated test asserts that no external state-change path bypasses the Workflow Engine)`.

### Method

Exact-string row edits. The INV-03 row's Test column already names `test_execute_success_verify_failure_marks_task_failed`; leave it.

### Details

- Do not touch the INV-07, INV-08, INV-10 and INV-11 rows.
- Backticked node IDs are read by `check_adr_invariant_matrix.py` only for the index, but keep the same form as the existing ADR-001 cells.

## Compatibility considerations

N/A: documentation only. `check_adr_preservation.py` may report test-citation changes; review each as intended and stop if an Invariant, Decision or Approval text appears in the report.

## Security considerations

N/A: no secret or credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest <cited node IDs> -q` (all exist and pass).
- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` (review every report).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.

## Completion criteria

- No ADR-001 invariant row has an empty Implementation cell without an explicit status, and each cited node ID exists and passes.
- No Invariant, Decision, Gate or Approval text changed; the checkers report no finding other than reviewed, intended preservation reports.

## Out of Scope

- New tests for INV-02.
- The `diff command` sentence (`plans/20261027-104127_govrev002_adr-001-diff-command.md`).
- The ADR-002 table and the index (rows 02 and 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-check the cited node IDs and the INV-02 search (read-only) | Pending | — | — | |
| 2 | Fill or mark the five Implementation cells | Pending | — | — | |
| 3 | Run the checkers named in the Validation plan | Pending | — | — | Review `check_adr_preservation.py` reports |

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
- **Requirement ID**: `REQ-001` (cite or mark the ADR-001 Implementation cells), `REQ-004` (no other ADR text changed)
- **Source issue**: issues/20261027-101918_govrev004_adr-verification-evidence-sync.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104705_govrev004_adr-verification-evidence-sync.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111927
- **Related target files**: docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md
