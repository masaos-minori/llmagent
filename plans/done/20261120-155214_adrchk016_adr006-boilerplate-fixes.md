# Plan: Fix ADR-006 internal conflicts and remove stale ADR boilerplate

## Goal
- Resolve the confirmed ADR-006 internal/Index conflicts, state the `since_seq` condition under its delivery guarantee as a pending amendment, and remove the stale single-DB / privileges-only-in-SQLite / runtime-behavior boilerplate from ADR-001, ADR-002, ADR-003, ADR-005, ADR-006, and ADR-009.

## Priority
Medium

## Scope
- **In-Scope**: the eight files in `Implementation Target Files`; documentation-only edits.
- **Out-of-Scope**: changing EventBus behavior; any `scripts/`, `tests/`, `config/`, or generated (`AUTO-GENERATED`) block edit; writing or simulating a maintainer approval statement.
- **Dependencies**: N/A: none — the Issue's two dependencies (adrchk008 and adrchk011) are both archived under `issues/done/` (closed); no open dependency gates this Plan.

## Background
- Filed from `issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md` (consolidated ADR review package `ADRCHK2-M04`). The review's claims carry the label `Documentation only`; Step 2 re-verified each against current source. Two claims were already fixed by earlier batches and are recorded below without generating a task.

## Problem
- ADR-006 contradicts itself on INV-06 verification, contrasts Alternative B against a capability the chosen model already has, and its delivery guarantee omits the `since_seq` condition that the Replay Contract already documents. The Index Invariant Verification Matrix row for INV-05/INV-09 contradicts Decision 11a.
- Stale boilerplate: ADR-005, ADR-006, and ADR-009 still describe a single SQLite database and "items to re-evaluate: multi-DB configuration" although ADR-008 has already separated SQLite into six databases. ADR-006, ADR-005, and ADR-009 still state "privileges are granted only within SQLite", which predates the ADR-013/ADR-017 authentication layers. ADR-001, ADR-002, and ADR-003 each list "Changes to runtime behavior" in Out of Scope although their Decisions mandate runtime behavior.
- Already resolved (no task, evidence kept):
  - "item 11b says non-empty consumer ID while ADR-013 requires an explicit ID": ADR-006 Decision 11b (line 80) and INV-10 (line 190) already state the explicit `consumer_id`/topic binding governed by ADR-013.
  - "Verification references stale test names": all 19 test references in ADR-006 resolve against `tests/` (script check of every `tests/**.py::Symbol` reference: 18 qualified pairs + 1 bare path, zero missing).

## Reason for Change
- ADRs are the authoritative decision record; a self-contradicting ADR and a stale Index row misdirect implementers and reviewers, and boilerplate describing a superseded architecture violates the Current-Specification-Only policy.

## Implementation Intent
- Correct each confirmed conflict from the current code and ADR text, add the missing delivery-guarantee condition in the governance_01 pending-amendment form (no approval text), and replace each stale boilerplate sentence with a sentence describing the current architecture.

## Requirements
- `REQ-001`: ADR-006 Manual Review must no longer claim INV-06 has no dedicated automated test; it must be consistent with the Automated Tests table's INV-06 row.
- `REQ-002`: ADR-006 Alternative B must not imply the chosen model forbids out-of-order ACKs; the rejection must rest only on backward offset movement, citing Decision 13.
- `REQ-003`: ADR-006 Decision Detail 9 must state the `since_seq` condition (a Consumer-initiated start position is not a loss under At-Least-Once), recorded as a pending amendment with a new ADR approval ledger entry; no approval text may be written.
- `REQ-004`: The Index Invariant Verification Matrix row for ADR-006 INV-05/INV-09 must match Decision 11a: an equal or lower offset is accepted and the stored offset never moves backward.
- `REQ-005`: ADR-005, ADR-006, and ADR-009 must describe the current per-process database layout and must not list multi-DB configuration as a future re-evaluation item.
- `REQ-006`: No ADR under `docs/10_adr/` may state that privileges are granted only within SQLite.
- `REQ-007`: ADR-001, ADR-002, and ADR-003 Out of Scope must not contain the boilerplate line "Changes to runtime behavior".

## Implementation Target Files
**Freeze status**: Frozen (all eight rows `Verified` in Step 8b: paths exist per `audit_plan_target_paths.py` (0 findings), concrete modification reasons, line-number evidence recorded in Step 2, and every row linked to a Plan Requirement; no path appears in both sections).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Fix INV-06 Manual Review conflict; clarify Alternative B; add the `since_seq` condition to Decision Detail 9 with a pending-amendment bullet; restate Assumptions/Constraints/Security boilerplate | REQ-001, REQ-002, REQ-003, REQ-005, REQ-006; AC1-AC3, AC5, AC6 | Conflicts at lines 249 vs 278; 133-139 vs 85; guarantee text at 76 without the `since_seq` condition while 90-92 documents the override; boilerplate at 50, 58, 60, 62, 176 (checked in Step 2) | `tests/eventbus/test_eventbus_publish.py::test_identical_content_retry_returns_same_seq`, `tests/eventbus/test_eventbus_publish.py::test_conflicting_content_retry_returns_409` (existing; cited, not modified) | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Add the AAL-037 ledger entry for the REQ-003 pending amendment after AAL-036 (Part 5) | REQ-003; AC3 | Last ledger entry `#### AAL-036` at line 666, `## Resolution Rules` follows at 670; entry format per AAL-033 (checked in Step 2) | N/A: governance ledger entry | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | Reword the Invariant Verification Matrix row `ADR-006 INV-05, INV-09` (hand-edited section; the AUTO-GENERATED guards close at line 153, the matrix starts at 162) | REQ-004; AC4 | Line 199 says "an equal offset is accepted, a lower one is not" while 11a (ADR-006 line 79) accepts a lower offset unchanged (checked in Step 2) | `tests/eventbus/test_eventbus_offsets.py::TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward` (existing; cited, not modified) | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Replace the single-DB and privileges-only-in-SQLite sentences and the re-evaluate line | REQ-005, REQ-006; AC5, AC6 | Lines 50, 58, 60, 62, 160 (checked in Step 2) | N/A: documentation-only | Verified |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Replace the single-DB and privileges-only-in-SQLite sentences and the re-evaluate line | REQ-005, REQ-006; AC5, AC6 | Lines 56, 58, 60, 153 (checked in Step 2) | N/A: documentation-only | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Delete the "Changes to runtime behavior" line from Out of Scope | REQ-007; AC7 | Line 85 contradicts Decision Details 1-5 (lines 60-66: mandatory engine, startup abort) (checked in Step 2) | N/A: documentation-only | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Delete the "Changes to runtime behavior" line from Out of Scope | REQ-007; AC7 | Line 107 contradicts Decision Details 1-7 (lines 62-68: per-process config-read rules) (checked in Step 2) | N/A: documentation-only | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Delete the "Changes to runtime behavior" line from Out of Scope | REQ-007; AC7 | Line 112 contradicts Decision Details 1-7 (lines 71-77: sole routing authority, startup failure rules) (checked in Step 2) | N/A: documentation-only | Verified |

Additional checks before freeze (Step 8b): no path appears in both sections; every row is an exact existing file path.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/subscribe_route.py` | `since_seq` > resume position > `Last-Event-ID` precedence, lines 110-127 | REQ-003 |
| `scripts/eventbus/auth.py` | Role model and per-role token map (lines 80-90) proving privilege enforcement lives in the authenticated HTTP boundary, not in SQLite | REQ-006 |
| `tests/eventbus/test_eventbus_publish.py` | Exists-check for the INV-06 test row (`test_identical_content_retry_returns_same_seq`, `test_conflicting_content_retry_returns_409`) | REQ-001 |
| `tests/eventbus/test_eventbus_publish_contract.py` | `TestPublishEnvelopeSchemaContract` and `TestPublishContract` exist (cited by ADR-006) | REQ-001 |
| `tests/eventbus/test_eventbus_offsets.py` | `TestConsumerOffsetsTable` and `TestSqliteOffsetMonotonicity` exist (cited by ADR-006 and the Index) | REQ-001, REQ-004 |
| `tests/eventbus/test_eventbus_ack_nack.py` | `TestAckHttpBehavior::test_ack_lower_seq_keeps_offset` exists (cited by ADR-006 and the Index) | REQ-004 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Six-database decision and Decision Detail #22 (lines 2, 134) ground the boilerplate replacement wording | REQ-005 |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | INV-01..INV-07 (lines 201-209) and Alternative B (lines 154-158) ground the ADR-006 privilege-model wording | REQ-002, REQ-006 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Pending Amendment Form (line 298 ff.) and ADR Change Protocol define REQ-003's required form | REQ-003 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Required Reviewers map to RACI roles for the pending amendment | REQ-003 |

## Acceptance Criteria
- `AC1` (REQ-001): ADR-006 Manual Review no longer states INV-06 lacks a dedicated automated test and is consistent with the Automated Tests table.
- `AC2` (REQ-002): Alternative B's rejection rests only on backward offset movement and cites Decision 13; the rejection outcome is unchanged.
- `AC3` (REQ-003): Decision Detail 9 states the `since_seq` condition; ADR-006 carries a `**Current Decision Approval (pending)**` bullet citing `AAL-037`; `governance_03` Part 5 contains the `AAL-037` entry; no approver name or date is invented.
- `AC4` (REQ-004): the Index row reads that an equal or lower offset is accepted and the stored offset never moves backward.
- `AC5` (REQ-005): `grep` over `docs/10_adr/` finds no "single SQLite database" claim or "items to re-evaluate ... multi-DB configuration" line in ADR-005, ADR-006, or ADR-009.
- `AC6` (REQ-006): `grep` over `docs/10_adr/` finds no "privileges ... only within SQLite" statement in any ADR.
- `AC7` (REQ-007): `grep` finds no "- Changes to runtime behavior" line in ADR-001, ADR-002, or ADR-003.
- `AC8` (all): the docs and ADR checkers listed in the Validation plan exit 0; the `check_adr_preservation.py` scenario run is recorded with its expected findings.

## Tests
- Documentation-only (Issue Testing Expectations). No new pytest tests.
- `T1` (REQ-001..REQ-007): grep-based existence checks named in AC4-AC7 run after the edits.
- `T2` (all): the checker commands in the Validation plan (`rules/toolchain.md` sequence for a docs-only change).

## Documentation Impact
- Yes. The target ADRs and the Index themselves are the documentation being corrected; `docs/00_governance/governance_03_issue-and-uncertainty-management.md` gains the AAL-037 ledger entry. No additional guide or reference document requires editing; `check_docs_consistency.py` verifies no guide repeats a corrected claim.

## Assumptions
- Deleting the "Changes to runtime behavior" line (rather than rewording it) is the correct boilerplate fix: the line is generic template text contradicted by each ADR's Decision.
- Replacement wording cites ADR-008 only in ADR-006 (whose front matter `related` already lists it); ADR-005 and ADR-009 replacement text describes the current layout without naming new ADRs, because adding front matter `related` entries is itself a decision-text change (AAL-009 precedent).
- Alternative B keeps its rejection; only its Description/Reason wording changes.
- The Index Invariant Verification Matrix is hand-edited (AUTO-GENERATED guards end at line 153); the generated blocks (dependency graphs, lines 66-153) are not touched.
- ADR-006 Constraint "Events managed in a single SQLite database" (line 50) and Review Trigger "Persistent storage moves away from a single local SQLite database" (line 305) stay: they are accurate for the EventBus's own event store (`eventbus.sqlite`); the stale claims are the system-level Assumptions lines.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer ultimately approves the REQ-003 `since_seq` guarantee-condition text (pending amendment) | No maintainer decision recorded yet | Owner decision recorded via the governance_01 pending-amendment form against `AAL-037`; the Plan implements in pending form regardless | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | 18 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Low | 19 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Low | 22 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Low | 8 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Low | 6 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Low | 0 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Low | 0 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Low | 0 | N/A (git-fame not installed) | not applicable (rsynced) |

Churn from `git log --name-only --since=30.days -- docs/10_adr/ docs/00_governance/` (checked in Step 5).

## Design
- Path B classification rationale: 8 modification-target files (> 3), documentation-only; no public/runtime interface or schema change.
- Architecture analysis (docs graph): the Invariant Verification Matrix in `adr_01_index.md` restates ADR INV text and is cross-checked by `tools/check_adr_invariant_matrix.py`; ADR text is preserved-audited by `tools/check_adr_preservation.py` (scenario-gated, not wired to pre-commit/CI); `tools/check_adr_structure.py` rejects a pending-amendment bullet citing a nonexistent AAL entry — so the AAL-037 entry and the ADR-006 bullet are one change unit in Phase 2. ADR graph (Index lines 108-109): ADR-008 Governs ADR-006; ADR-013 Specializes ADR-006; the Index ownership table (lines 124-126) keeps `eventbus.persistence` owned by ADR-006, so no authority edge changes.
- Dependency graphing: no Python module imports a `docs/` file; consumers are the checker tools listed above plus `check_docs_structure.py` front matter `related:` coverage (replacement wording therefore avoids naming ADRs absent from each file's `related`). "These 8 files require changes" — no other file.
- Historical analysis: churn per `Affected areas`; `git log -S "admin and shared credentials have no Consumer-route bypass"` shows the 11b fix exists since at least `09e6bc93f` (2026-10-19), predating the Issue — confirming that claim is already resolved.
- Operational dependency inspection: docs-only change; no port, DB lock, or dependency-upgrade check applies (`ss`/`fuser`/`pip-audit` not run: nothing operational is touched).
- Consumer scan: N/A: no persisted schema, public API, or shared constant change.
- Validation quality baseline: `N/A: no Python target` (no `scripts/` or `tools/` row), so radon/vulture/bandit and the diff-cover baseline are not run per `workflow.md` Step 5.
- No deploy step: no `scripts/`/`config/` change (hand-off rule does not apply).

## Implementation steps
1. **Phase 1: ADR-006 verification-conflict and Alternative-B wording fixes**
   - [ ] Rewrite the Manual Review bullet so INV-06 is consistent with the Automated Tests table (keeps the INV-01 no-dedicated-test note) (REQ-001; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Update the Completion Checklist gap note to name only INV-01 (REQ-001; same file)
   - [ ] Clarify Alternative B so the rejection rests only on backward offset movement and cites Decision 13 (REQ-002; same file)
2. **Phase 2: Delivery-guarantee condition as a pending amendment**
   - [ ] Add the `AAL-037` entry after `AAL-036` in governance_03 Part 5 (re-confirm the current max AAL id first) (REQ-003; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] State the `since_seq` condition in Decision Detail 9 and add the matching `**Current Decision Approval (pending)**` bullet citing `AAL-037` in the Approval Record (REQ-003; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
3. **Phase 3: Stale boilerplate removal (single-DB and privileges statements)**
   - [ ] Restate ADR-006 Assumptions (single SQLite database, privileges, re-evaluate line) and the Security Consequences trust-boundary line (REQ-005, REQ-006; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Restate ADR-005 Constraints line 50, Assumptions lines 58/60/62, and the Security Consequences trust-boundary line 160 (REQ-005, REQ-006; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`)
   - [ ] Restate ADR-009 Assumptions lines 56/58/60 and the Security Consequences trust-boundary line 153 (REQ-005, REQ-006; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`)
4. **Phase 4: Out-of-Scope boilerplate in ADR-001/002/003**
   - [ ] Delete the "Changes to runtime behavior" line from each Out of Scope section (REQ-007; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
5. **Phase 5: Index Invariant Verification Matrix wording**
   - [ ] Reword the `ADR-006 INV-05, INV-09` row to match 11a/INV-09 (equal or lower offset accepted; stored offset never moves backward) (REQ-004; `docs/10_adr/adr_01_index.md`)
6. **Phase 6: Validation**
   - [ ] Run the checker sequence in the Validation plan and record results (all REQs; no file modified)
   - [ ] Run `check_adr_preservation.py` in its scenario mode and record expected WARNING/ERROR findings as intentional-signal notes (REQ-002, REQ-003, REQ-005, REQ-006)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| all 8 target docs | docs structural checks | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py` | No findings |
| ADR targets | ADR structure and pending-bullet ledger resolution | `uv run python tools/check_adr_structure.py` | No findings (pending bullet resolves to AAL-037) |
| `adr_01_index.md`, ADR Invariants | matrix/authority/reference consistency | `uv run python tools/check_adr_invariant_matrix.py`; `uv run python tools/check_adr_authority.py`; `uv run python tools/check_adr_reference.py` | No findings |
| `governance_03_issue-and-uncertainty-management.md` | ledger and identifier sync | `uv run python tools/check_known_deviation_sync.py`; `uv run python tools/check_needs_confirmation_inventory.py` | No findings (no new NC/UNK token is added) |
| domain claims (eventbus/rag/agent docs touched) | claim cross-check against config/scripts | `uv run python tools/check_docs_consistency.py --domain eventbus`, `--domain rag`, `--domain agent` | No findings |
| changed-file gate mapping | whole-diff gate discovery | `uv run python tools/run_validation_gates.py` | Pass |
| decision-text change audit (REQ-002/003/005/006) | preservation scenario run (manual, scenario-gated tool) | `uv run python tools/check_adr_preservation.py` with the changed-ADR scenario | WARNING/ERROR findings limited to the intended Decision/Alternatives/Assumptions text changes; recorded as expected signals |
| AC4-AC7 | grep existence checks | `grep -rn "only within SQLite\|multi-DB configuration\|Changes to runtime behavior" docs/10_adr/` and the Index row read-back | Only the corrected wording remains (AC5-AC7 satisfied) |
| this Plan | workitem structure | `uv run python tools/check_workitem_structure.py --file plans/20261120-155214_adrchk016_adr006-boilerplate-fixes.md` | No findings |

## Risks
- **Risk**: high churn on `adr_01_index.md` (22) and ADR-006 (18) in 30 days could collide with concurrent work → **Mitigation**: the open agentcfg001 batch's 19 procedures touch only `scripts/`, `config/`, `registry/manifests/`, and `docs/23_agent|22_mcp|91_security` files (verified from `implementations/20261120-132256_*` filenames); `check_plan_target_overlaps.py` runs after freeze.
- **Risk**: `check_adr_preservation.py` reports WARNING/ERROR on the intended Decision/Alternatives/Assumptions edits → **Mitigation**: run it as its scenario-gated tool and record the findings as expected signals; the tool is not wired to pre-commit/CI.
- **Risk**: AAL-037 id could collide with a concurrently added ledger entry → **Mitigation**: re-read the current max AAL id in governance_03 immediately before inserting.
- **Risk**: wording that names an ADR absent from a file's front matter `related` fails `check_docs_structure.py` coverage → **Mitigation**: replacement wording cites ADR-008/ADR-013 only in ADR-006 (already related); ADR-005/ADR-009 wording stays ADR-number-free.
- **Risk**: an edit could be read as writing a maintainer approval → **Mitigation**: use only the governance_01 pending-amendment form; Approver/Date stay "Not recorded".

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: ADR-006 INV-06 conflict and Alternative B wording | Completed | 20261120-155900 | 20261120-162500 | Manual Review now names INV-01 as the only invariant without a dedicated automated test and states that INV-06 has dedicated tests; Alternative B is rejected on backward offset movement and cites Decision Detail 13. The Completion Checklist gap lines are generic ("gaps: Verification > Manual Review") and name no invariant, so they needed no edit. |
| 2 | Phase 2: `since_seq` condition pending amendment + AAL-037 | Completed | 20261120-155900 | 20261120-162000 | AAL-037 inserted after AAL-036 (max id re-confirmed first), Approver and Date "Not recorded". The pending bullet is in ADR-006's Approval Record: this governance document has no Pending Amendments section, and the precedent is ADR-005's Approval Record. The condition is stated in Decision Detail 9 and in INV-07, which restates it in the Invariants section; editing only one of the two would create a new conflict in the same file, so the AAL-037 Scope names both. |
| 3 | Phase 3: boilerplate removal in ADR-006/005/009 | Completed | 20261120-155900 | 20261120-165000 | ADR-006 names ADR-008 and ADR-013, both already in its `related`. ADR-005 and ADR-009 wording stays ADR-number-free and uses the repository's existing trust-boundary phrasing pattern ("privileges are granted only within each process"): no HTTP authentication layer is documented for the RAG side, so the wording attributes privileges to the RAG layer's processes instead. |
| 4 | Phase 4: Out-of-Scope line removal in ADR-001/002/003 | Completed | 20261120-155900 | 20261120-160000 | "Changes to runtime behavior" deleted from each Out of Scope list. |
| 5 | Phase 5: Index matrix row wording | Completed | 20261120-155900 | 20261120-161500 | Row reworded to "EventBus offsets are non-decreasing (an equal or lower ACK offset leaves it unchanged)" in the hand-edited section; generated blocks untouched. The first wording pushed the file to 36641 bytes, over the 36609 ceiling in `tools/check_docs_structure.py`, so it was compacted; the neighbouring `ADR-006 INV-09` row already states that a lower-`seq` ACK leaves the offset unchanged. |
| 6 | Phase 6: validation and preservation signal recording | Completed | 20261120-162500 | 20261120-165500 | `check_docs_structure.py` (after the size fix), `check_docs_quality.py`, `check_docs_content_policy.py`, `check_adr_invariant_matrix.py`, `check_adr_authority.py`, `check_adr_reference.py`, `check_metadata_field_policy.py`, `check_db_separation.py`, `check_needs_confirmation_inventory.py`, `check_known_deviation_sync.py`: no findings. `check_adr_structure.py`: one pre-existing warning in `adr_02_07_015_docs-reference-document-class-disposition.md`, a file this batch does not touch. `check_docs_consistency.py --domain eventbus` and `--domain rag`: no findings; `--domain agent`: one pre-existing warning in `agent_14_reference-api-subpackages-generated.md`, untouched by this batch. `tools/check_domain_dependencies.py` named in the Implementation steps does not exist in `tools/`. `run_validation_gates.py` fast mode: all mapped gates Pass after the Status-vocabulary fix below. `check_adr_preservation.py --base HEAD`: 2 errors and 5 warnings, each mapping to an intended edit — ADR-001/002/003 `Decision` sections are the deleted Out-of-Scope bullet; ADR-006 `Decision` is the Alternative B rewording plus the Decision Detail 9 condition, `Invariants` is the INV-07 condition, and `Approval` is the new pending bullet. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261120-162706_01_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 1, 2, 3 | Procedure | Completed | — | — |
| implementations/20261120-162706_02_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261120-162706_03_docs_10_adr_adr_01_index.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261120-162706_04_docs_10_adr_adr_02_06_005_rag-source-derived-index-relationships.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261120-162706_05_docs_10_adr_adr_02_06_009_rag-fts5-text-separation.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261120-162706_06_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261120-162706_07_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261120-162706_08_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-155214
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/10_adr/adr_01_index.md`; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change; adr_006:249 vs 278 (checked in Step 2) | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | 1 | AC1 | T1/T2 checker runs; existing INV-06 tests cited | Confirmed by repository evidence |
| REQ-002 | Reason for Change; adr_006:133-139 vs 85 (checked in Step 2) | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | 1 | AC2 | T2 preservation scenario run | Confirmed by repository evidence |
| REQ-003 | Reason for Change; adr_006:76, 90-92; `subscribe_route.py:110-127` (checked in Step 2) | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | 2 | AC3 | T2 `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | governance_01 Pending Amendment Form; governance_03 Part 5 AAL-036 at line 666 (checked in Step 2) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | 2 | AC3 | T2 `check_adr_structure.py` | Explicit in issue |
| REQ-004 | Reason for Change; adr_01_index:199 vs adr_006:79 (checked in Step 2) | docs/10_adr/adr_01_index.md | 5 | AC4 | T1 read-back; T2 `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Reason for Change; adr_006:50/58/62, adr_005:50/58/62, adr_009:56/60; adr_008:2/134 (checked in Step 2) | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | 3 | AC5 | T1 grep | Confirmed by repository evidence |
| REQ-005 | adr_005:50/58/62 (checked in Step 2) | docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md | 3 | AC5 | T1 grep | Confirmed by repository evidence |
| REQ-005 | adr_009:56/60 (checked in Step 2) | docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md | 3 | AC5 | T1 grep | Confirmed by repository evidence |
| REQ-006 | Reason for Change; adr_006:60/176; `auth.py:80-90` (checked in Step 2) | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | 3 | AC6 | T1 grep; T2 `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-006 | adr_005:60/160 (checked in Step 2) | docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md | 3 | AC6 | T1 grep | Confirmed by repository evidence |
| REQ-006 | adr_009:58/153 (checked in Step 2) | docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md | 3 | AC6 | T1 grep | Confirmed by repository evidence |
| REQ-007 | Problem; adr_001:85, adr_002:107, adr_003:112 vs their Decision Details (checked in Step 2) | docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md | 4 | AC7 | T1 grep | Confirmed by repository evidence |
| REQ-007 | adr_002:107 vs 62-68 (checked in Step 2) | docs/10_adr/adr_02_01_002_platform-config-isolation.md | 4 | AC7 | T1 grep | Confirmed by repository evidence |
| REQ-007 | adr_003:112 vs 71-77 (checked in Step 2) | docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md | 4 | AC7 | T1 grep | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-162706 -->
