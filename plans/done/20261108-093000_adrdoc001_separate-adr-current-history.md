## Goal
- State once, in the documentation policy, what ADRs and the other document classes are responsible for and how a current decision is told apart from amendment history, then apply that rule minimally to the ADRs where the current contract is incomplete or an amendment is unmarked, without a wholesale rewrite or relocation.

## Priority
Low

## Scope
- **In-Scope**: one new rule in `docs/00_governance/governance_01_documentation-policy.md` (ADR responsibilities, current-versus-historical marking, relocation rule); a pointer in `docs/10_adr/adr_00_document-guide.md`; making the ADR-001 current contract complete and its stale pointer correct; marking the ADR-010 Amendment per the rule.
- **Out-of-Scope**: architectural redesign; unrelated editorial changes; new registries; relocating any ADR content (no maintenance benefit is demonstrated at planning time, see UNK-02); changing `config/documentation_canonical_sources.toml`; ADR-015 and ADR-016 text (they stay references so no competing normative source arises); ADR-008 text, whose Amendment is already marked superseded.
- **Dependencies**: this Plan is performed after the contract corrections, as the Issue requires; authority-related wording is coordinated with the `adrauth001` Plan, with no required order between them. The Plans for `adrver001`, which also edits ADR-010, and this Plan have no required order.
  - **Depends on**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md | phase all | ADR-010 corrections must be complete before the ADR-010 Amendment is marked.
  - **Depends on**: plans/20261108-091719_adrrag002_reconcile-adr-010-contract.md | phase all | it adds the ADR-010 Amendment record that this Plan marks.
  - **Depends on**: plans/20261108-092007_adrdb001_clarify-adr-008-scope.md | phase all | ADR-008 historical marking and the amendment-to-approval mapping must exist before the general rule is written.
  - **Depends on**: plans/20261108-092140_adrcfg001_clarify-adr-002-isolation.md | phase all | the Issue requires the High and Medium contract corrections to finish first.

## Background
Verified against the current documents and checkers (checked in Step 2):
- The documentation policy `docs/00_governance/governance_01_documentation-policy.md` defines six document classes (Governance, Guide, Reference, Operations, Note, Known Issues, L47-L58). ADR is not a class there, and the Claim Type Taxonomy states that no per-area `*_specification.md` document is maintained (L74), so the Issue's "specification" class does not exist; functional requirements live in Accepted ADRs or in sources registered in the Canonical Source Registry. `adr_00_document-guide.md` (Guide class, 5087 bytes) states the directory purpose but no responsibilities, and ADR-015 covers only the Reference class.
- The same policy's Current-Specification-Only Policy (L22-L45) says the active set does not retain superseded specifications, migration history or change history, and that removal of such historical content is a separate, later change after any still-applicable requirement is transferred. `governance_02_documentation-metadata.md` (L53-L55) removes a document that would need `superseded` from the active set instead of marking it, and `config/doc_quality_rules.json` rule `history_marker_in_active_doc` rejects, as ERROR, `(Added <date>` annotations, `issues/`, `plans/` and `implementations/` `done/` paths, `REQ-NNN` identifiers, `Resolved` bullets, strikethrough and `Traceability` headings in active documents. The Issue's intent to keep amendments as marked history therefore conflicts with the current policy and needs an owner decision (UNK-01).
- Three ADRs carry an Amendment subsection, not two: ADR-001 (wflease001, L58), ADR-008 (dbmig001, L73) and ADR-010 (ragcorpus001, L80). They are marked inconsistently: ADR-008's states "Superseded 2026-11-07 ... retained as historical record only"; ADR-001's and ADR-010's carry no marker.
- ADR-001's current contract is not complete without its Amendment: INV-07 (L175) says interrupted Attempts are recovered as `failed`, and the definition of "interrupted" by lease expiry exists only in the Amendment (L58-L60). Its Amendment also cites `plans/20261030-114516_wflease001_stale-attempt-lease.md`, which is now under `plans/done/` (stale pointer).
- `governance_01` is 21530 bytes and `adr_00_document-guide.md` 5087 bytes, both within the 24576-byte default limit and passing `check_docs_structure.py` (Operationally observed), so the additions fit if they stay concise.
- The ADR Change Protocol (L293-L298) already says an edit that does not change the decision does not reopen approval and that a decision change needs a new approval record in the same change; it says nothing about marking amendments.

## Problem
Readers must reconstruct the current contract from amendments: ADR-001's current definition of an interrupted Attempt sits only in an Amendment, and two of three Amendments are not marked as in force or superseded. No document states ADR responsibilities or the historical-content rule for ADRs, and the policy that does exist conflicts with retaining amendment history at all.

## Reason for Change
Clear responsibilities reduce stale-requirement risk as ADRs grow. It is Low because it is a maintainability improvement with no confirmed defect, and it must follow the contract corrections to avoid rework.

## Implementation Intent
Make the smallest change that removes ambiguity. Add one rule to the policy document, where classes and ADR conventions already live, and have the Guide point to it. Keep decisions, rationale, alternatives, invariants and verification in the ADR; keep every current-contract section complete without its Amendment; mark each Amendment as in force or superseded; relocate content only when a maintenance benefit is shown and a single owner exists. The rule's treatment of retained amendment history follows the owner's decision on how it relates to the Current-Specification-Only Policy; the recommendation is to name ADR Amendment subsections as the one sanctioned form of retained decision history, because they carry rationale and approval traceability that the Issue requires, and to forbid any current requirement living only in an Amendment.

## Requirements
- `REQ-001`: `governance_01` states the responsibilities of ADRs (decisions, rationale, alternatives, core invariants and their verification) relative to the existing document classes and the Canonical Source Registry, notes that no specification class exists, and does not restate ADR-015 or ADR-016 rules.
- `REQ-002`: `governance_01` defines how an ADR distinguishes a current decision from history: every current-contract section is complete without its Amendment, and an Amendment is marked in force (it only records rationale of text already in the current sections) or superseded (historical record only); the rule names its relationship to the Current-Specification-Only Policy as the owner decides.
- `REQ-003`: `governance_01` states the relocation rule: content moves out of an ADR only when a maintenance benefit is demonstrated, the destination has exactly one authoritative owner, and essential safety or recovery guarantees stay in the ADR even when detailed.
- `REQ-004`: ADR-001's Decision Details define "interrupted Attempts" by lease expiry so INV-07 is complete without the Amendment; invariant text is unchanged; the Amendment is marked in force and cites its plan by identifier only.
- `REQ-005`: The ADR-010 Amendment is marked per the rule without losing its rationale, after the ADR-010 corrections of the dependency Plans.
- `REQ-006`: `adr_00_document-guide.md` points to the `governance_01` rule in a single sentence without restating it.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Documentation policy (document classes, ADR conventions) | Add the ADR responsibilities, current-versus-historical marking and relocation rule | `REQ-001`, `REQ-002`, `REQ-003` / AC-01, AC-02, AC-03 | Classes at L47-L58, no specification class at L74, Current-Specification-Only Policy at L22-L45, ADR Change Protocol at L293-L298 (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` (checkers, run unchanged) | Verified |
| `docs/10_adr/adr_00_document-guide.md` | ADR directory guide (Guide class) | Add a one-sentence pointer to the policy rule | `REQ-006` / AC-06 | Sections at L15-L96 contain no responsibility or historical-content statement (checked in Step 2) | `tools/check_docs_structure.py` (checker, run unchanged) | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | ADR-001 | Move the "interrupted Attempts" definition into Decision Details, mark the Amendment in force, replace the stale plan path by an identifier | `REQ-004` / AC-04 | INV-07 at L175 versus the Amendment at L58-L60; the cited plan now under `plans/done/` (checked in Step 2) | `tests/agent/workflow/test_stale_recovery_lease.py` (existing, run unchanged) | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | ADR-010 | Mark the Amendment per the rule | `REQ-005` / AC-05 | Amendment at L80-L82 carries no marker (checked in Step 2) | `tools/check_adr_structure.py` (checker, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_02_documentation-metadata.md` | States that a document needing `superseded` is removed from the active set (L53-L55) | `REQ-002` |
| `docs/00_governance/governance_04_documentation-checks.md` | Describes the change-history rejection rules the new text must not trip (L41) | `REQ-002`, `REQ-004` |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Defines whether a policy edit needs approval ("Reading the Approval Required Column", L64) | `REQ-001` |
| `config/doc_quality_rules.json` | Holds the `history_marker_in_active_doc` rule | `REQ-002`, `REQ-004` |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Covers only the Reference class; must not be restated | `REQ-001` |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Owns authority rules; referenced, not restated | `REQ-001` |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Its Amendment is the model of a superseded marker (L75) | `REQ-002` |
| `tools/check_adr_structure.py` | Defines the required ADR headings; an Amendment must stay a subsection | `REQ-002`, `REQ-004` |

## Acceptance Criteria
- AC-01 (`REQ-001`): `governance_01` contains the ADR responsibility statement with no restatement of ADR-015 or ADR-016 rules and no specification class.
- AC-02 (`REQ-002`): The marking rule is present, names how it relates to the Current-Specification-Only Policy as the owner decided, and contains none of the markers rejected by `history_marker_in_active_doc`.
- AC-03 (`REQ-003`): The relocation rule states the demonstrated-benefit condition, the single-owner condition and the essential-guarantee exception.
- AC-04 (`REQ-004`): ADR-001 Decision Details define "interrupted Attempts" by lease expiry; INV-07 text is unchanged (`check_adr_preservation.py` reports no ERROR); the Amendment is marked in force and cites no `plans/` path.
- AC-05 (`REQ-005`): The ADR-010 Amendment carries the marker the rule requires and keeps its rationale.
- AC-06 (`REQ-006`): `adr_00_document-guide.md` contains one pointer sentence and no restated rule.
- AC-07: Links, anchors and generated references remain valid; `generate_reference_table.py --check`, `generate_adr_authority.py --check`, `check_adr_authority.py` and the documentation checkers pass; no architectural behavior changed.

## Tests
- Documentation-only; no behavior test. `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py` runs once to confirm the lease behavior that ADR-001 now defines in Decision Details is unchanged (`REQ-004`).
- Review the complete text of each edited section for a requirement that lives only in an Amendment (`REQ-002`, `REQ-004`, `REQ-005`).

## Documentation Impact
Yes. Document-class and ADR responsibilities and the marking of historical content (`governance_01`, located through `docs/00_index.md`), the ADR guide pointer, and two ADRs. Driven by `REQ-001` to `REQ-006`. English only.

## Assumptions
- The rule goes into `governance_01` because classes and ADR conventions are defined there; putting normative responsibilities into the Guide-class `adr_00_document-guide.md` or into ADR-015 or ADR-016 would create a competing source (falsifiable by an owner statement that another location is canonical).
- No content is relocated: no volatile ADR detail with a demonstrated maintenance benefit and a single destination owner is known at planning time (falsifiable by churn evidence found at implementation, see UNK-02).
- Phase 1 (ADR-001 completeness) is needed under either owner decision on the policy conflict, because a requirement living only in an Amendment must be transferred first (the policy's own transfer rule); Phase 2 onward waits for the owner's decision.
- Overlap on ADR-010 with the `adrrag001`, `adrrag002` and `adrver001` Plans is a sequencing dependency, not a design conflict: this Plan changes only the Amendment marker and runs after them.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How retained ADR amendment history relates to the Current-Specification-Only Policy (a named exception for ADR Amendments, or transfer and later removal) | An owner decision; the policy and the Issue conflict | The owner decides before Phase 2; Phase 1 is independent. If the owner chooses removal, the marking steps become a transfer-and-remove Plan amendment | False |
| UNK-02 | Which ADR details are volatile enough to justify relocation | Change-frequency and ownership evidence per detail block | None planned; relocate only if implementation finds a demonstrated benefit with a single destination owner, and then amend the Plan first | False |
| UNK-03 | Whether a policy edit in `governance_01` needs approval beyond the task-level decision | The Approval Required reading for a governance document change | Check `governance_05` "Reading the Approval Required Column" before Phase 2 and obtain approval if required | False |
| UNK-04 | The four dependency Plans and the coordinated `adrauth001` Plan are open | Their implementation status | Implement them first (`Depends on` above) and coordinate authority wording with `adrauth001` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | High | 12 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Medium | 4 | N/A | not applicable (rsynced) |

## Design
Classification: Path B, because the change touches 4 files (more than 3).

Analysis (Path B, all four recorded):
- Architecture: only documents change; no Python import or module boundary is touched, so `lint-imports` is not run (checked in Step 3).
- Dependency: `governance_01` is cited by `docs/00_index.md`, the agent and RAG document guides, `tools/check_docs_quality.py` and `tools/check_needs_confirmation_inventory.py`; the added rule must not change any heading those tools read. ADR-001 and ADR-010 are read by `check_adr_structure.py`, `check_adr_preservation.py` and the index matrix.
- Historical: 30-day churn from `git log` (table above); `governance_01` is the highest-churn row, so the edit is one subsection. Bus factor not measured (`git-fame` not run).
- Operational: no port, process or database is touched.
- Persisted schema and consumer scan: not applicable.

Design decisions:
1. One normative rule in `governance_01`; the Guide only points to it. Alternative considered: a new document class definition or a new ADR; rejected because the Issue forbids new registries without need and ADR-015 and ADR-016 already own other rules.
2. Invariants stay unchanged: ADR-001 gains a Decision Details item for the lease definition instead of rewording INV-07, so no preservation ERROR arises.
3. A marked Amendment is the single sanctioned form of retained decision history (recommendation, UNK-01), with the markers listed in `history_marker_in_active_doc` avoided; plan paths are cited by identifier only.
4. No relocation now; the rule states the conditions under which one would be justified.

## Implementation steps
1. **Phase 1: Complete the ADR-001 current contract** (independent of the owner decision)
   - [ ] Add the "interrupted Attempts" definition to Decision Details, mark the Amendment in force, replace the stale plan path by an identifier (`REQ-004`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`)
2. **Phase 2: Policy rule** (starts after the owner's decision on UNK-01 and the approval check of UNK-03)
   - [ ] Add the ADR responsibility, marking and relocation rule (`REQ-001`, `REQ-002`, `REQ-003`; `docs/00_governance/governance_01_documentation-policy.md`)
   - [ ] Add the one-sentence pointer (`REQ-006`; `docs/10_adr/adr_00_document-guide.md`)
3. **Phase 3: Apply the marker to ADR-010** (after the ADR-010 dependency Plans)
   - [ ] Mark the Amendment per the rule (`REQ-005`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
4. **Phase 4: Verification**
   - [ ] Run the Validation plan commands and review each edited section for a requirement that lives only in an Amendment (`REQ-001` to `REQ-006`; all target files). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All four documents | Quality (including the history-marker rule), structure, policy, language | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/00_governance/governance_01_documentation-policy.md docs/10_adr/adr_00_document-guide.md docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md docs/10_adr/adr_02_06_010_rag-fallback.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |
| ADR-001 and ADR-010 | Preservation, structure, invariant matrix | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py` | No ERROR; invariants unchanged |
| Authority and generated content | Model and generated sections | `uv run python tools/check_adr_authority.py`; `uv run python tools/generate_adr_authority.py --check`; `uv run python tools/generate_reference_table.py --check` | Pass; no drift |
| Touched domains | Cross-check with code | `uv run python tools/check_docs_consistency.py --domain agent`; `uv run python tools/check_docs_consistency.py --domain rag` | No findings |
| ADR-001 lease behavior (unchanged) | Regression | `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py` | Pass |

## Risks
- **Risk**: The new rule contradicts the Current-Specification-Only Policy in the same document → **Mitigation**: the rule states its relationship to that policy explicitly as the owner decides (UNK-01), and Phase 2 does not start before that decision.
- **Risk**: Added text trips `history_marker_in_active_doc` (a `done/` path, `REQ-NNN`, a `Traceability` heading) → **Mitigation**: cite plans by identifier, avoid those forms, and run `check_docs_quality.py`.
- **Risk**: Defining "interrupted Attempts" in Decision Details is read as a new decision → **Mitigation**: copy the definition from the existing Amendment without change, state that no behavior changed, and keep INV-07 untouched.
- **Risk**: A policy edit needs approval that is not obtained → **Mitigation**: check the Approval Required rule first (UNK-03) and stop at Phase 2 until it is settled.
- **Risk**: Overlapping edits on ADR-010 with three other Plans → **Mitigation**: run Phase 3 only after those Plans and limit the change to the Amendment marker.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Complete the ADR-001 current contract | In Progress | — | — |  |
| 2 | Policy rule | In Progress | — | — |  |
| 3 | Apply the marker to ADR-010 | In Progress | — | — |  |
| 4 | Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-111822_01_docs_00_governance_governance_01_documentation-policy.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261108-111822_02_docs_10_adr_adr_00_document-guide.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261108-111822_03_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261108-111822_04_docs_10_adr_adr_02_06_010_rag-fallback.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050707_adrdoc001_separate-adr-current-history.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-093000
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1-2; `governance_01` L47-L58, L74 | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-01 | `check_docs_quality.py`; `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 5-7; `governance_01` L22-L45; `doc_quality_rules.json` | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-02 | `check_docs_quality.py` | Needs confirmation |
| REQ-003 | Required Changes 3-4, Constraints; Implementation Intent | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-03 | Full read-through | Explicit in issue |
| REQ-004 | Required Changes 5-6; ADR-001 L58-L60, L175 | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 1 | AC-04 | `check_adr_preservation.py`; `tests/agent/workflow/test_stale_recovery_lease.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 6; ADR-010 L80-L82 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 3 | AC-05 | `check_adr_structure.py`; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 1, 8; `adr_00_document-guide.md` L15-L96 | `docs/10_adr/adr_00_document-guide.md` | Phase 2 | AC-06 | `check_docs_structure.py` | Derived from confirmed evidence |