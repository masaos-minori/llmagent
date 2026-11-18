## Goal
- Align the RAG consistency diagnostics (prefix, severity, repair action, message) with each other, correct the ADR and guide wording that the code contradicts, and prepare the option table for the maintainer's decision on how a derived-index mismatch, a check timeout, and a check exception are classified, then apply the recorded decision in the pending-amendment form.

## Priority
High

## Scope
- **In-Scope**: finding prefixes, repair actions, and messages in `scripts/db/rag_consistency.py` with tests; the RAG guide's repair table; ADR-009 transaction boundary and invariant numbering wording; the CSC-001 evidence in `governance_03`; the option table for the maintainer; after the decision, the ADR-004, ADR-005, ADR-009, and guide wording, the startup comment, and the pending ledger entries.
- **Out-of-Scope**: writing or choosing the policy decision; writing approval text; editing archived files under `issues/done/` (UNK-03); editing ADR-010 to close CSC-001 (UNK-06); changing a finding's severity; persistence of repairs (already merged); `rebuild_fts` behavior.
- **Dependencies**: N/A: none. The Issue's prerequisites are met: the repair persistence fix is merged (`rebuild_vec` removes orphan vector rows) and the approval governance defines the pending-amendment form and the ledger. This Plan is a prerequisite of the open issue adrchk005 (startup-fail-closed), which uses FATAL until the decision is recorded; that issue is named by id and not by path because it does not gate this Plan. The order against it, which also edits the startup module, is the owner's call.

## Background
The RAG consistency check, ADR-004, ADR-005, ADR-009, and earlier archived issue files disagree on what a derived-index failure is and how severe it is. Re-verification (Step 2) confirmed most claims, corrected two (three `[CRITICAL]` DEGRADED findings, and ADR-009's Degraded condition is not None), and found that the "fail-closed downstream" comment in the startup module has no code support.

## Problem
- Startup continues with a warning for a RAG consistency timeout, an exception, and DEGRADED findings; ADR-004 Decision Group 2 forbids warning-only continuation for safety/integrity failures, and no ADR-004 Exception covers this case.
- Three DEGRADED findings (FTS orphan, orphan vector rows, chunks without vector rows) carry `[CRITICAL]`; the other DEGRADED findings carry `[WARNING]` and every FATAL finding carries `[CRITICAL]`.
- Orphan vector rows, vector mismatch, chunks without vector rows, and documents without chunks set `repair_action=rebuild_vec`; URL-level inconsistency sets `reconcile_url`. The messages tell users to re-run ingestion, and `rebuild_vec` now only removes orphan vector rows while `reconcile_url` only inserts missing FTS entries.
- ADR-009 says the transaction boundary is per chunk; the ingester commits one transaction per URL and ADR-005 says per document. ADR-009's invariant list ends at INV-08 while INV-10 and INV-11 appear only in Implementation Notes and a Manual Review line cites INV-11.
- The startup comment says the unverified RAG state is fail-closed downstream; no module consumes it except the reporter's counts.
- CSC-001's Validation evidence cites a corpus-identity issue as an open `issues/` path; the identity modules no longer exist.

## Reason for Change
- Operators and readers get contradictory guidance: a finding names one repair and describes another, and the policy documents describe three different behaviors.
- The Issue asks for one recorded policy; the decision is the maintainer's, so the Plan separates what needs no decision from what does and stops at the gate.

## Implementation Intent
- Every finding's prefix matches its severity, and its message and `repair_action` name the same repair, which can fix that state.
- ADR-009 and the RAG guide describe the current code.
- One option table lets the maintainer decide; the recorded decision is applied to ADR-004, ADR-005, ADR-009, the guide, and the startup comment, in the pending-amendment form without approval text.

## Requirements
- `REQ-001`: Every finding built from `_CHECKS` carries `[CRITICAL]` if and only if its severity is FATAL, and `[WARNING]` otherwise; the three DEGRADED findings that carry `[CRITICAL]` change their prefix, not their severity.
- `REQ-002`: Each finding's `repair_action` and message name the same repair and the repair can fix the state: `rebuild_fts` for the FTS gap and FTS orphan, `rebuild_vec` (with the `/session rag-rebuild-vec` command in the message) for orphan vector rows, a new `reingest` value (message: re-run ingestion with `ingester.py --force`) for vector mismatch, chunks without vector rows, documents without chunks, and URL-level inconsistency, and `restore_from_backup` for the FATAL findings (UNK-02 default).
- `REQ-003`: The repair table and prose of the RAG guide match REQ-002.
- `REQ-004`: ADR-009 states the transaction boundary as per document and states its current invariant numbering (INV-09 unused; INV-10 and INV-11 defined in Implementation Notes) (UNK-04, UNK-05 defaults).
- `REQ-005`: The CSC-001 entry of `governance_03` describes the current state: the identity modules are gone and unreferenced, ADR-010's surviving wording remains, and no archived issue path is cited as open (UNK-06).
- `REQ-006`: The option table for the maintainer is in this Plan's Design section, and no policy decision or approval text is written before the maintainer's decision is recorded (UNK-01).
- `REQ-007`: After the decision, ADR-004 covers the RAG consistency timeout, exception, and DEGRADED behavior as the decision states, shown in the pending-amendment form with an approval ledger entry; ADR-005's Fail-Open or Degraded Conditions, ADR-009's Degraded condition, and the guide's startup section follow it.
- `REQ-008`: The startup comment that claims a downstream fail-closed behavior is corrected to what the code does, and the timeout and exception branches follow the decision (no behavior change under option A or B; option C is a scope change).
- `REQ-009`: The re-verification of the three archived issue files' claims is recorded in the Notes of the `governance_03` procedure and the final report; no archived file is edited (UNK-03).
- `REQ-010`: The ADR-004 per-file size ceiling in `tools/check_docs_structure.py` equals the accepted size after the REQ-007 edit (fallout of REQ-007).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/db/test_rag_consistency.py` | Prefix, severity, and repair-action tests | Add tests over the `_CHECKS` issue builders for prefix versus severity and for message versus `repair_action`, written before the fix | REQ-001, REQ-002 / AC-1, AC-2 | `_CHECKS` pairs a clean predicate with an issue builder; the file exists with 5 commits in 30 days (checked in Step 3) | `uv run pytest tests/db/test_rag_consistency.py` | Verified |
| `scripts/db/rag_consistency.py` | Finding prefixes, repair actions, messages | Change the three DEGRADED `[CRITICAL]` prefixes, add the `reingest` repair action, and align the messages | REQ-001, REQ-002 / AC-1, AC-2 | FTS orphan, orphan vec, and chunks without vec are DEGRADED with `[CRITICAL]`; four findings set `rebuild_vec` and one `reconcile_url` while their messages say to re-ingest (checked in Step 2) | `tests/db/test_rag_consistency.py` | Verified |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Repair table and startup section | Align the repair table with REQ-002; after the decision, align the Startup Warnings section | REQ-003, REQ-007 / AC-3, AC-7 | The table lists `rebuild_vec` for vector mismatch, chunks without vector rows, and documents without chunks, and `reconcile_url` for URL-level inconsistency; the Startup Warnings section describes warn-and-continue (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | CSC-001 evidence and ledger entries | Correct the CSC-001 evidence and required action; after the decision add the pending ledger entries for the ADR amendments | REQ-005, REQ-007, REQ-009 / AC-5, AC-7, AC-8 | CSC-001 Validation evidence cites an issue path that is now archived; Part 5 holds the ledger (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_issue_inventory_conformance.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Transaction boundary, numbering, Degraded condition | Correct `Transaction Boundary` to per document, state the invariant numbering, and after the decision align the Degraded condition | REQ-004, REQ-007 / AC-4, AC-7 | `Transaction Boundary: per chunk`; INV-01 to INV-08 listed, INV-10 and INV-11 only in Implementation Notes; `Degraded condition: fts_gap > 0` (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Policy coverage of the RAG check | After the decision, state how the RAG consistency timeout, exception, and DEGRADED results are classified, in the pending-amendment form | REQ-007 / AC-7 | Decision Group 2 items 5 to 8 and Group 3 items 10 to 12 govern the classification; `## Exceptions` lists no RAG case; 34551 B against a 34555 B ceiling (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Fail-Open or Degraded wording | After the decision, align `Fail-Open or Degraded Conditions` and the Degraded condition with it, in the pending-amendment form | REQ-007 / AC-7 | The section's first bullet delegates the startup policy and the timeout behavior to the RAG guide, its second says the post-ingestion check only logs warnings; the Degraded condition is `fts_gap > 0` or `orphan_vec_count > 0`; two pending ledger bullets exist (checked in Step 2 and Step 3a of plan-to-implementation-procedure) | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py`, `tools/check_docs_structure.py` | Verified |
| `scripts/agent/startup_validation.py` | Startup comment and branches | Correct the "fail-closed downstream" comment and apply the decision to the timeout and exception branches | REQ-008 / AC-7 | The timeout, exception, and DEGRADED branches add warnings and continue; the comment claims a downstream fail-closed behavior that no module implements (checked in Step 2) | `tests/agent/test_startup.py`, `tests/agent/test_startup_validation.py` | Verified |
| `tools/check_docs_structure.py` | ADR-004 size ceiling (fallout) | Re-record the ADR-004 ceiling at the accepted size after the REQ-007 edit | REQ-010 / AC-9 | `SIZE_EXCEPTIONS` holds a ceiling of 34555 for ADR-004, whose size is 34551 (checked in Step 3) | `tests/tools/test_check_docs_structure.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/models.py` | `ConsistencyFinding` and `FindingSeverity`; `repair_action` is a free string | REQ-001, REQ-002 |
| `scripts/agent/services/rag_maintenance_service.py` | The merged `rebuild_vec` and `reconcile_url` contracts that the repair actions must match | REQ-002 |
| `scripts/rag/ingestion/transaction_commit.py` | One `BEGIN IMMEDIATE` transaction per URL | REQ-004 |
| `scripts/rag/ingestion/document_manager.py` | The post-ingestion consistency check that ADR-005 cites | REQ-007 |
| `tests/agent/test_startup.py` | Startup tests for degraded findings and repair actions | REQ-008 |
| `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Describes `summarize_issues` and `_CHECKS` | REQ-001 |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | The Withdrawn ADR whose surviving wording CSC-001 tracks | UNK-06 |
| `docs/00_governance/governance_01_documentation-policy.md` | The pending-amendment form and ledger citation rules | REQ-007 |

## Acceptance Criteria
- `AC-1` (REQ-001): A test shows every finding built from `_CHECKS` has `[CRITICAL]` if and only if it is FATAL.
- `AC-2` (REQ-002): A test shows each finding's message names the repair its `repair_action` stands for, and no finding sets a repair action that cannot fix its state.
- `AC-3` (REQ-003): The RAG guide's table and prose match the code's repair actions and messages.
- `AC-4` (REQ-004): ADR-009 states per document and states its invariant numbering.
- `AC-5` (REQ-005): The CSC-001 entry cites only existing paths and the current facts.
- `AC-6` (REQ-006): The option table is in the Plan and a maintainer decision comment on the Plan exists before any Phase 4 edit.
- `AC-7` (REQ-007, REQ-008): ADR-004 explicitly covers the RAG consistency timeout, exception, and DEGRADED behavior in the pending-amendment form with a ledger entry; ADR-005, ADR-009, the guide, and the startup comment follow the decision.
- `AC-8` (REQ-009): The re-verification of the archived issue files' claims is in the procedure Notes and `git status` shows no archived file changed.
- `AC-9` (REQ-010): `tools/check_docs_structure.py` passes with the re-recorded ceiling.
- `AC-10` (REQ-001 to REQ-010): The validation sequence of `rules/toolchain.md` and the docs and ADR checkers pass.

## Tests
- `REQ-001`, `REQ-002`: unit tests in `tests/db/test_rag_consistency.py` that build a report with every rule unclean, iterate the `_CHECKS` issue builders, and assert the prefix against the severity and the message against a table of repair action to expected command or phrase.
- `REQ-008`: the existing startup tests keep passing; under option C new tests for the aborting branches are a Plan amendment.
- `REQ-003` to `REQ-007`, `REQ-009`, `REQ-010`: documentation changes verified by the checkers in the Validation plan and by reviewing the diff.

## Documentation Impact
Yes. `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (REQ-003, REQ-007), ADR-009 (REQ-004, REQ-007), ADR-004 and ADR-005 (REQ-007), and `governance_03` (REQ-005, REQ-007). `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` already describes `summarize_issues` without prefixes and needs no change.

## Assumptions
- A prefix fix changes the text only; severities stay, because a severity change is a policy change (it would change which findings abort startup).
- `repair_action` is a free string with one consumer (the startup message), so a new `reingest` value needs no type change (UNK-02 default).
- The ADR-009 `Transaction Boundary` correction aligns wording to the code and to ADR-005 and does not change a decision; if the maintainer treats it as a decision change, it moves to the pending-amendment form (UNK-05).
- The ADR edits of Phase 4 are shown only in the pending-amendment form (`governance_01`), with ledger entries whose approver and date stay `Not recorded`; no approval text is written.
- Phase 4 edits are gated: the maintainer's decision is recorded as a maintainer comment on this Plan before the first Phase 4 edit (`rules/coding.md` Explicit sign-off gates).
- The `governance_03` row precedes the ADR rows, so the ledger entries that the pending bullets of ADR-004, ADR-005, and ADR-009 cite exist before the live `tools/check_adr_structure.py` run (new entry ids continue after the existing ones).
- The ADR-004 size ceiling (34555) leaves no room for the Phase 4 edit, so REQ-010 re-records it, as `tools/check_docs_structure.py` does for other ADRs above the default limit.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The policy for a derived-index mismatch, the check timeout, and the check exception (option table in Design) | Maintainer decision; `Do not write the policy decision` is an Issue constraint | The maintainer chooses an option and records it as a comment on this Plan at the Phase 4 gate; option C is a scope change and a Plan amendment | False |
| UNK-02 | The repair action mapping and the new `reingest` value | Owner confirmation; the mapping follows the guide's own `Fix` column | The owner confirms with UNK-01 before the `scripts/db/rag_consistency.py` edit | False |
| UNK-03 | How the claims about the three archived issue files are verified and corrected; the Issue's acceptance that they "no longer give opposite directions" cannot be met without editing archived files | Archived files were not read (`rules/workflow-lifecycle.md` Target Validation); owner decision on reading or editing them | The procedure records what a read-only check shows if the owner allows reading; no archived file is edited here; a correction elsewhere is the owner's decision | False |
| UNK-04 | How to treat ADR-009's invariant numbering: state the current numbering (default) or renumber | Owner preference; renumbering changes citations and needs an approval record | The owner confirms the default before the ADR-009 edit | False |
| UNK-05 | Whether the ADR-009 transaction boundary correction is a wording alignment (default) or a decision change | Owner reading of `governance_01` ADR Change Protocol | The owner confirms with UNK-04; a decision change uses the pending-amendment form | False |
| UNK-06 | CSC-001 can be closed only when ADR-010's surviving present-tense wording is moved or removed; ADR-010 is not a Target File | Owner decision on a scope amendment | This Plan corrects the evidence only; closing is a separate change | False |
| UNK-07 | Order against the open issue adrchk005, which edits the same startup module and relies on this decision | Owner decision | The owner decides the order; this Plan records the overlap | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/db/test_rag_consistency.py` | Modify | Low | 5 | High (single author) | not applicable (rsynced) |
| `scripts/db/rag_consistency.py` | Modify | Medium | 3 | High (single author) | not applicable (rsynced) |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Medium | 5 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Medium | 4 | High (single author) | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium | 14 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | High | 13 | High (single author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Medium | 7 | High (single author) | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | Modify | High | 13 | High (single author) | not applicable (rsynced) |
| `tools/check_docs_structure.py` | Modify | Low | 37 | High (single author) | not applicable (rsynced) |

## Design
- **Classification**: Path B (more than 3 files; changes a public diagnostic contract). Baseline (checked in Step 3): `radon cc` rates `check_rag_consistency` C (18) and `StartupValidationPipeline.check_services` C (19) already, which this Plan does not raise; `vulture` and `bandit` report nothing on the two scripts targets; `lint-imports` keeps all contracts. Consumer scan for `repair_action` and `summarize_issues`: the production consumer of `repair_action` is the startup message (`scripts/agent/startup_validation.py`), the other candidates are ADR test citations, the guide, and the DB maintenance doc, listed in `Reference Files` or `not affected: documentation or test citation only`. Persisted schema check: not applicable.
- **D1 Prefix**: a FATAL finding is `[CRITICAL]`, every other finding `[WARNING]`; only the three DEGRADED builders change.
- **D2 Repair action**: the mapping of REQ-002; `reingest` is a plain string like the others and the startup message prints it unchanged.
- **D3 Tests**: one report with every rule unclean, then each builder's finding is checked; failing before the fix.
- **D4 Option table for the maintainer (UNK-01)**. Facts: ADR-004 Decision Group 2 item 6 forbids warning-only continuation for a safety/integrity failure; item 8 allows continuation after an availability failure only if the component is non-mandatory, the failure is localized, every affected function can be safely disabled, no control is relaxed, and the partial state is observable; Group 3 item 11 forbids treating a component as non-mandatory merely because startup is possible. The code warns and continues for DEGRADED results, a check timeout, and a check exception.

| Option | ADR-004 change | Startup outcome | Fit with ADR-004 | Needs from the maintainer | Cost and interplay |
|---|---|---|---|---|---|
| A. Availability failure | Add the RAG derived-index results (DEGRADED findings, check timeout, check exception) to the availability failures of Group 2 and classify the RAG component non-mandatory for startup | Unchanged: warn and continue | The conditions of item 8 must hold; RAG search keeps running on an index that is not disabled, so "every affected function can be safely disabled" needs a mechanism or a justification | The classification and the justification | ADR-004 text change; no code change unless a disable mechanism is added |
| B. Registered Exception | Add an ADR-004 Exception for derived-index inconsistency, with a rationale and approval | Unchanged: warn and continue | An explicit exception, like the existing ones | The rationale and the approval, which the implementer never writes | ADR-004 text change; a Known Issue or NC entry for the pending state |
| C. Fail closed | State that an unverified or inconsistent RAG index is a safety/integrity failure | Check timeout and check exception (and optionally DEGRADED) abort startup | Follows Group 2 item 6 literally | The scope of what aborts | Code change and new tests in `scripts/agent/startup_validation.py`; Plan amendment; overlaps adrchk005; lowers startup availability |
- **D5 Startup comment**: replace the unsupported "fail-closed downstream" remark with the reason the check does not abort (what the code does), per the decision.

## Implementation steps
1. **Phase 1: Failing diagnostics tests**
   - [ ] Add the prefix, severity, and repair-action tests to `tests/db/test_rag_consistency.py` and run them to show the failures (REQ-001, REQ-002)
2. **Phase 2: Diagnostics fix and guide table**
   - [ ] Confirm UNK-02 with the owner before the edit; stop if the mapping differs
   - [ ] Fix the prefixes, repair actions, and messages in `scripts/db/rag_consistency.py` (REQ-001, REQ-002)
   - [ ] Align the repair table of `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (REQ-003)
3. **Phase 3: ADR-009 wording and CSC-001 evidence (no decision)**
   - [ ] Confirm UNK-04 and UNK-05, then correct `Transaction Boundary` and the numbering statement in `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` (REQ-004)
   - [ ] Correct the CSC-001 evidence in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and record the archived-file re-verification result in the procedure Notes (REQ-005, REQ-009)
4. **Phase 4: Decision gate and application**
   - [ ] Present the option table (Design D4) to the maintainer and record the decision as a maintainer comment on this Plan; stop until it exists (REQ-006)
   - [ ] Apply the decision to `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` and `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` in the pending-amendment form (REQ-007)
   - [ ] Align the Degraded condition of `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` and the Startup Warnings section of `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` (REQ-007)
   - [ ] Add the pending ledger entries in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (REQ-007)
   - [ ] Correct the comment and apply the decision to the branches in `scripts/agent/startup_validation.py` (REQ-008)
   - [ ] Re-record the ADR-004 ceiling in `tools/check_docs_structure.py` (REQ-010)
5. **Phase 5: Validation and hand-off**
   - [ ] Run the Validation plan commands and report each result
   - [ ] Deploy hand-off: `scripts/` changes, so after the change is committed and pushed, deploying is the user's decision through `skills/deploy/SKILL.md`

### Release units
**Unit**: rag-diagnostics | **Phases**: 1, 2 | **Reason**: the failing-first tests of Phase 1 stay red until the fix of Phase 2 lands, so neither phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/db/test_rag_consistency.py`, `scripts/db/rag_consistency.py` | Unit | `uv run pytest tests/db/test_rag_consistency.py tests/agent/test_startup.py tests/agent/test_startup_validation.py` | New tests fail before Phase 2 (record), pass after |
| `scripts/db/rag_consistency.py`, `scripts/agent/startup_validation.py` | Lint, type, security, architecture | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |
| `docs/21_rag/*.md`, `docs/10_adr/*.md`, `docs/00_governance/*.md` | Documentation and ADR checks | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_issue_inventory_conformance.py`, `uv run python tools/check_docs_consistency.py --domain rag` | No ERROR except the reviewed Approval-section reports of `check_adr_preservation.py` |
| `tools/check_docs_structure.py` | Unit | `uv run pytest tests/tools/test_check_docs_structure.py`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Pass |
| Whole change | Suite and coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass; at least 90% on changed lines |
| `plans/`, `issues/`, `implementations/` | Work item checks | `uv run python tools/check_workitem_structure.py --file __CHANGED_FILES__`, `uv run python tools/check_workitem_traceability.py --active-only` | No findings |

## Risks
- **Risk**: ADR edits that change a decision need an approval record, which the implementer must not write → **Mitigation**: Phase 4 uses the pending-amendment form with pending ledger entries; the gate waits for the maintainer's decision comment.
- **Risk**: The Phase 4 edit of ADR-004 exceeds its size ceiling → **Mitigation**: REQ-010 re-records the ceiling in the same change; `tools/check_docs_structure.py` is an explicit target.
- **Risk**: A new `reingest` repair action surprises a consumer that matches repair action strings → **Mitigation**: the consumer scan found only the startup message; the existing startup tests build their own findings; the guide table is updated with it.
- **Risk**: Option C changes startup behavior and overlaps the open issue adrchk005 → **Mitigation**: option C is a scope change, a Plan amendment, and the owner decides the order against that issue (UNK-07).
- **Risk**: Other issues edit the same ADR files and `governance_03` (adrchk005, 009, 013, 021, 022, and others) → **Mitigation**: re-run the searches before each edit; `tools/check_plan_target_overlaps.py` reports overlaps when those Plans freeze.
- **Risk**: The ADR-009 numbering statement is read as a history note → **Mitigation**: it states the current numbering only (UNK-04); renumbering needs an approval record.
- **Risk**: The Issue's acceptance for the archived issue files cannot be met without editing them → **Mitigation**: UNK-03 records it; the Plan restates the acceptance as the recorded re-verification (AC-8).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing diagnostics tests | In Progress | — | — |  |
| 2 | Diagnostics fix and guide table | In Progress | — | — |  |
| 3 | ADR-009 wording and CSC-001 evidence (no decision) | In Progress | — | — |  |
| 4 | Decision gate and application | In Progress | — | — |  |
| 5 | Validation and hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-124938_01_tests_db_test_rag_consistency.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-124938_02_scripts_db_rag_consistency.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-124938_03_docs_21_rag_rag_05_07-rag-index-consistency-checks.md.md | 2, 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_04_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 3, 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_05_docs_10_adr_adr_02_06_009_rag-fts5-text-separation.md.md | 3, 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_06_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_07_docs_10_adr_adr_02_06_005_rag-source-derived-index-relationships.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_08_scripts_agent_startup_validation.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-124938_09_tools_check_docs_structure.py.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-124317
- **Related target files**: `tests/db/test_rag_consistency.py`; `scripts/db/rag_consistency.py`; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`; `scripts/agent/startup_validation.py`; `tools/check_docs_structure.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (prefixes); three DEGRADED `[CRITICAL]` findings (Step 2) | `tests/db/test_rag_consistency.py` | Phase 1 | AC-1 | `uv run pytest tests/db/test_rag_consistency.py` | Confirmed by repository evidence |
| REQ-001 | Same | `scripts/db/rag_consistency.py` | Phase 2 | AC-1 | `uv run pytest tests/db/test_rag_consistency.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (messages and repair action); message versus `repair_action` mismatches (Step 2) | `tests/db/test_rag_consistency.py` | Phase 1 | AC-2 | `uv run pytest tests/db/test_rag_consistency.py` | Derived from confirmed evidence |
| REQ-002 | Same; guide `Fix` column | `scripts/db/rag_consistency.py` | Phase 2 | AC-2 | `uv run pytest tests/db/test_rag_consistency.py` | Derived from confirmed evidence |
| REQ-003 | Issue Implementation Intent (the RAG guide follows); guide repair table (Step 2) | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Phase 2 | AC-3 | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Derived from confirmed evidence |
| REQ-004 | Issue Required Changes (transaction boundary, INV-09); ADR-009 and `transaction_commit.py` (Step 2) | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Phase 3 | AC-4 | `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Issue Reason for Change (stale text) and Documentation Impact (CSC-001 evidence); CSC-001 entry (Step 2) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 3 | AC-5 | `tools/check_known_deviation_sync.py`, `tools/check_issue_inventory_conformance.py` | Confirmed by repository evidence |
| REQ-006 | Issue Constraints and AI Implementation Instruction (option table, then stop) | N/A: the option table is Design D4 of this Plan | Phase 4 | AC-6 | the maintainer's decision comment on the Plan | Explicit in issue |
| REQ-007 | Issue Required Changes (decision) and Acceptance Criteria (ADR-004 coverage) | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 4 | AC-7 | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Needs confirmation |
| REQ-007 | Same | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Phase 4 | AC-7 | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Needs confirmation |
| REQ-007 | Same | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Phase 4 | AC-7 | `tools/check_adr_structure.py` | Needs confirmation |
| REQ-007 | Same | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Phase 4 | AC-7 | `tools/check_docs_quality.py` | Needs confirmation |
| REQ-007 | Same; `governance_01` pending-amendment form | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 4 | AC-7 | `tools/check_adr_structure.py` | Needs confirmation |
| REQ-008 | Issue Required Changes (apply the decision to the timeout and exception branches); startup comment (Step 2) | `scripts/agent/startup_validation.py` | Phase 4 | AC-7 | `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_validation.py` | Needs confirmation |
| REQ-009 | Issue Required Changes (re-verify the archived issue files) and Unresolved Questions | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 3 | AC-8 | `git status` shows no archived file changed | Needs confirmation |
| REQ-010 | `SIZE_EXCEPTIONS` ceiling of ADR-004 (Step 3) | `tools/check_docs_structure.py` | Phase 4 | AC-9 | `uv run pytest tests/tools/test_check_docs_structure.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-124938 -->