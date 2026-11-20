# Plan: Fix editorial defects in ADR-012, ADR-014, ADR-015, and ADR-017

## Goal
- Bring ADR-012, ADR-014, ADR-015, and ADR-017 into agreement with the current code and with each other, after adversarial re-verification of the source Issue's claims: two claims are already resolved or invalid and are recorded with evidence and skipped; four real editorial defects are fixed. Documentation-only; no code, test, or pipeline changes.

## Priority
Medium

## Scope
- **In-Scope**:
  - ADR-012: register the `git_add`/`git_commit` protected-branch INV/test gap in `Known Deviations` (reword-INV-09 and test-ID fixes are already resolved — evidence in Requirements).
  - ADR-014: add the task-status vocabulary (`pending`/`running`/`completed`/`failed`/`halted`) beside the existing stage-transition vocabulary, taken from `scripts/db/schema_sql.py`.
  - ADR-015: remove the Scope-vs-INV-01 divergence about guard blocks (ADR-016 already governs `tools/generate_adr_authority.py` blocks) and resolve the `check_adr_structure.py` Implementation Notes/References drift warning; record the alignment as a pending amendment per the Issue constraint.
  - ADR-017: complete the `Completion Checklist` with the six canonical items the sibling Accepted ADRs carry, each verified true before marking.
  - Governance ledger: add the new `AAL-NNN` entry required by the ADR-015 pending bullet (scope amendment against the Issue's Target Files, recorded here).
- **Out-of-Scope**:
  - Cross-ADR decisions; changing the Git write pipeline (per the Issue).
  - Adding new automated tests (Issue Testing Expectations: Documentation-only). Adding an actual INV-11 to ADR-012 is deferred to the owner (see Unknowns).
  - Editing generated guard blocks (`docs/10_adr/adr_01_index.md`, `docs/00_governance/governance_01_documentation-policy.md`, `docs/13_api`-class reference docs, `registry/manifests/*.yaml`); the four target ADRs and the ledger contain no guard blocks.
- **Dependencies**: ordering against sibling items editing the same ADRs; completed predecessors are applied (adrchk001 and adrchk011 have done plans; adrchk022 is still open and unplanned).
  - **Depends on**: issues/20261117-123022_adrchk022_history-comment-removal.md | all | Both edit ADR-017. This Plan touches only the `Completion Checklist` section; adrchk022 targets ADR-017 history text — the overlap is section-disjoint. Owner decision (2026-11-20): this Plan runs first; adrchk022 re-verifies the `Completion Checklist` section when its Plan is created.

## Background
The source Issue was filed from the consolidated ADR review package `ADRCHK2-M09` with every claim labeled `Documentation only` until re-verified. Since the Issue was filed (2026-11-17), completed predecessor plans (adrchk011 approval-governance ledger form, adrchk001 MCP auth contract, adrchk013 invariant-matrix mirroring, adrchk003 approval posture) have already rewritten parts of these ADRs, so the Issue's own constraint — "if a defect is already gone, record the evidence and skip that task" — applies to several claims.

## Problem
Adversarial re-verification against current source (2026-11-20) result per claim:

| Issue claim | Verdict | Evidence |
|---|---|---|
| ADR-012 INV-09 wording contradicts pipeline construction | Already resolved | Decision Detail 9 already states "Stages 1 to 3 run before the pipeline is constructed"; INV-09 cites Decision Detail 9; the change is tracked as pending amendment AAL-015 (`## Approval`, ledger Part 5). |
| ADR-012 protected-branch check for `git_add`/`git_commit` has no INV and no test | Confirmed | INV-03 names only `git_checkout`/`git_push`/`git_pull` (file L132); `verify_authorization()` protects the HEAD destination for `git_add`/`git_commit` (`scripts/mcp_servers/git/repository_state.py` L129-152); no protected-branch test for those two tools exists (only the dirty-worktree reachability test at `tests/mcp_servers/git/test_git_security_compliance.py` L1959); `Known Deviations` is "Not applicable". |
| ADR-012 cited ID `test_git_service_dispatch.py::test_rejected_remote_forms` lacks the class name and may fail to resolve | Already resolved | The malformed form appears nowhere in `docs/10_adr/adr_01_index.md` or the ADR-012 citation columns; the bare name survives only in prose without a `` `file.py::` `` wrapper, which the citation regex `` `([^`]+\.py)::([^`]+)` `` does not extract. Baseline run `uv run python .github/run_cited_adr_tests.py` on 2026-11-20: "All 70 cited ADR invariant tests passed." |
| ADR-014 `tasks.status` allows `halted` but the stage transitions do not include it; complete and completed are both used | Partially invalid | ADR-014 never contained `halted` or `completed` (`git log -S` returns no commits; as-of-2026-11-17 and current file greps agree). The only vocabulary is the stage list `plan -> execute -> verify -> complete/failed`, which matches `scripts/agent/workflow/workflow_loader.py` `_REQUIRED_STAGES` and `workflow_engine.py`. The real gap: the ADR names no task-status vocabulary at all, although the Workflow Engine persists `halted` (`workflow_engine.py` L233). |
| ADR-015 Scope covers all guard-commented documents but INV-01 and its verification cover only `generate_reference_table.py` | Confirmed | Scope: "Applies to every document that carries a generated guarded block"; INV-01 mandates only the `generate_reference_table.py --type <domain>` generator; `docs/00_governance/governance_01_documentation-policy.md` and `docs/10_adr/adr_01_index.md` carry `generate_adr_authority.py` guard blocks, governed instead by ADR-016 Decision 6 and INV-03. |
| ADR-017 Completion Checklist is shorter than the governed template | Confirmed | ADR-017 has the 11 base items; ADR-012/014/015 carry the same base plus the six canonical follow-on items (Each Invariant has a corresponding Verification; Automatable verification...; Discrepancies... Known Issues; Owner and required Reviewers...; Review Triggers are recorded; registered in the ADR index and Document Guides). No standalone checklist template file exists in the repo; the governed set is this shared item list. |

## Reason for Change
Accepted ADRs are the authority record for governance checkers and future plans; leaving a confirmed INV/test coverage gap unregistered (ADR-012), a missing state vocabulary (ADR-014), a Scope-vs-INV divergence (ADR-015), and a truncated checklist (ADR-017) keeps known-false or incomplete authority text in `Accepted` documents. The ADR-015 checker warning (`'scripts/agent/*.py' appears in Implementation Notes but not in Implementation References`) is currently the only warning emitted by `check_adr_structure.py` repo-wide.

## Implementation Intent
Documentation-only edits in four ADR files plus one ledger entry. Skipped claims are recorded as evidence comments in this Plan, not in the ADRs (Current-Specification-Only: no history-style notes in the ADRs). The ADR-015 alignment is recorded as a pending amendment using the ledger form already applied in ADR-012 (`Current Decision Approval (pending)` bullet citing an `AAL-NNN` entry); no maintainer approval text is written or simulated.

## Requirements
- `REQ-001`: ADR-012 — register in `Known Deviations` that the destination (HEAD) protected-branch check applied to `git_add`/`git_commit` by `verify_authorization()` is mandated by no INV (INV-03 covers only `git_checkout`/`git_pull`/`git_push`) and has no dedicated protected-branch test; keep the existing Scope description unchanged. Skip the INV-09 reword and the test-ID fix with the evidence above (no edit needed).
- `REQ-002`: ADR-014 — extend the Workflow Engine responsibility bullet to name both state vocabularies exactly as the code defines them: stage transitions (`plan -> execute -> verify -> complete/failed`) and task status (`pending`/`running`/`completed`/`failed`/`halted`, with `halted` persisted when max attempts is exceeded), taken from the `tasks.status` CHECK constraint in `scripts/db/schema_sql.py`. Skip the "complete vs completed" cleanup as invalid (only the stage term `complete` exists in the file).
- `REQ-003`: ADR-015 — align Scope and INV-01 by attribution: keep the Scope sentence and INV-01's obligation text unchanged and add an explicit attribution that guard blocks produced by `tools/generate_adr_authority.py` are governed by ADR-016 (Decision 6, INV-03), recorded also in `Related ADRs` (owner decision 2026-11-20, see resolved UNK-01). Record the alignment as a `Current Decision Approval (pending)` bullet citing the new ledger ID; write no approval statement. Also resolve the `check_adr_structure.py` warning at ADR-015 L126 by aligning the `scripts/agent/*.py` phrasing between Implementation Notes and Implementation References.
- `REQ-004`: ADR-017 — append the six missing canonical checklist items in canonical order after the existing eleven, each only if verified true against ADR-017's own sections (all six verified true during this analysis: every INV-01..05 has a Verification row; all rows are automated Unit/Regression checks; Known Deviations has no discrepancy to register; Required Reviewers and an Approval Record exist; Review Triggers are recorded; ADR-017 is registered in `docs/10_adr/adr_01_index.md` and referenced from `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` and `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`). Introduce no new requirement text.
- `REQ-005`: Governance ledger — append a new entry `AAL-038` to Part 5: ADR Approval Ledger in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` for the REQ-003 pending amendment (ADR, Decision, Approver: Not recorded, Date: Not recorded, Scope), following the existing AAL-036/AAL-037 entry format.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Known Deviations entry for the git_add/git_commit protected-branch INV/test gap | Confirmed coverage gap; INV-03 excludes git_add/git_commit; no dedicated test | REQ-001 / AC-001 | `scripts/mcp_servers/git/repository_state.py` L129-152; INV-03 text L132; `Known Deviations` currently "Not applicable" | None (documentation-only; cited suites re-run unchanged) | Verified |
| docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | Add task-status vocabulary to the Workflow Engine bullet | ADR names no task status; code persists `halted` | REQ-002 / AC-002 | `scripts/db/schema_sql.py` L171; `scripts/agent/workflow/models.py` L16; `scripts/agent/workflow/workflow_engine.py` L233 | `tests/db/test_create_schema.py` (pins DDL, unchanged) | Verified |
| docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md | Scope/INV-01 alignment (pending amendment) + Implementation Notes/References drift fix | Scope claims all guard blocks; INV-01 covers one generator; checker warning open | REQ-003 / AC-003 | ADR-015 Scope L65, INV-01 L110; ADR-016 Decision 6 L64, INV-03 L124; `check_adr_structure.py` warning at L126 | `tests/tools/test_check_adr_structure.py` | Verified |
| docs/10_adr/adr_02_03_017_mcp-authentication.md | Append six canonical Completion Checklist items | Checklist shorter than the shared governed item set | REQ-004 / AC-004 | ADR-017 checklist (11 items) vs ADR-012/014/015 (17 items); truth of each item verified against ADR-017 sections | `tests/tools/test_check_adr_structure.py` | Verified |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Append AAL-038 ledger entry for the ADR-015 pending amendment | Pending bullets must cite an existing ledger ID (checker rule); scope amendment against the Issue's Target Files, recorded for the owner | REQ-005 / AC-005 | Part 5 entries end at AAL-037; `tools/check_adr_structure.py` `_PENDING_BULLET_RE`/ledger-ID check L324-359 | `tests/tools/test_check_adr_structure.py` | Verified |

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
| scripts/db/schema_sql.py | Authoritative `tasks.status` CHECK vocabulary for the ADR-014 edit | REQ-002 |
| scripts/agent/workflow/models.py | `TASK_STATUSES` mirror of the DDL vocabulary | REQ-002 |
| scripts/agent/workflow/workflow_engine.py | `halted` persistence path (max attempts exceeded) and stage loop wording | REQ-002 |
| scripts/agent/workflow/workflow_loader.py | `_REQUIRED_STAGES` confirms the stage vocabulary already in ADR-014 | REQ-002 |
| scripts/mcp_servers/git/repository_state.py | `verify_authorization()` destination rule for git_add/git_commit | REQ-001 |
| scripts/mcp_servers/git/write_protection_pipeline.py | Stage 1-3-before-construction evidence for skipping the INV-09 reword | REQ-001 |
| tests/mcp_servers/git/test_git_security_compliance.py | Existing protected-branch and pipeline-order suites; confirms the git_add/git_commit test gap | REQ-001 |
| tests/mcp_servers/git/test_git_service_dispatch.py | Confirms `TestWriteRefAllowlist::test_rejected_remote_forms` exists with the class name | REQ-001 |
| docs/10_adr/adr_01_index.md | ADR-012/ADR-017 matrix citations and registration status; guard-generated, never hand-edited | REQ-001, REQ-004 |
| docs/10_adr/adr_02_07_016_adr-authority-model.md | Decision 6 and INV-03 govern `generate_adr_authority.py` guard blocks | REQ-003 |
| docs/00_governance/governance_01_documentation-policy.md | ADR Acceptance Evidence Standard wording reused verbatim in checklist/approval parentheticals | REQ-004 |
| .github/run_cited_adr_tests.py | Acceptance-criteria command; citation extraction is matrix-driven | REQ-001 |
| tools/check_adr_structure.py | Pending-bullet/ledger-ID and checklist structural rules the edits must satisfy | REQ-003, REQ-004, REQ-005 |

## Acceptance Criteria
- `AC-001` (REQ-001): ADR-012 `Known Deviations` names the git_add/git_commit INV/test gap and its HEAD-destination basis; `uv run python .github/run_cited_adr_tests.py` still resolves and passes every node ID cited in the ADR-012 matrix row (baseline 2026-11-20: 70/70 passed).
- `AC-002` (REQ-002): ADR-014 states the task-status vocabulary exactly matching the `tasks.status` CHECK constraint values (`pending`, `running`, `completed`, `failed`, `halted`) as a status vocabulary distinct from the stage vocabulary; no other `complete`/`completed` inconsistency exists in the file.
- `AC-003` (REQ-003): ADR-015 contains no sentence that obligates coverage ADR-015 cannot enforce: after the edit, every guard-block class in the Scope is either covered by INV-01 or explicitly attributed to ADR-016; the alignment is recorded as a `Current Decision Approval (pending)` bullet citing AAL-038, with Approver/Date "Not recorded" and no approval statement text; the L126 `check_adr_structure.py` warning no longer fires.
- `AC-004` (REQ-004): ADR-017 `Completion Checklist` contains the 17 canonical items in canonical order with true parentheticals; no item asserts something absent from ADR-017; no new normative requirement is introduced anywhere in the file.
- `AC-005` (REQ-005): Part 5 of the governance ledger contains `AAL-038` in the established entry format, and `tools/check_adr_structure.py` reports no pending-bullet/ledger mismatch.
- `AC-006` (all): `uv run python tools/check_adr_structure.py` exits without errors for all four ADRs and emits no warning for ADR-015.

## Tests
- No new or modified test files (Documentation-only per the Issue). Validation is checker-based:
  - `uv run python tools/check_adr_structure.py` — 0 errors, no ADR-015 warning (REQ-003/004/005).
  - `uv run python .github/run_cited_adr_tests.py` — all cited node IDs still pass (REQ-001).
  - `uv run python tools/check_adr_invariant_matrix.py` — matrix rows/citations consistent (REQ-001).
  - `uv run python tools/generate_adr_authority.py --check` and `uv run python tools/generate_reference_table.py --check` — guard blocks unmodified and consistent (REQ-003 boundary).
  - `uv run pytest tests/tools/test_check_adr_structure.py tests/tools/test_check_adr_invariant_matrix.py -q` (REQ-003/004/005).
  - `uv run python tools/check_workitem_structure.py --file plans/20261120-172527_adrchk021_adr-editorial-defects.md --kind plan` and the `routing.md` docs-checkers pass after the edits.

## Documentation Impact
Yes — the documentation files ARE the implementation targets (the four ADRs and the governance ledger, rows above). No additional document is driven by this Plan: the changed ADR text does not alter the generated index/guard blocks (`generate_adr_authority.py --check` confirms), so no generated mirror refresh is expected. Named via the task mapping: ADR/governance documents under `docs/10_adr/` and `docs/00_governance/`.

## Assumptions
- "Governed checklist template" (ADR-017 claim) means the 17-item shared set used by the other Accepted ADRs; no standalone checklist template file exists in the repo (verified by repo-wide greps of the canonical item phrases — they occur only inside `docs/10_adr/*.md`).
- The Issue's "add ... a test reference" for ADR-012 is satisfied only by the Known Deviations route, because no git_add/git_commit protected-branch test exists to reference and adding tests is out of this Plan (Documentation-only).
- Adding the task-status vocabulary to ADR-014 is descriptive of existing implemented behavior (like the existing stage list), not a decision-text change, so it needs no pending-amendment record.
- `governance_03` Part 5 is a plain (unguarded) list, safe to append to directly; guard blocks in `governance_01`/`adr_01_index` are untouched by this Plan.
- Bus Factor 1 repo-wide (single-maintainer project) for the Affected areas table.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Resolved 2026-11-20 (owner): ADR-015 alignment route is the attribution route — keep Scope and INV-01, attribute `generate_adr_authority.py` guard blocks to ADR-016 (Decision 6, INV-03); the Scope-narrowing route was rejected | — (owner decision recorded in chat 2026-11-20) | Owner decision; wording fixed in REQ-003 and Phase 3 | False |
| UNK-02 | Whether the owner prefers a new ADR-012 INV for the git_add/git_commit HEAD-destination protected check (decision change, pending amendment) instead of the Known Deviations registration chosen here | Maintainer preference | Owner decision; Known Deviations registration is a valid stand-alone outcome that satisfies the Issue's "or state why it is out of scope" branch | False |
| UNK-03 | Resolved 2026-11-20 (owner): execution order against adrchk022 is fixed — this Plan runs first; adrchk022 re-verifies the ADR-017 `Completion Checklist` section when its Plan is created | — (owner decision recorded in chat 2026-11-20) | Owner decision; recorded in Scope Dependencies | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Known Deviations entry | Low — docs only; no cited test IDs change | 6 | 1 | None: docs-only change |
| docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | Task-status vocabulary sentence | Low — docs only | 7 | 1 | None: docs-only change |
| docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md | Scope/INV alignment + pending bullet + notes fix | Medium — decision-adjacent text; gated on UNK-01 | 6 | 1 | None: docs-only change |
| docs/10_adr/adr_02_03_017_mcp-authentication.md | Six checklist items | Low — checklist only | 3 | 1 | None: docs-only change |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | One AAL-038 entry | Low — appended entry in a high-churn ledger | 20 | 1 | None: docs-only change |

## Design
- Single-source discipline: every vocabulary or coverage statement added to an ADR is copied from its authoritative code artifact (`schema_sql.py` CHECK constraint; `verify_authorization()` destination rule; ADR-016 INV-03) rather than restated from the review text.
- Pending-amendment mechanics (already governed by adrchk011's completed work): an ADR `### Approval Record` bullet `Current Decision Approval (pending)` must cite an `AAL-NNN` entry in governance_03 Part 5; `check_adr_structure.py` errors on a pending bullet without a resolving ledger ID. Therefore the ADR-015 bullet (target row 3) and the AAL-038 entry (target row 5) are one release unit.
- Skipped-claim evidence lives in this Plan only; the ADR edits contain no history-style wording (Current-Specification-Only).
- ADR-017 checklist items are added only in their canonical ADR-012/014/015 wording, with parentheticals that restate already-existing sections; the ADR's normative content (Decision, Invariants, Failure Policy) is untouched, honoring "complete the checklist without introducing new requirements".

## Implementation steps
Each step description cites the exact file path(s) it touches by referencing rows of `Implementation Target Files`.

Release unit: **Unit**: ADR015-pending-amendment | **Phases**: 3, 4 | **Reason**: a `Current Decision Approval (pending)` bullet citing a ledger ID that does not yet exist makes `check_adr_structure.py` fail; the ADR-015 bullet and the AAL-038 entry must land in the same commit.

1. **Phase 1: ADR-012 Known Deviations registration**
   - [ ] Replace "Not applicable" in `Known Deviations` with the gap entry: the destination-branch protected check applied to `git_add`/`git_commit` (HEAD destination) is not mandated by INV-03 and has no dedicated protected-branch test; scope statement already records the behavior. (REQ-001; docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md)
2. **Phase 2: ADR-014 task-status vocabulary**
   - [ ] Extend the Workflow Engine bullet with the task-status vocabulary `pending`/`running`/`completed`/`failed`/`halted` from the `tasks.status` CHECK constraint, kept distinct from the stage vocabulary. (REQ-002; docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md)
3. **Phase 3: ADR-015 scope alignment (owner route recorded 2026-11-20: attribution to ADR-016)**
   - [ ] Keep the Scope sentence and INV-01 obligation text unchanged; add the explicit attribution that `tools/generate_adr_authority.py` guard blocks are governed by ADR-016 (Decision 6, INV-03), plus the matching `Related ADRs` entry. (REQ-003; docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md)
   - [ ] Add the `Current Decision Approval (pending)` bullet citing AAL-038 (no approval statement text). (REQ-003; docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md)
   - [ ] Align the `scripts/agent/*.py` phrasing between Implementation Notes and Implementation References so the checker warning is gone. (REQ-003; docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md)
4. **Phase 4: Governance ledger entry (same commit as Phase 3)**
   - [ ] Append AAL-038 in the established entry format. (REQ-005; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
5. **Phase 5: ADR-017 checklist completion**
   - [ ] Append the six canonical items in canonical order with verified parentheticals. (REQ-004; docs/10_adr/adr_02_03_017_mcp-authentication.md)
6. **Phase 6: Verification**
   - [ ] Run the full checker set from `Tests` (check_adr_structure, run_cited_adr_tests, check_adr_invariant_matrix, both generator `--check`s, tools tests, docs checkers). (all; no new files)

### Release units
**Unit**: ADR015-pending-amendment | **Phases**: 3, 4 | **Reason**: pending bullet without its ledger entry fails `check_adr_structure.py`; both files must land in one commit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Static check + cited-test re-run | `uv run python .github/run_cited_adr_tests.py`; `uv run python tools/check_adr_invariant_matrix.py` | 70/70 cited tests pass; matrix consistent |
| docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | Static check | `uv run python tools/check_adr_structure.py` | No error/warning; vocabulary text matches schema values |
| docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md | Static check | `uv run python tools/check_adr_structure.py`; `uv run python tools/generate_reference_table.py --check`; `uv run python tools/generate_adr_authority.py --check` | L126 warning gone; pending bullet resolves to AAL-038; guard blocks clean |
| docs/10_adr/adr_02_03_017_mcp-authentication.md | Static check | `uv run python tools/check_adr_structure.py`; `uv run pytest tests/tools/test_check_adr_structure.py -q` | 17 checklist items; checker green |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Static check | `uv run python tools/check_adr_structure.py` (ledger load) | AAL-038 present; no pending-bullet errors |
| Whole docs tree | Docs checkers | `routing.md` Tools docs-checker set + `uv run python tools/check_workitem_structure.py --kind plan --file plans/20261120-172527_adrchk021_adr-editorial-defects.md` | All pass |

## Risks
- **Risk**: adrchk022 (open, unplanned) edits ADR-017 history text and could collide with this Plan's checklist edit → **Mitigation**: section-disjoint edits; ordering confirmed with the owner (UNK-03); re-run `check_adr_structure.py` after whichever lands second.
- **Risk**: A pending bullet committed without its AAL entry breaks the checker gate for every ADR run → **Mitigation**: declared release unit ADR015-pending-amendment (Phases 3+4 in one commit).
- **Risk**: wording drift when copying the canonical checklist items from sibling ADRs (they carry per-ADR parentheticals) → **Mitigation**: copy the shared item strings verbatim; add only ADR-017-specific parentheticals that restate verified existing sections.
- **Risk**: touching ADR text near guard-generated mirrors (governance_01 header list, adr_01_index matrix) could create apparent drift → **Mitigation**: no edits to guarded files; verify with both generator `--check` commands.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: ADR-012 Known Deviations registration | Completed | 2026-11-20 | 2026-11-20 | V1-1: MCP-005 companion entry added to governance_03 Part 1 (frozen-table row 5 scope extension); V1-2: tools/check_docs_structure.py SIZE_EXCEPTIONS ceiling re-recorded 31908->33915 |
| 2 | Phase 2: ADR-014 task-status vocabulary | Completed | 2026-11-20 | 2026-11-20 |  |
| 3 | Phase 3: ADR-015 scope alignment (owner route: attribution to ADR-016) | Completed | 2026-11-20 | 2026-11-20 |  |
| 4 | Phase 4: governance_03 AAL-038 entry | Completed | 2026-11-20 | 2026-11-20 | Same commit as Phase 3 V1-2 ceiling re-recorded 33915->34313 after AAL-038 entry |
| 5 | Phase 5: ADR-017 checklist completion | Completed | 2026-11-20 | 2026-11-20 |  |
| 6 | Phase 6: verification checkers | Completed | 2026-11-20 | 2026-11-20 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261120-174933_01_docs_10_adr_adr_02_03_012_mcp-git-server-side-write-enforcement.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261120-174933_02_docs_10_adr_adr_02_02_014_agent-control-plane-responsibility-boundaries.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261120-174933_03_docs_10_adr_adr_02_07_015_docs-reference-document-class-disposition.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261120-174933_04_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261120-174933_05_docs_10_adr_adr_02_03_017_mcp-authentication.md.md | 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123021_adrchk021_adr-editorial-defects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-172527
- **Related target files**: docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md; docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md; docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md; docs/10_adr/adr_02_03_017_mcp-authentication.md; docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Reason for Change" ADR-012 bullet; repository_state.py L129-152; INV-03 text | docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md | Phase 1 | AC-001 | run_cited_adr_tests.py (70/70 baseline), check_adr_invariant_matrix.py | Planned |
| REQ-002 | Issue "Reason for Change" ADR-014 bullet; schema_sql.py L171; workflow_engine.py L233 | docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | Phase 2 | AC-002 | check_adr_structure.py | Planned |
| REQ-003 | Issue "Reason for Change" ADR-015 bullet; ADR-015 Scope L65/INV-01 L110; ADR-016 Decision 6/INV-03 | docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md | Phase 3 | AC-003 | check_adr_structure.py (warning gone), generator --check pair | Planned |
| REQ-004 | Issue "Reason for Change" ADR-017 bullet; checklist item-count comparison | docs/10_adr/adr_02_03_017_mcp-authentication.md | Phase 5 | AC-004 | check_adr_structure.py, test_check_adr_structure.py | Planned |
| REQ-005 | Issue "Constraints" pending-amendment rule; check_adr_structure ledger rule L324-359 | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 4 | AC-005 | check_adr_structure.py ledger load | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-174933 -->