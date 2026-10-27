## Goal
- Make the ADR body Verification section the canonical record of verification evidence for ADR-001 and ADR-002, fill or honestly mark every empty Implementation cell, make the ADR-002 Completion Checklist state the true verification status, and state the canonical-source rule in the ADR index so that the ADR bodies, their checklists and the index agree.

## Priority
Medium

## Scope
- **In-Scope**:
  - ADR-001: fill the Implementation cells of INV-01, INV-03 and INV-05 with existing test node IDs, decide INV-06 from the closest existing tests, and record INV-02 as not verified.
  - ADR-002: record INV-03 and INV-04 as not verified, using the vocabulary defined by the dependency plan, and make the Verification-related Completion Checklist items state the true status.
  - Index: state that the ADR body Verification section is canonical, and make the ADR-001 INV-01 evidence identical in the body and the index.
- **Out-of-Scope**:
  - Writing new tests for the unverified invariants.
  - Changing any ADR Decision, Invariant, Gate or Approval record.
  - Defining the Verification Status vocabulary (the dependency plan).
  - Extending `check_adr_invariant_matrix.py` to read ADR bodies (a separate plan of the same batch).
  - The "diff command" sentence of ADR-001 (a separate plan of the same batch).
  - ADRs other than ADR-001 and ADR-002.
- **Dependencies**: `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` (the issue's dependency, `depends on`): that Plan defines the Verification Status vocabulary and Gate effects used here and edits the same index file, so it is implemented first. `plans/20261027-104127_govrev002_adr-001-diff-command.md` edits a different sentence of ADR-001 and is compatible.

## Background
- ADR-002: the Automated Tests rows for INV-03 and INV-04 list Type `Integration`, Blocking `Yes` and Implementation `-`, while the Completion Checklist marks "Each Invariant has a corresponding Verification" and "Automatable verification does not rely only on Manual Review" as done.
- ADR-001: the Automated Tests rows for INV-01, INV-02, INV-03, INV-05 and INV-06 have Implementation `-`; the INV-03 row names its test but not its path. The index cites concrete tests for ADR-001 INV-01 and marks it Confirmed.
- Test search in this cycle: INV-01 is covered by `tests/agent/test_startup_workflow_preflight.py::TestComponentInitializerWorkflowPreflight::test_aborts_on_missing_workflow_definition` and `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal`; INV-03 by `tests/agent/workflow/test_workflow_engine.py::TestRunStageWithRetryGeneralization::test_execute_success_verify_failure_marks_task_failed`; INV-05 by `...::TestComponentInitializerWorkflowPreflight::test_aborts_on_invalid_workflow_json` and the detector tests `tests/agent/test_repl_health.py::TestCheckWorkflowDefinition` (malformed JSON, missing required key, missing required stage). Correction from `plan-to-implementation-procedure` Step 3a: `test_aborts_on_invalid_workflow_schema` is NOT an INV-05 test. It patches `check_workflow_schema` to return an invalid result and asserts that `_check_workflow_schema()` raises `RuntimeError`, which is the startup abort of INV-06 (inconsistent required DB schema). INV-06 is therefore verified by `...::TestComponentInitializerWorkflowPreflight::test_aborts_on_invalid_workflow_schema` (startup abort) together with `tests/agent/test_repl_health.py::TestCheckWorkflowSchema` (detection), and the initializer calls the schema check before constructing the Orchestrator. All cited node IDs were collected, and a run of `tests/agent/test_startup_workflow_preflight.py`, `tests/agent/test_repl_health.py`, `TestWorkflowLoadFailureIsFatal` and the INV-03 test passed (53 passed). No test was found for ADR-001 INV-02 or ADR-002 INV-03 and INV-04.
- `tools/check_adr_invariant_matrix.py` checks only the index matrix's test paths, so an empty body cell is not detected.

## Problem
The Accepted ADRs assert a verification completeness that their own tables do not show, and the evidence for the same invariant is split between the index and the ADR body without a stated canonical source. A test can be renamed with only one side updated, and the verification level of ADR-002 INV-03 and INV-04 is overstated.

## Reason for Change
Verification status decides whether an invariant is enforceable (the Gate rules of the ADR index). Overstated evidence in Accepted ADRs defeats that decision. The change depends on the vocabulary of the dependency plan, so it cannot be implemented earlier.

## Implementation Intent
Treat the ADR body Verification section as the canonical evidence record and the index as a synchronized summary. For each invariant with an empty Implementation cell, do exactly one of: cite an existing test by full node ID, or record it as not verified with the vocabulary of the dependency plan. Make the ADR-002 Completion Checklist state the true status of each item while keeping the `Completion Checklist` heading required by `check_adr_structure.py`. Add the canonical-source statement in one place, the index matrix introduction. Write no new tests.

## Requirements
- `REQ-001`: In ADR-001, cite the verified test node IDs for INV-01, INV-03 and INV-05, decide INV-06 from the closest tests (cite them if a test asserts startup abort, otherwise record the status defined by the dependency plan), and record INV-02 as not verified.
- `REQ-002`: In ADR-002, record INV-03 and INV-04 as not verified with the vocabulary of the dependency plan, and make the Completion Checklist items about Verification state the true status.
- `REQ-003`: In the index, state that the ADR body Verification section is canonical and the index mirrors it, make the ADR-001 INV-01 evidence identical in body and index, and keep the ADR body note about the index consistent with that statement.
- `REQ-004`: Keep every Invariant, Decision, Gate and Approval text unchanged, keep each file within the size gate, and leave the checkers without findings other than reviewed, intended `check_adr_preservation.py` reports.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | ADR-001 `### Automated Tests` table | Fill or mark the Implementation cells of INV-01, INV-02, INV-03, INV-05, INV-06 | REQ-001, REQ-004; AC-1, AC-4 | The table rows for these invariants end with `\| - \|`; the INV-07, INV-08, INV-10 and INV-11 rows cite node IDs in the same column (checked in Step 3) | N/A: documentation-only; validated by the checkers under Tests | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | ADR-002 `### Automated Tests` table and `### Completion Checklist` | Record INV-03 and INV-04 as not verified; correct the two Verification checklist items | REQ-002, REQ-004; AC-2, AC-4 | The INV-03 and INV-04 rows end with `\| - \|`; the Completion Checklist marks the Verification items `[x]` (checked in Step 3) | N/A: documentation-only; validated by the checkers under Tests | Verified |
| `docs/10_adr/adr_01_index.md` | ADR index matrix introduction and the ADR-001 INV-01 row | State the canonical-source rule; align the INV-01 evidence with the ADR body | REQ-003, REQ-004; AC-3, AC-4 | The matrix introduction states the matrix is not exhaustive and that each ADR's Verification section covers all its invariants, without naming a canonical source; the ADR-001 INV-01 row cites two tests (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/agent/test_startup_workflow_preflight.py` | Source of the INV-01 and INV-05 node IDs | REQ-001 |
| `tests/agent/test_orchestrator.py` | Source of the INV-01 node ID `TestWorkflowLoadFailureIsFatal` | REQ-001 |
| `tests/agent/workflow/test_workflow_engine.py` | Source of the INV-03 node ID | REQ-001 |
| `tests/agent/test_repl_health.py` | Closest tests for INV-06 (`TestCheckWorkflowSchema`) | REQ-001 |
| `scripts/agent/startup_component_init.py` | Confirms the initializer runs the workflow schema check at startup | REQ-001 |
| `tests/mcp_servers/test_config_isolation_fail_closed.py` | Confirms the existing isolation tests do not cover ADR-002 INV-03 or INV-04 | REQ-002 |
| `tools/check_adr_invariant_matrix.py` | Confirms the checker reads only the index status column | REQ-003 |
| `tools/check_adr_structure.py` | Defines the required `Completion Checklist` heading | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): No ADR-001 invariant has an empty Implementation cell without an explicit status; each cited node ID exists.
- AC-2 (REQ-002): ADR-002 INV-03 and INV-04 are recorded as not verified, and the Completion Checklist Verification items match the table.
- AC-3 (REQ-003): The index states which side is canonical; for every invariant in both an ADR body and the index matrix, the status and cited evidence agree; the ADR body note about the index does not contradict the statement.
- AC-4 (REQ-004): No Invariant, Decision, Gate or Approval text changed, each file is within the size gate, and the checkers under Tests pass except the reviewed, intended `check_adr_preservation.py` reports.

## Tests
- `uv run python tools/check_adr_invariant_matrix.py` and `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` (REQ-003).
- `uv run python tools/check_adr_structure.py` (REQ-002, REQ-004).
- `uv run python tools/check_adr_preservation.py` (REQ-004; each reported test-citation change is reviewed as intended).
- `uv run pytest` on every cited test node ID (REQ-001), to confirm the cited tests exist and pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` on the three files, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` (REQ-001 to REQ-004).

## Documentation Impact
Yes. `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md` and `docs/10_adr/adr_01_index.md` change (verification evidence and boundary, ADR checklist completion state, and the canonical-source rule); REQ-001 to REQ-003 drive it. Any invariant recorded as not verified is a candidate Needs Confirmation or Known Issue entry only if the repository owner decides so. All text is written in English.

## Assumptions
- The vocabulary of the dependency plan (`plans/20261027-104411_govrev003_partial-verification-gate-rules.md`) is implemented before this Plan; its overlap on `docs/10_adr/adr_01_index.md` is a sequencing dependency, and this Plan edits the introduction after it.
- Step 8b overlap judgments: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` is also targeted by `plans/20261027-104127_govrev002_adr-001-diff-command.md`; the designs are compatible (that Plan edits one Negative Consequences sentence, this Plan edits the Automated Tests table). `docs/10_adr/adr_01_index.md` is also targeted by `plans/20261027-104411_govrev003_partial-verification-gate-rules.md`; this is a sequencing dependency (that Plan edits the matrix introduction and status cells first, this Plan then adds one canonical-source statement), recorded in Scope Dependencies.
- The issue file was reverted on disk during this cycle to its pre-verification text by an external change; the verified test search results are therefore recorded in this Plan's Background and Unknowns, not in the issue.
- Citing a test for INV-06 is allowed only if a test asserts startup abort; otherwise INV-06 gets the status defined by the dependency plan. Step 3a found such a test (see Background), so INV-06 is cited, not marked.
- Size measurements in Step 3a (UTF-8 bytes): ADR-001 is 19141 B and ADR-002 is 20369 B against the default limit of 24576 B with no per-file exception (headroom 5435 B and 4207 B); `adr_01_index.md` has 2529 B of headroom shared with `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` (net growth budget 1200 B) and `plans/20261027-105004_govrev005_adr-matrix-checker-extension.md`, so this Plan's index edit is budgeted at 500 B at most.
- The ADR-001 INV-01 evidence in the index already equals the two tests this Plan cites in the body (`test_aborts_on_missing_workflow_definition` and `TestWorkflowLoadFailureIsFatal`); the index row needs no edit unless the body cites more.
- Recording an invariant as not verified keeps its Gate unchanged; the Blocking column of the ADR body table and the index Gate stay consistent under the dependency plan's rule (UNK-02).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Does a test assert that startup aborts on an inconsistent workflow DB schema (ADR-001 INV-06)? | Resolved in Step 3a: `test_aborts_on_invalid_workflow_schema` asserts the startup abort, and `TestCheckWorkflowSchema` covers detection | Cite both for INV-06 (see Background); the Phase 1 read-only check re-confirms them | False |
| UNK-02 | If an invariant is recorded as not verified while its ADR body row says Blocking `Yes`, which side changes? | The dependency plan's rule is not yet implemented | Decide under the vocabulary of `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` with the repository owner, per the sign-off channel of `rules/coding.md` Explicit sign-off gates | False |
| UNK-03 | Should the ADR-002 Completion Checklist items be unchecked or kept checked with a status note? | No stated preference | Unchecking is the recommendation; the `Completion Checklist` heading stays either way | False |
| UNK-04 | Implementation order: this Plan needs the vocabulary of the dependency plan, whose Execution Status rows are still `Pending` | Dependency not yet implemented | Implement `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` first; the implementation-procedure phase reads this Plan's Scope Dependencies | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Medium | 3 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium | 18 | N/A | not applicable (rsynced) |

## Design
- Path A: three documentation files, no public interface, no schema. Validation baseline is `N/A: no Python target`.
- Decision: the ADR body is canonical, the index mirrors it. Alternative rejected: the index as canonical, because each ADR's own Verification section covers all its invariants while the index is explicitly not exhaustive.
- Decision: cite only node IDs verified to exist; an invariant with no verifying test is recorded as not verified, never given an invented citation.
- Size headroom under the documentation size gate: ADR-001 about 5 KB, ADR-002 about 4 KB, the index about 2.5 KB shared with the dependency plan, so the index edit is one short statement.
- Blast radius: ADR-001 is referenced by 14 files and ADR-002 by 19; the index by 16 and changed 18 times in 30 days.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirm the evidence**
   - [ ] Confirm the dependency plan's vocabulary is implemented (UNK-04) and read the INV-06 candidate tests (UNK-01) (REQ-001; read-only)
   - [ ] Verify that every node ID to be cited exists (REQ-001; read-only)
2. **Phase 2: Edit the ADRs**
   - [ ] Fill or mark the ADR-001 Implementation cells (REQ-001; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`)
   - [ ] Mark ADR-002 INV-03 and INV-04 and correct the Verification checklist items (REQ-002; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`)
3. **Phase 3: Edit the index and verify (no deployment)**
   - [ ] Add the canonical-source statement and align the ADR-001 INV-01 row (REQ-003; `docs/10_adr/adr_01_index.md`)
   - [ ] Run the checkers and review every `check_adr_preservation.py` report (REQ-004; the three target files). No `scripts/` or `config/` file changes, so no deploy step applies.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Matrix checker and its tests | `check_adr_invariant_matrix.py`; `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` | No finding; tests pass |
| ADR-001, ADR-002 | Structure and preservation | `check_adr_structure.py`; `check_adr_preservation.py` | No structure issue; only reviewed test-citation changes reported |
| Cited tests | Existence and result of each cited node ID | `uv run pytest <node IDs> -q` | All cited tests exist and pass |
| Three target files | Documentation checks and size gate | `check_docs_quality.py`; `check_docs_structure.py`; `check_docs_content_policy.py --strict`; `check_docs_japanese.py` | No finding; sizes within the ceiling |

## Risks
- **Risk**: A cited node ID is wrong or later renamed → **Mitigation**: Verify each ID with a pytest run before citing; the matrix checker covers the index side.
- **Risk**: Recording an invariant as not verified conflicts with its Blocking column → **Mitigation**: Decide under the dependency plan's vocabulary (UNK-02) and do not change any Gate silently.
- **Risk**: `check_adr_preservation.py` reports ERROR for the intended test-citation changes → **Mitigation**: Review each report as intended; never suppress the check, and stop if an Invariant, Decision or Approval text appears in the report.
- **Risk**: The index edit exceeds the size gate after the dependency plan consumed headroom → **Mitigation**: Keep the statement to one sentence and measure before and after.
- **Risk**: Implementing before the dependency plan leaves the vocabulary undefined → **Mitigation**: Scope Dependencies and UNK-04 fix the order; Phase 1 confirms it first.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the evidence and the dependency plan | Pending | — | — | |
| 2 | Edit ADR-001 and ADR-002 | Pending | — | — | |
| 3 | Edit the index and run the checkers (no deployment) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-101918_govrev004_adr-verification-evidence-sync.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-104705
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_01_index.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (search tests, cite or mark); Background (test search) | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 1, Phase 2 | AC-1 | `uv run pytest <cited node IDs> -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes (ADR-002 INV-03 and INV-04; checklist) | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 2 | AC-2 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (canonical-source statement; INV-01 evidence) | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-3 | `check_adr_invariant_matrix.py`; `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-004 | Constraints; Acceptance Criteria; Testing Expectations | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 2, Phase 3 | AC-4 | `check_adr_preservation.py`; `check_docs_structure.py` | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria; Testing Expectations | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 2, Phase 3 | AC-4 | `check_adr_preservation.py`; `check_docs_structure.py` | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria; Testing Expectations | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-4 | `check_adr_preservation.py`; `check_docs_structure.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-111927 -->
