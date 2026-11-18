## Goal
- Make every safety-tier gap and every unverifiable RAG consistency result produce a recorded non-ok startup entry, and make ADR-003 describe the same startup behavior in ADR-004 terms with the approval state of Decisions #15, #16, and #17 shown as pending.

## Priority
High

## Scope
- **In-Scope**:
  - `check_config` records each safety-tier gap as FATAL (`routing_safety_tiers`); the drift comment and docstrings state what strict mode really does.
  - `rag_consistency.py` gets issue builders (DEGRADED findings) for the five silent rules in `_CHECKS`: `diagnostic_errors`, a failed `read_smoke_test_ok`, `fk_unverified`, `embedding_unverified`, `schema_unverified`.
  - `check_services` records a FATAL `rag_consistency` entry when `is_consistent` is false and no finding was recorded.
  - ADR-003 wording: Decision #15 severity, abort scope "regardless of `required`", Fail-Fast vs Fail-Closed, Derived Data, and pending approval state for Decisions #15, #16, #17.
  - Scope amendments against the Issue's Target Files, both decided by the user in this cycle: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (ledger rows the ADR-003 pending bullets cite) and `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (documents the new findings); plus the three existing test files that pin the old safety-tier warning behavior.
- **Out-of-Scope**:
  - Writing approval text for any ADR-003 Decision, and filling `Approver`/`Date` of a ledger row.
  - Choosing the final RAG severity beyond the pending classification already recorded in ADR-004 Decision Group 2 item 7 (ledger AAL-019).
  - `scripts/db/models.py` (verified: needs no change), `shared/tool_routing_validation.py`, and the behavior of an empty `tool_safety_tiers` (see UNK-03).
  - Editing generated files (`registry/manifests/*.yaml`, guarded blocks).
- **Dependencies**: N/A: none open. The RAG failure policy issue (adrchk006) and the ADR approval governance issue (adrchk011) are already implemented and archived; this Plan builds on their results (AAL-019, the pending-bullet form, the ledger).

## Background
Filed from the consolidated ADR review (package ADRCHK2-H05, findings H2, H3, M17, N45). Re-verification against current source (checked in Step 2 and Step 3) changed the picture:
- Routing drift is already fatal: `check_routing_drift(strict=True)` raises `RuntimeError` when any drift exists, and `check_config` maps that to `add_fatal("routing_drift", ...)`. With strict mode the returned list is always empty, so the `add_warning` loop in `check_config` never records anything.
- Safety-tier gaps are warnings: `check_tool_safety_tiers` returns one message per registered tool missing from `tool_safety_tiers` and `check_config` sends each to `add_warning`; only an exception becomes FATAL.
- The five silent RAG rules are confirmed: `_CHECKS` entries without an issue builder make `is_consistent` false while `findings` stays empty, and `check_services` iterates only `findings`, so startup records no entry.
- ADR-003: Decision #15 says drift "warns" while the Verification table says startup aborts on drift (Implementation Notes carry no drift statement); the Startup Validation bullet limits the posture abort to `required=true` servers while Decision #16 and ADR-004 abort regardless; the unregistered-tool bullet sits under Fail-Fast although ADR-004 Decision Group 5 item 15 classifies it as runtime Fail-Closed; `ToolRegistry` is called Derived Data although `scripts/shared/tool_registry.py` populates it from `tool_constants.py` frozensets, not from `RuntimeToolRegistry`; the Approval Record covers Decisions #1 to #15 only.

## Problem
A safety-tier gap and an unverifiable RAG result can let startup finish with no fatal result (and, for the RAG rules, no entry at all), and ADR-003 states the drift severity, abort scope, failure class, and data class inconsistently with the code and ADR-004.

## Reason for Change
ADR-004 INV-07 makes Safety Tier failures Fail-Closed at startup, and the RAG failure policy now classifies an unverifiable consistency result as an availability failure that must be reported. The current code silently drops both, and ADR-003 contradicts itself.

## Implementation Intent
- Treat a safety-tier gap as FATAL at the `check_config` call site (the function keeps returning messages).
- Add one issue builder per silent rule in `_CHECKS` (single-rule design kept, no second condition list) producing DEGRADED findings, so the existing startup routing records a warning entry; add a FATAL fallback entry in `check_services` for the case "not consistent and no finding" so a future rule without a builder cannot pass silently.
- Rewrite the ADR-003 sentences to one description, and mark #15 (severity correction), #16, and #17 as pending with ledger rows, without approval text.

## Requirements
- `REQ-001`: Drift handling is documented as it behaves: strict mode raises on any drift, `check_config` records it as FATAL; the stale comment and docstrings are corrected; a test with one unregistered routed tool yields a FATAL `routing_drift` entry.
- `REQ-002`: Each safety-tier gap message from `check_routing_safety_tiers` is recorded as a FATAL `routing_safety_tiers` entry; a test with one tool missing from `tool_safety_tiers` yields a FATAL entry.
- `REQ-003`: `_CHECKS` gives each of `diagnostic_errors`, `read_smoke_test_ok`, `fk_unverified`, `embedding_unverified`, `schema_unverified` an issue builder returning a DEGRADED finding with a message and `repair_action`; no second list of conditions is added; `_ConsistencyCheck.issue` is required once no rule lacks one.
- `REQ-004`: `check_services` records a FATAL `rag_consistency` entry when `is_consistent` is false and the result has no finding; a test with `fk_unverified=True` and all counts zero produces a non-ok `rag_consistency` entry.
- `REQ-005`: ADR-003 Decision #15, the Verification table, and the Startup Validation text use one severity (drift aborts startup); the Startup Validation bullet says "regardless of `required`"; the unregistered-tool condition is classed as Fail-Closed; `ToolRegistry` is described as static reference data, not Derived Data.
- `REQ-006`: ADR-003 shows Decisions #15 (severity correction), #16, and #17 as pending approval in the form `- **Current Decision Approval (pending)**: ... tracked by AAL-0NN.`; `governance_03` Part 5 gains the matching ledger rows with `Approver` and `Date` `Not recorded`.
- `REQ-007`: `rag_05_07` lists the new findings (severity, `repair_action`, fix) and the startup routing sentence stays true.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify: safety-tier gaps to `add_fatal`; correct the drift comment; add the FATAL `rag_consistency` fallback entry | Gaps are recorded as warnings (`add_warning` loop in `check_config`); `check_services` iterates only `findings` | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-3 | `check_config` sends safety-tier messages to `add_warning` and the comment says drift is always FATAL; `check_services` routes only `rag_check.findings` (checked in Step 2 and Step 3) | `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py` | Verified |
| `scripts/agent/services/routing_drift.py` | Modify: docstrings state that strict mode raises on any drift and the safety-tier function returns gap messages the caller records as FATAL | Docstrings say "Returns warning messages" for both | REQ-001, REQ-002 / AC-1, AC-2 | `check_routing_drift` raises `RuntimeError` when `drift and strict`; `check_routing_safety_tiers` wraps `check_tool_safety_tiers` (checked in Step 3) | `tests/agent/test_startup_validation.py` | Verified |
| `scripts/db/rag_consistency.py` | Modify: add five issue builders and wire them into `_CHECKS`; make `_ConsistencyCheck.issue` required and update its docstring | Five `_CHECKS` rules have `issue=None`, so `findings` stays empty while `is_consistent` is false | REQ-003, REQ-004 / AC-3 | `_CHECKS` entries for `diagnostic_errors`, `read_smoke_test_ok`, `fk_unverified`, `embedding_unverified`, `schema_unverified` have no builder; `findings` is built only from entries with a builder (checked in Step 3) | `tests/db/test_rag_consistency.py` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify: Decision #15 severity, Verification row, Startup Validation bullet, Failure Policy classification, Data Ownership term, pending bullets for #15, #16, #17 | Contradictory severity, abort scope, failure class, data class; no approval state for #16 and #17 | REQ-005, REQ-006 / AC-5, AC-6 | Decision #15 says "warns"; Verification says "startup is aborted on drift"; Startup Validation says `required=true`; the Approval Record covers #1 to #15 (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` (validation) | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify: add ledger rows AAL-021, AAL-022, AAL-023 to Part 5 | The pending bullets cite ledger ids that must exist first (scope amendment decided by the user) | REQ-006 / AC-6 | Part 5 ends at AAL-020 (ADR-005 row); the ledger row form has `ID`, `ADR`, `Decision`, `Approver`, `Date`, `Scope` (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify: add rows for the new findings to the repair table and the Startup Warnings text | The document lists every finding with severity and `repair_action`; new findings must appear (scope amendment) | REQ-007 / AC-7 | `Repair Decision Flow` table and `Startup Warnings` list the existing findings only (checked in Step 2) | `tools/check_docs_structure.py` (validation) | Verified |
| `tests/agent/test_startup_validation.py` | Modify: add tests for a real drifted tool, a safety-tier gap, and the RAG fallback entry | Acceptance Criteria require these tests | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-3 | Existing `test_routing_drift_is_fatal` and `test_safety_tier_failure_is_fatal` mock the functions and never use real drift data (checked in Step 3) | itself | Verified |
| `tests/agent/test_startup_severity_classification.py` | Modify: change `test_routing_safety_tiers_warning_on_messages` to expect FATAL | It pins the old warning behavior | REQ-002 / AC-2 | Test at line 345 asserts a warning for returned messages (checked in Step 3) | itself | Verified |
| `tests/agent/test_startup.py` | Modify: same change for its `test_routing_safety_tiers_warning_on_messages` | It pins the old warning behavior | REQ-002 / AC-2 | Test at line 440 asserts a warning for returned messages (checked in Step 3) | itself | Verified |
| `tests/db/test_rag_consistency.py` | Modify: tests that each silent rule yields a finding, `is_consistent` agrees with `findings`, and `fk_unverified=True` with zero counts yields a finding | Acceptance Criteria; pins the single-rule design | REQ-003, REQ-004 / AC-3 | `test_is_consistent_false_on_diagnostic_errors` checks only `is_consistent`; the unverified-probe tests check only the flags (checked in Step 3) | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/models.py` | `ConsistencyFinding`, `FindingSeverity`, `RagConsistencyReport` fields; verified that no change is needed | REQ-003 |
| `scripts/shared/tool_routing_validation.py` | `check_tool_safety_tiers` returns one message per missing tool and `[]` when `tool_safety_tiers` is empty | REQ-002 |
| `scripts/shared/tool_registry.py` | Shows `ToolRegistry` is populated from `tool_constants.py`, not from `RuntimeToolRegistry` | REQ-005 |
| `scripts/agent/shared/health_models.py` | `StartupValidationResult.add_fatal` / `add_warning` semantics | REQ-002, REQ-004 |
| `scripts/agent/services/rag_maintenance_service.py` | `consistency()` builds `RagConsistencyResult` from the report | REQ-004 |
| `scripts/db/rag_consistency_queries.py` | Where the probes and `_check_read_smoke_test` are defined | REQ-003 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | INV-02, INV-07, Decision Group 5 item 15, Group 2 item 7 pending bullet (AAL-019), pending-bullet example | REQ-005, REQ-006 |
| `docs/00_governance/governance_01_documentation-governance.md` | Pending amendment form and Withdrawn/approval rules | REQ-006 |
| `tools/check_adr_structure.py` | Pending-form and ledger-id checks the ADR edit must satisfy | REQ-006 |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Existing drift and safety-tier pipeline tests that must keep passing | REQ-001, REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): a test with one unregistered routed tool in config `tool_names` produces a FATAL `routing_drift` entry through the real `check_routing_drift(strict=True)`.
- AC-2 (REQ-002): a test with one registered tool missing from `tool_safety_tiers` produces a FATAL `routing_safety_tiers` entry; no WARNING entry is recorded for it.
- AC-3 (REQ-003, REQ-004): a test with `fk_unverified=True` and all counts zero produces a non-ok `rag_consistency` entry; each of the five silent rules yields exactly one finding; for any report, `is_consistent` is true only if `findings` is empty.
- AC-4 (REQ-004): when the service result is not consistent and has no finding, a FATAL `rag_consistency` entry is recorded.
- AC-5 (REQ-005): ADR-003 Decision #15, the Verification table, and the Startup Validation bullets use the same severity; the Startup Validation bullet says "regardless of `required`"; the unregistered-tool condition is not under Fail-Fast; `ToolRegistry` is not called Derived Data.
- AC-6 (REQ-006): `check_adr_structure.py` passes with the new pending bullets; ledger ids exist in `governance_03` Part 5; no approval text is written.
- AC-7 (REQ-007): `rag_05_07` lists each new finding with severity and `repair_action` equal to the code values.

## Tests
- REQ-001 / REQ-002 / REQ-004: unit tests in `tests/agent/test_startup_validation.py`; update the two pinned tests in `tests/agent/test_startup_severity_classification.py` and `tests/agent/test_startup.py`.
- REQ-003 / REQ-004: unit tests in `tests/db/test_rag_consistency.py`, including the invariant that no unclean rule is missing from `findings`.
- REQ-005 / REQ-006 / REQ-007: documentation checkers (see Validation plan).

## Documentation Impact
Yes. ADR-003 (REQ-005, REQ-006) and `rag_05_07` (REQ-007) per `routing.md` Docs mapping; `governance_03` Part 5 ledger rows (REQ-006). Run the checkers listed in `routing.md` Tools after each `docs/` edit. `agent_10_01` already says the safety-tier check records no outcome when healthy and needs no edit.

## Assumptions
- AAL-021, AAL-022, AAL-023 are the next free ledger ids (the ledger ends at AAL-020; verified in Step 2).
- The Decision #15 severity correction ("warns" to "aborts startup") is treated as an amendment of an approved decision, so it gets a pending bullet instead of an approval statement (conservative reading of governance_01/governance_05; see UNK-04).
- Unverifiable RAG results are DEGRADED (WARNING) findings, aligned with ADR-004 Decision Group 2 item 7 (pending, AAL-019); decided by the maintainer in this cycle. The FATAL fallback in `check_services` covers only a rule that has no builder.
- No overlap with another Frozen Plan (checked in Step 8b).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | `repair_action` value and message wording for the five unverifiable findings | No documented vocabulary for "re-run the check" findings; existing values are `rebuild_fts`, `rebuild_vec`, `reingest`, `restore_from_backup` | Implementer chooses one value, records it in `rag_05_07` and the test pinning it; no approval needed (code and doc vocabulary) | False |
| UNK-02 | Whether the ADR-003 template and `check_adr_structure.py` allow a `Fail-Closed Conditions` subsection under Failure Policy | `docs/10_adr` template and the checker were not read for this question | Implementer reads the ADR template and the checker; if no subsection is allowed, state the Fail-Closed classification in an existing bullet instead | False |
| UNK-03 | An empty `tool_safety_tiers` makes `check_tool_safety_tiers` return `[]`, so no gap is reported when tiers are not configured | Whether ADR-004 INV-07 requires the map to be non-empty | Outside this Issue; record in the report and let the maintainer file a separate Issue | False |
| UNK-04 | Whether the Decision #15 severity correction needs an approval record (pending) or counts as a wording correction | `governance_01`/`governance_05` do not say how to classify a severity correction of an approved decision | Plan uses the conservative pending bullet (AAL-021); maintainer may withdraw it | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify | High (startup pipeline) | 14 | N/A | `scripts/` change: deploy to `/opt/llm` is the user's decision (`skills/deploy/SKILL.md`) |
| `scripts/agent/services/routing_drift.py` | Modify | Low (docstrings only) | 0 | N/A | `scripts/` change: same hand-off |
| `scripts/db/rag_consistency.py` | Modify | Medium (new findings change startup output) | 4 | N/A | `scripts/` change: same hand-off |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Medium | 8 | N/A | None: documentation only |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Low | 15 | N/A | None: documentation only |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Low | 6 | N/A | None: documentation only |
| `tests/agent/test_startup_validation.py` | Modify | Low | 10 | N/A | None: tests are not deployed |
| `tests/agent/test_startup_severity_classification.py` | Modify | Low | N/A | N/A | None: tests are not deployed |
| `tests/agent/test_startup.py` | Modify | Low | N/A | N/A | None: tests are not deployed |
| `tests/db/test_rag_consistency.py` | Modify | Low | 6 | N/A | None: tests are not deployed |

## Design
Path B (more than 3 target files). Architecture, dependency, history, and operational checks were run once each (checked in Step 3 and Step 5): `lint-imports` reports 6 contracts kept, 0 broken; `startup_validation.py` is imported by the startup pipeline and tests only; no process or lock issue applies (no schema or server change); radon reports `check_services` at C (19) and `check_rag_consistency` at C (18), so additions go into new small functions rather than into those bodies; vulture and bandit report nothing for the target modules.

Decisions:
1. Drift: strict mode already raises on any drift, so no behavior change is needed. Fix the `check_config` comment and the two docstrings; the `add_warning` loop in `check_config` can only run on an empty list in strict mode and the implementer removes it if the tests allow, otherwise keeps it with an accurate comment (alternative considered: send returned messages to `add_fatal`; rejected because nothing is ever returned).
2. Safety tiers: `check_routing_safety_tiers` keeps returning messages (its callers in `tests/agent/shared/test_startup_validation_pipeline.py` expect a list); `check_config` records each as `add_fatal("routing_safety_tiers", msg)` per ADR-004 INV-07. Alternative (raise inside the function) rejected: it would change the return contract.
3. RAG: five `_ConsistencyCheck` builders in `rag_consistency.py` return `ConsistencyFinding(severity=DEGRADED, ...)`, so `summarize_issues` and `check_rag_consistency` pick them up without a second condition list. Because every rule then has a builder, `_ConsistencyCheck.issue` becomes required. Alternative (FATAL, the Issue's interim value) rejected by the maintainer in this cycle in favor of ADR-004 item 7 alignment.
4. Fallback in `check_services`: when `is_consistent` is false and `rag_check.findings` is empty, call `pipeline.add_fatal("rag_consistency", ...)` (fail-closed guard for a rule without a builder). It needs a test that supplies an inconsistent result with no finding.
5. ADR-003 wording: Decision #15 "warns after the fact" becomes "aborts startup when drift is detected (ADR-004 INV-02)"; Startup Validation bullet: a posture failure aborts startup "regardless of `required`" (ADR-004); the unregistered-tool condition is runtime Fail-Closed (ADR-004 Decision Group 5 item 15; subject to UNK-02); `ToolRegistry` becomes "Static Reference Data (tests, documentation generation, startup Drift validation)".
6. Pending approval: three bullets `- **Current Decision Approval (pending)**: ... tracked by AAL-02N.` under `### Approval Record`, with ledger rows AAL-021 (#15 severity), AAL-022 (#16), AAL-023 (#17) in `governance_03` Part 5; the ledger rows must land before the ADR bullets that cite them.
Consumer scan: not run; no persisted schema, public API, or shared constant changes (`ConsistencyFinding` shape is unchanged).

## Implementation steps
1. **Phase 1: Ledger rows**
   - [ ] Add AAL-021, AAL-022, AAL-023 to Part 5 with `Approver` and `Date` `Not recorded` (REQ-006; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
2. **Phase 2: RAG findings**
   - [ ] Add the five issue builders, wire them into `_CHECKS`, make `issue` required (REQ-003; `scripts/db/rag_consistency.py`)
   - [ ] Add tests for each rule, the `is_consistent`/`findings` invariant, and the `fk_unverified` case (REQ-003, REQ-004; `tests/db/test_rag_consistency.py`)
   - [ ] Add the new rows to the repair table and the Startup Warnings text (REQ-007; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`)
3. **Phase 3: Startup pipeline**
   - [ ] Record safety-tier gaps as FATAL, correct the drift comment, add the `rag_consistency` fallback entry (REQ-001, REQ-002, REQ-004; `scripts/agent/startup_validation.py`)
   - [ ] Correct the docstrings (REQ-001, REQ-002; `scripts/agent/services/routing_drift.py`)
   - [ ] Add the real-drift, safety-tier gap, and fallback tests (REQ-001, REQ-002, REQ-004; `tests/agent/test_startup_validation.py`)
   - [ ] Update the two pinned warning tests (REQ-002; `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`)
4. **Phase 4: ADR-003 wording and pending state**
   - [ ] Apply the Design decision 5 and 6 edits, then run `check_adr_structure.py` and the ADR checkers from `routing.md` (REQ-005, REQ-006; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the full validation sequence (`rules/toolchain.md`) and the doc checkers; after the change is committed and pushed, hand off to `skills/deploy/SKILL.md` for the `scripts/` changes (deploying is the user's decision; REQ-002, REQ-003, REQ-004; files of Phases 2 and 3)

### Release units
N/A: no release unit (each phase passes validation alone)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/db/rag_consistency.py`, `tests/db/test_rag_consistency.py` | Unit | `uv run pytest tests/db/test_rag_consistency.py` | Five new findings; invariant holds |
| `scripts/agent/startup_validation.py`, `scripts/agent/services/routing_drift.py` and three startup test files | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup_severity_classification.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py` | FATAL entries for gap and fallback; drift FATAL via real function |
| ADR-003, `governance_03`, `rag_05_07` | Documentation | `uv run python tools/check_adr_structure.py`, `tools/check_docs_structure.py` and the checkers in `routing.md` Tools | No findings |
| Whole change | Full suite and coverage | `rules/toolchain.md` validation sequence, `diff-cover` at the threshold in its Completion checklist | All pass; 100% diff coverage |

## Risks
- **Risk**: Making safety-tier gaps FATAL aborts startup on a production configuration that currently only warns (likelihood medium) → **Mitigation**: run `check_routing_safety_tiers` against the production `config/agent.toml` before deploy (read-only) and report any gap to the user; deploy remains the user's decision.
- **Risk**: A new DEGRADED finding for `read_smoke_test_ok` or `diagnostic_errors` adds startup warnings on databases that were silently passing (likelihood medium) → **Mitigation**: warnings do not abort startup; document the new findings in `rag_05_07`.
- **Risk**: The ADR-003 edit touches Decision #15 text approved on 2026-10-07 (likelihood low) → **Mitigation**: pending bullet and ledger row only; no approval text; UNK-04 records the classification question.
- **Risk**: `check_adr_structure.py` rejects a pending bullet whose ledger id is missing (likelihood low) → **Mitigation**: Phase 1 lands the ledger rows before Phase 4.
- **Risk**: The adrchk006 follow-up and other Plans edit `startup_validation.py` and `rag_consistency.py` (likelihood medium) → **Mitigation**: re-run the searches in the Acceptance Criteria before editing; a defect already gone is recorded with evidence and skipped.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add ledger rows AAL-021 to AAL-023 in governance_03 | Pending | — | — | |
| 2 | Phase 2: RAG issue builders, tests, rag_05_07 rows | Pending | — | — | |
| 3 | Phase 3: startup pipeline FATAL entries, docstrings, tests | Pending | — | — | |
| 4 | Phase 4: ADR-003 wording and pending bullets | Pending | — | — | |
| 5 | Phase 5: full validation and deploy hand-off | Pending | — | — | |

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
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-134945
- **Related target files**: `scripts/agent/startup_validation.py`; `scripts/agent/services/routing_drift.py`; `scripts/db/rag_consistency.py`; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`; `tests/agent/test_startup_validation.py`; `tests/agent/test_startup_severity_classification.py`; `tests/agent/test_startup.py`; `tests/db/test_rag_consistency.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change (drift); `routing_drift.py` strict raise | `scripts/agent/startup_validation.py` | 3 | AC-1 | `tests/agent/test_startup_validation.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes (read `routing_drift.py`) | `scripts/agent/services/routing_drift.py` | 3 | AC-1 | `tests/agent/test_startup_validation.py` | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria (unregistered routed tool) | `tests/agent/test_startup_validation.py` | 3 | AC-1 | `uv run pytest tests/agent/test_startup_validation.py` | Explicit in issue |
| REQ-002 | Reason for Change (safety tiers go to `add_warning`) | `scripts/agent/startup_validation.py` | 3 | AC-2 | `tests/agent/test_startup_validation.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes (same rule for safety tiers) | `scripts/agent/services/routing_drift.py` | 3 | AC-2 | `tests/agent/test_startup_validation.py` | Derived from confirmed evidence |
| REQ-002 | Acceptance Criteria (tool missing from `tool_safety_tiers`) | `tests/agent/test_startup_validation.py` | 3 | AC-2 | `uv run pytest tests/agent/test_startup_validation.py` | Explicit in issue |
| REQ-002 | Existing tests pin the warning | `tests/agent/test_startup_severity_classification.py` | 3 | AC-2 | `uv run pytest tests/agent/test_startup_severity_classification.py` | Confirmed by repository evidence |
| REQ-002 | Existing tests pin the warning | `tests/agent/test_startup.py` | 3 | AC-2 | `uv run pytest tests/agent/test_startup.py` | Confirmed by repository evidence |
| REQ-003 | Reason for Change (silent RAG rules); Required Changes (issue builders) | `scripts/db/rag_consistency.py` | 2 | AC-3 | `tests/db/test_rag_consistency.py` | Confirmed by repository evidence |
| REQ-003 | Constraints (single-rule `_CHECKS`) | `tests/db/test_rag_consistency.py` | 2 | AC-3 | `uv run pytest tests/db/test_rag_consistency.py` | Explicit in issue |
| REQ-004 | Required Changes (fatal entry when no finding) | `scripts/agent/startup_validation.py` | 3 | AC-3, AC-4 | `tests/agent/test_startup_validation.py` | Explicit in issue |
| REQ-004 | Acceptance Criteria (`fk_unverified=True`) | `tests/agent/test_startup_validation.py` | 3 | AC-3, AC-4 | `uv run pytest tests/agent/test_startup_validation.py` | Explicit in issue |
| REQ-004 | Acceptance Criteria (`fk_unverified=True`, counts zero) | `tests/db/test_rag_consistency.py` | 2 | AC-3 | `uv run pytest tests/db/test_rag_consistency.py` | Explicit in issue |
| REQ-005 | Reason for Change (ADR-003 contradictions); Required Changes | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 4 | AC-5 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-006 | Reason for Change (approval records); Required Changes (pending) | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 4 | AC-6 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-006 | Dependencies (pending form from governance issue); ledger required | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 1 | AC-6 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-007 | Documentation Impact; rag doc lists every finding | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | 2 | AC-7 | `tools/check_docs_structure.py` | Derived from confirmed evidence |
