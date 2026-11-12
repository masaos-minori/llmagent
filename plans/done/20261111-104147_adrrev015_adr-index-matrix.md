## Goal
Make the ADR index and the ADR bodies agree exactly: correct the stale ADR-015 manifest status and generated-document list, the ADR-006 INV-13 wording and invariant-to-test mappings, the ADR-014 producer wording, ADR-001's Blocking flag on an unverified invariant, the index wording and row order, and add the one missing test that proves ADR-004 INV-14 (startup abort on an undefined component mandatoriness).

## Priority
Medium

## Scope
- **In-Scope**: Corrections to ADR-001, ADR-004, ADR-006, ADR-014, ADR-015, the ADR index, and the `agent_08_04` front matter; one new test of `_check_component_mandatoriness()` in `tests/agent/test_startup_validation.py`; the ADR-006 requeue-error wording; a recorded reason for the matrix membership of ADR-001 INV-02 and ADR-004 INV-11/INV-12; pending approval records for the decision-text edits.
- **Out-of-Scope**: Adding invariants to ADR-013 (EventBus authorization issue); the authority model, reference edges, and ADR format (the authority-format issue, which this work blocks); changing the requeue API's 409 text (a behavior question); adding a test for ADR-001 INV-02 (maintainer decision, UNK-02); creating an `adr_authority` manifest (maintainer decision, UNK-01); changing existing test behavior other than adding the INV-14 test; approval records for a maintainer.
- **Dependencies**: None to start. This Plan blocks the authority-format issue (adrrev016: authority model and ADR format), which needs a clean index. Sequencing notes: ADR-006 is also edited by the EventBus specification Plan (adrrev014) and the index is edited by other ADR Plans; the edits are to different sections (see Assumptions). Approval records for the amendments made here are tracked by the approval-ledger Plan (adrrev012).

## Background
The ADR index (`docs/10_adr/adr_01_index.md`) is a projection of the ADR bodies, whose Verification sections are the canonical evidence record. Verification (2026-11-11) confirmed: ADR-015 still says the `component_mandatoriness` manifest is deferred although `registry/manifests/component_mandatoriness.yaml` and `scripts/shared/component_mandatoriness.py` exist, and `agent_08_04` (a generated document, `mandatoriness` rendering) is neither in ADR-015's generated-document list nor carries `class: Reference`; ADR-006 INV-13 says "has exceeded max_retry" while its Implementation Notes, the code, and the cited test say `>= max_retry`; ADR-006's INV-04 and INV-07 rows cite tests that verify different invariants; the index says "strictly monotonic" while Decision 11a accepts equal offsets; three index rows are out of ADR order; ADR-014's Decision and INV-02 name different owners for `LlmTurnExecutor` creation; ADR-001's table lists INV-02 as Blocking with "Not verified", which the index rule forbids; and the ADR-004 INV-14 row cites only `required` default tests while the startup abort path is mocked in every `tests/agent` startup test. Memo claims refuted: ADR-004 INV-14's cited test does not "continue" where abort is required (it tests a different mechanism), and no index row combines "Not verified" with Blocking.

## Problem
- A projection that disagrees with its source misleads implementers and weakens the Blocking gates that rest on it; "exceeded" versus `>=` changes the DLQ boundary in a strict reading, and a mapping to the wrong invariant lets a regression of the claimed invariant pass.
- No test proves that startup aborts for an undefined mandatoriness, although ADR-004 INV-14 is a Deployment-Blocking gate.
- Stale deferred-manifest status and an incomplete generated-document list misdescribe the documentation pipeline.

## Reason for Change
Verification evidence is the basis of the Blocking gates; inaccurate evidence undermines them, and the authority-format work needs a clean index first.

## Implementation Intent
Correct the ADR body first (it is authoritative) through the amendment process, then bring the index into agreement, regenerating the guarded sections with the tool; add only the single test the INV-14 gate lacks.

## Requirements
- `REQ-001`: ADR-015 states the manifest status truthfully (`component_mandatoriness` is not deferred; `architecture_assumptions` remains deferred; `adr_authority` per the maintainer's answer to UNK-01), and lists `agent_08_04` among the generated documents; `agent_08_04` declares `class: Reference`.
- `REQ-002`: ADR-006 INV-13 says promotion happens when every attempting consumer's failure count has reached `max_retry` (`>=`), agreeing with its Implementation Notes, the code, and the cited test.
- `REQ-003`: ADR-006's Automated Tests rows verify the invariants they claim: the restart-resume tests for INV-04, the unacked-replay test for INV-07, and the publish-retry idempotency tests re-mapped to the invariant they actually verify (INV-06, Event IDs for idempotent processing); the requeue paragraph names the API's HTTP 409 error text, not only the internal status.
- `REQ-004`: ADR-014 names one producer: `Orchestrator` constructs the single `LlmTurnExecutor` in both the Decision and INV-02, with the WorkflowEngine side as the logical owner of the loop.
- `REQ-005`: A test exercises `_check_component_mandatoriness()` unmocked and proves a fatal for an unknown configured server and for a missing or invalid registry; ADR-004's INV-14 verification text and the index row cite it (and the registry tests) alongside the default tests.
- `REQ-006`: ADR-001's INV-02 row is no longer both Blocking and "Not verified" (set to Non-Blocking unless the maintainer supplies a test, UNK-02).
- `REQ-007`: The index says "non-decreasing" for the ADR-006 INV-05/INV-09 row, fixes the three out-of-order rows, records why ADR-001 INV-02 and ADR-004 INV-11/INV-12 are not matrix rows, and the guarded sections are regenerated with `tools/generate_adr_authority.py`; the index checks report no mismatch.
- `REQ-008`: Each decision-text edit (ADR-001, ADR-004, ADR-006, ADR-014, ADR-015) carries a clearly marked pending approval record; none is written on a maintainer's behalf.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/agent/test_startup_validation.py` | Modify | Add unmocked tests of `_check_component_mandatoriness()` (unknown server; missing or invalid registry) (433 lines) | REQ-005 / AC-5 | `_check_component_mandatoriness` at `scripts/agent/startup_validation.py:67` adds fatals for an unknown server and a missing registry; every existing test patches it with a `MagicMock` (lines 61, 104, 215, 345) (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify | Rewrite the deferred-manifest sentence (line 133) and add `agent_08_04` to the generated-document list (lines 121-123) | REQ-001, REQ-008 / AC-1 | Line 133 "Deferred manifests (`component_mandatoriness`, `adr_authority`, `architecture_assumptions`) ... when their source modules land"; `registry/manifests/component_mandatoriness.yaml` and `config/adr_authority.toml` exist, `architecture_assumptions` only in `schemas/contract_manifest.json` (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_docs_structure.py` | Verified |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Modify | Add `class: Reference` to the front matter (front matter only) | REQ-001 / AC-1 | Front matter at lines 1-14 has no `class:`; the other five generated documents have it; `tools/generate_reference_table.py:108` targets this file (checked in Step 2) | `tools/check_docs_structure.py`, `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | INV-13 wording (line 186), INV-04/INV-07 test mapping and the publish-retry row (lines 232, 240), requeue paragraph (line 276) | REQ-002, REQ-003, REQ-008 / AC-2, AC-3 | INV-13 "has exceeded max_retry" versus Implementation Notes line 273 `>= max_retry`; `dlq.py` `_PROMOTABLE_CONDITION` blocks at `< max_retry`; rows at lines 232 and 240 (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Name `Orchestrator` as the creator in INV-02 and the Decision (lines 58, 128) | REQ-004, REQ-008 / AC-4 | Line 58 "logical owner ... is the WorkflowEngine side ... `Orchestrator` is the construction owner"; INV-02 "the one component that actually drives the ... loop"; single construction site `scripts/agent/orchestrator.py:121` (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | INV-14 verification text (line 289) to cite the startup-abort and registry tests | REQ-005, REQ-008 / AC-5 | Line 291 (the Plan's line 289 drifted by two) cites only `TestRequiredDefault` (checked in Step 3a) | `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | INV-02 row (line 190): Blocking "Yes" with "Not verified" becomes Non-Blocking | REQ-006, REQ-008 / AC-6 | Line 190 "Regression \| Yes \| Not verified (no automated test asserts ...)"; the index states a "Not verified" row is Non-Blocking (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | "non-decreasing" wording, ADR-004 INV-14 row evidence, three row moves, matrix-membership note, regenerate guarded sections | REQ-005, REQ-007 / AC-5, AC-7 | Rows 13/14-15, 29/30, 31/32 out of ADR order; row "ADR-006 INV-05, INV-09 \| EventBus offsets strictly monotonic"; ADR-004 INV-14 row cites `TestRequiredDefault` (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/generate_adr_authority.py --check`, `tools/check_adr_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/startup_validation.py` | `_check_component_mandatoriness()` behavior the new test exercises | REQ-005 |
| `scripts/shared/component_mandatoriness.py` | `load_component_mandatoriness()` errors and `UnknownComponentError` | REQ-005 |
| `scripts/agent/production_config_validator.py` | `validate_against_registry()` messages for conflict and unknown server | REQ-005 |
| `tests/shared/test_component_mandatoriness.py` | Existing `UnknownComponentError` tests the ADR-004 text will cite | REQ-005 |
| `tests/shared/test_mcp_config.py` | `TestRequiredDefault`: default `required` tests, left unchanged | REQ-005 |
| `scripts/eventbus/dlq.py` | `_PROMOTABLE_CONDITION` (`>= max_retry` boundary) | REQ-002 |
| `scripts/eventbus/dlq_repo.py` | `already_redelivered` repository status | REQ-003 |
| `scripts/eventbus/dlq_route.py` | The route's HTTP 409 mapping and text | REQ-003 |
| `scripts/eventbus/route_helpers.py` | `ERR_EVENT_NOT_IN_DLQ` text | REQ-003 |
| `tests/eventbus/test_eventbus_restart_resume.py` | Candidate evidence for ADR-006 INV-04 | REQ-003 |
| `tests/eventbus/test_eventbus_crash_ack.py` | Unacked-replay test for ADR-006 INV-07 | REQ-003 |
| `scripts/agent/orchestrator.py` | Single construction site of `LlmTurnExecutor` | REQ-004 |
| `tools/generate_reference_table.py` | `mandatoriness` rendering target for `agent_08_04` | REQ-001 |
| `tools/check_adr_invariant_matrix.py` | Index-versus-body rules that report mismatches | REQ-007 |
| `docs/00_governance/governance_02_documentation-metadata.md` | Defines the `class:` front-matter field | REQ-001 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | An ADR edit that changes the decision needs a new approval record in the same change | REQ-008 |

## Acceptance Criteria
- AC-1: ADR-015 no longer calls `component_mandatoriness` deferred, lists `agent_08_04` as generated, and `agent_08_04` declares `class: Reference`; `generate_reference_table.py --check` still passes (`REQ-001`).
- AC-2: ADR-006 INV-13 text, Implementation Notes, and the cited test agree on `>= max_retry` (`REQ-002`).
- AC-3: Each ADR-006 test row verifies the invariant it names; the requeue paragraph names the API's 409 text (`REQ-003`).
- AC-4: ADR-014's Decision and INV-02 name the same producer (`REQ-004`).
- AC-5: A test fails if `_check_component_mandatoriness()` stops adding a fatal for an unknown server or a missing registry, and ADR-004 and the index cite it (`REQ-005`).
- AC-6: No ADR table row is both Blocking and "Not verified" (`REQ-006`).
- AC-7: The index checks report zero mismatches (`check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_adr_authority.py`, `generate_adr_authority.py --check`), and the wording and row order are corrected (`REQ-007`).
- AC-8: `check_adr_preservation.py` reports only the intended decision-text changes, each explained, and each has a marked pending approval record (`REQ-008`).
- AC-9: `check_docs_structure.py` and `check_docs_content_policy.py --strict` pass; `uv run pytest tests/agent/test_startup_validation.py tests/shared/test_mcp_config.py tests/shared/test_component_mandatoriness.py tests/eventbus -v` passes.

## Tests
- `REQ-005` (new, `tests/agent/test_startup_validation.py`): with the real `_check_component_mandatoriness` and a configured server absent from the registry, the pipeline holds a fatal under the `component_mandatoriness` source; with `load_component_mandatoriness` raising `ComponentMandatorinessError` or `FileNotFoundError`, the pipeline holds the "Undeterminable component mandatoriness" fatal; with a consistent registry no fatal is added. Written first and shown to fail against a deliberately broken check.
- Existing tests, including `tests/shared/test_mcp_config.py::TestRequiredDefault` and the cited EventBus tests, run unchanged.
- Documentation requirements are verified by the checkers in the Validation plan.

## Documentation Impact
ADR-001, ADR-004, ADR-006, ADR-014, ADR-015, the ADR index, and the `agent_08_04` front matter, located through `docs/00_index.md` "Document References by Task" (governance, agent, eventbus areas). State intent and verification status; do not copy test code or configuration values. Write in English.

## Assumptions
- The ADR body is authoritative, so the index follows the ADR (the index is never edited alone to match a memo).
- Publish-retry idempotency tests map to INV-06 (Event IDs assigned so consumers can process idempotently) because INV-07 is the at-least-once baseline; if the maintainer prefers another invariant, only the row mapping changes (UNK-03).
- ADR-001 INV-02 becomes Non-Blocking (the index rule: a gate cannot be enforced without verification) unless the maintainer supplies a test (UNK-02); no new Blocking matrix rows are created for ADR-004 INV-11/INV-12 because the ADR records them as Non-Blocking, and the index records the reason.
- Overlap judgment (`tools/check_plan_target_overlaps.py`): ADR-006 is also targeted by the EventBus specification Plan (adrrev014: Scope, Data Ownership, `/replay` contract), and `docs/10_adr/adr_01_index.md` is also targeted by the MCP audit and authentication Plan (adrrev011: it adds the ADR-017 row and the authority sections, while this Plan edits other rows); compatible, because this Plan edits INV-13, the test rows, and the requeue paragraph of ADR-006 and different sections elsewhere.
- Step 3a (2026-11-12): re-verified against current source; the claims hold. ADR-006 INV-04 currently cites the unacked-replay test and INV-07 the publish-retry tests, as the Plan states; ADR-001 INV-02, ADR-014 INV-02, and ADR-015 text match. The new test node id is `tests/agent/test_startup_validation.py::TestComponentMandatorinessAbort`. `tests/agent/test_startup_validation.py` is also targeted by `rmcompat003` (a different region, compatible).
- Keeping the invariant numbers stable: no invariant is renumbered, so index citations by `ADR-NNN INV-NN` stay valid.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an `adr_authority` registry manifest is wanted, or ADR-015's deferred sentence should drop it | `config/adr_authority.toml` exists, no manifest does; no maintainer decision | Maintainer decides; until then ADR-015 states that the source landed and no manifest is produced | False |
| UNK-02 | Whether ADR-001 INV-02 should stay Blocking by adding an automated test | An automated test that no external state-change path bypasses the Workflow Engine does not exist and its design is open | Maintainer decides; this Plan makes the row Non-Blocking and a separate issue can add the test | False |
| UNK-03 | Which invariant the publish-retry idempotency tests should verify (INV-06 assumed) | Wording of INV-06 versus the tests was read, not confirmed by the maintainer | Maintainer confirms at approval; only the mapping changes | False |
| UNK-04 | Maintainer approval statements for the five ADR decision-text edits | Approver, date, and scope are `不明` | Write marked pending records and report them; the ledger Plan tracks them | False |
| UNK-05 | Whether `check_adr_invariant_matrix.py` reports further index-versus-body mismatches beyond those found | The tool was not run in this review | Run it in Phase 1 and Phase 4; add any extra mismatch row through `tools/amend_plan.py` (fallout class) | False |
| UNK-06 | Whether `tests/agent/test_startup_validation.py` can build the unmocked `AgentContext` cheaply | Existing fixtures were read only for mocking | Use a minimal context stub as the other tests in the file do; if not feasible, put the test beside `tests/agent/test_startup.py` by plan amendment | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/agent/test_startup_validation.py` | Modify | Low | 7 | N/A | not applicable (tests are not deployed) |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify | Medium (ADR graph and index consumers) | 3 | N/A | not applicable (docs) |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Modify | Low (front matter only; generated block untouched) | 11 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Medium | 3 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium | 7 | N/A | not applicable (docs) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (generated sections, CI-checked, high churn) | 29 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files, ADR amendments across six ADRs, one new test). Findings from the inspection:
- Architecture: the only code-adjacent change is a test in the `tests/agent` startup module; `scripts/` is not modified. No import or layering change.
- Dependency graph: the ADR index cites ADR invariants by number and tests by node id; `check_adr_invariant_matrix.py` verifies that cited paths and nodes exist and reads ADR bodies for further rules; no invariant is renumbered, so no citation breaks.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: none (no process, port, or database involved). Persisted schema: not applicable. Consumer scan: no persisted schema, public API, or shared constant changes (`not affected`).
- Ordering inside the change: ADR bodies first, the index after, then `generate_adr_authority.py` and the checkers, so the index never disagrees with an unamended body.
- The new test is justified because ADR-004 INV-14 is a Deployment-Blocking gate: without an unmocked test, the gate's abort path could regress while every cited test passes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Startup-abort test for ADR-004 INV-14** (REQ-005; `tests/agent/test_startup_validation.py`)
   - [ ] Run `uv run python tools/check_adr_invariant_matrix.py` first and record the baseline (UNK-05).
   - [ ] Write the unmocked tests first and show them failing against a deliberately broken check, then passing.
   - [ ] Run `uv run pytest tests/agent/test_startup_validation.py tests/shared/test_component_mandatoriness.py tests/shared/test_mcp_config.py -v`.
2. **Phase 2: ADR-015 and the generated document** (REQ-001, REQ-008; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`)
   - [ ] Rewrite the deferred-manifest sentence and add `agent_08_04` to the generated-document list; add a pending approval record.
   - [ ] Add `class: Reference` to the `agent_08_04` front matter and run `generate_reference_table.py --check`.
3. **Phase 3: ADR bodies** (REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-008; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`)
   - [ ] ADR-006: INV-13 to `>= max_retry` wording; INV-04, INV-07, and publish-retry test rows; the requeue paragraph; pending approval record.
   - [ ] ADR-014: name `Orchestrator` in the Decision and INV-02; pending approval record.
   - [ ] ADR-004: INV-14 verification text cites the new test and the registry tests; pending approval record.
   - [ ] ADR-001: INV-02 row becomes Non-Blocking; pending approval record.
4. **Phase 4: Index and generated sections** (REQ-007; `docs/10_adr/adr_01_index.md`)
   - [ ] "non-decreasing" wording; ADR-004 INV-14 row evidence; move the three out-of-order rows; record the matrix-membership reason.
   - [ ] Run `uv run python tools/generate_adr_authority.py`, then `--check`, then the ADR checkers; resolve any extra mismatch (UNK-05).
5. **Phase 5: Verification** (all target files)
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence.
   - [ ] Run `check_adr_preservation.py` and explain every reported decision change; report the pending approvals (approver, date, scope as `不明`) and write none.
   - [ ] No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup_validation.py` | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/shared/test_component_mandatoriness.py tests/shared/test_mcp_config.py tests/eventbus -v` | Pass |
| Python test file | Format, lint, type | `uv run ruff format tests/agent/test_startup_validation.py`, `uv run ruff check tests/agent/test_startup_validation.py`, `uv run mypy tests/agent/test_startup_validation.py` | Clean |
| `tests/agent/test_startup_validation.py` | Mock patch targets | `uv run python tools/check_mock_patch_targets.py` | Pass |
| ADR index and bodies | Cited tests exist; index versus body | `uv run python tools/check_adr_invariant_matrix.py` | Pass, zero mismatches |
| ADR files | Structure and authority | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `generate_adr_authority.py --check` | Pass |
| ADR files | Decision-change guard | `uv run python tools/check_adr_preservation.py` | Only the intended, explained changes |
| Generated documents | Guarded block drift | `uv run python tools/generate_reference_table.py --check` | No drift |
| ADR and agent docs | Structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| ADR files | Reference and deviation sync | `uv run python tools/check_adr_reference.py`, `check_known_deviation_sync.py` | Pass |

Validation quality baseline: `N/A: no Python target under scripts/ or tools/` (the only Python file is a test file).

## Risks
- **Risk**: Rewording ADR-006 INV-13 or changing ADR-001's Blocking flag is read as changing an accepted decision. → **Mitigation**: INV-13's edit makes the text agree with the code and its own Implementation Notes; the ADR-001 edit applies the index's existing rule; both are labelled corrections with marked pending approval records, and `check_adr_preservation.py` output is explained.
- **Risk**: Re-mapping tests to another invariant weakens evidence for the original. → **Mitigation**: Only mappings that the invariant text supports are moved; INV-12 and INV-14 stay with their documented limits.
- **Risk**: The unmocked startup test is brittle or depends on the real registry file. → **Mitigation**: Patch `load_component_mandatoriness` and use a minimal context stub; assert the fatal's source label and message only.
- **Risk**: Regenerating the guarded sections of the high-churn index conflicts with other ADR Plans. → **Mitigation**: Use `tools/generate_adr_authority.py` rather than hand edits; rerun `check_plan_target_overlaps.py`.
- **Risk**: Moving rows in the index drops a row. → **Mitigation**: Count rows before and after; the invariant-matrix checker verifies cited nodes.
- **Risk**: A decision-text edit lacks an approval record. → **Mitigation**: Marked pending records, reported, never fabricated (UNK-04).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Startup-abort test for ADR-004 INV-14 (REQ-005) | Completed | — | 20261112-170344 |  |
| 2 | ADR-015 and the generated document (REQ-001, REQ-008) | Completed | — | 20261112-170503 |  |
| 3 | ADR bodies (REQ-002 to REQ-006, REQ-008) | Completed | — | 20261112-173649 |  |
| 4 | Index and generated sections (REQ-007) | Completed | — | 20261112-173649 |  |
| 5 | Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261112-123307_01_tests_agent_test_startup_validation.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261112-123307_02_docs_10_adr_adr_02_07_015_docs-reference-document-class-disposition.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261112-123307_03_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261112-123307_04_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261112-123307_05_docs_10_adr_adr_02_02_014_agent-control-plane-responsibility-boundaries.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261112-123307_06_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261112-123307_07_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261112-123307_08_docs_10_adr_adr_01_index.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-104147
- **Related target files**: `tests/agent/test_startup_validation.py`, `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_01_index.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: update the ADR-015 manifest status and generated-document list | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Step 2 | AC-1 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes: add `class: Reference` to `agent_08_04` | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Step 2 | AC-1 | `check_docs_structure.py`, `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Required Changes: ADR-006 INV-13 to `>= max_retry` | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 3 | AC-2 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: fix the ADR-006 test mapping (INV-04, 07, 12, 14) and the requeue error name | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 3 | AC-3 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: ADR-014 single producer in Decision and INV-02 | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Step 3 | AC-4 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: make the ADR-004 INV-14 verification prove an abort | `tests/agent/test_startup_validation.py` | Step 1 | AC-5 | `uv run pytest tests/agent/test_startup_validation.py -v` | Derived from confirmed evidence |
| REQ-005 | Same; ADR-004 INV-14 verification text | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Step 3 | AC-5 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Same; index row evidence | `docs/10_adr/adr_01_index.md` | Step 4 | AC-5 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes: ADR-001 INV-02 as Blocking or record why not; no row combines "Not verified" with Blocking | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Step 3 | AC-6 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes: "non-decreasing", row order, matrix membership of ADR-004 INV-11/12 | `docs/10_adr/adr_01_index.md` | Step 4 | AC-7 | `generate_adr_authority.py --check`, `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-008 | Constraints: ADR amendments need approval records; the implementer must not fabricate approvals | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Step 5 | AC-8 | `check_adr_preservation.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261112-123307 -->
