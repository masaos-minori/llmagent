## Goal
Make the manual recovery procedure for `workflow.sqlite` and `eventbus.sqlite` as safe as the automated rag/session recovery (stop the standalone EventBus service, move `-wal`/`-shm` sidecars aside before restoring, verify the backup), remove the confirmed self-contradictions in `db_07` and ADR-008, and record the Dry Run journal-mode deviation truthfully — all as documentation changes, with maintainer decisions recorded rather than fabricated.

## Priority
High

## Scope
- **In-Scope**: Rewrite the manual recovery procedure in `agent_10_01` to stop the EventBus service and the Agent, move `-wal`/`-shm` sidecars aside before Step 5's `cp`, verify the backup (`PRAGMA integrity_check` plus the schema-fingerprint check from adrrev005), restore, then start. Correct the stale `db_07` 9.2 claim so it matches 9.5 and the code. Clarify ADR-008 Decision Detail #7/#8 wording (which is textually contradictory but not factually wrong). Flag the `memories_vec` dual-listing and the Dry Run journal-mode deviation as maintainer decisions and record them without fabricating approvals. Update the ADR index to track ADR-008.
- **Out-of-Scope**: Implementing the schema fingerprint (adrrev005). Deciding the `mcp_dedup.sqlite` classification (adrrev008). Automating restore for workflow/eventbus (ADR-008 INV-18 stays prohibited). Fixing Dry Run in code unless a maintainer decides the code fix over recording the deviation. Rewriting the manual procedure into a command-by-command catalog beyond the minimal operator steps.
- **Dependencies**:
  - **Depends on**: `issues/20261109-112715_adrrev005_schema-fingerprint-unify.md` | phase all | the post-restore schema-fingerprint verification referenced by the rewritten procedure; the procedure text names it but its exact check is adrrev005's. Not blocking the procedure wording.
  - **Depends on**: `plans/done/20261110-230633_adrrev008_mcp-dedup-ownership.md` | phase all | adrrev008 adds the `mcp_dedup.sqlite` Recovery Policy Matrix row to ADR-008; this Plan edits other ADR-008 sections. Sequencing dependency (see Assumptions) — not blocking, but adrrev008 should land first to avoid ADR-008 file contention.
  - **Related**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md` (classification recorded in the same ADR-008 matrix), `issues/20261109-112538_adrrev002_agent-eventbus-coupling.md` (ownership of `eventbus.sqlite`, relevant to the EventBus service-stop step).

## Background
Manual recovery is the only restore path for `workflow.sqlite` and `eventbus.sqlite` (ADR-008 INV-18 prohibits automatic restore). The automated rag/session recovery path (`scripts/db/recovery.py`, `recovery_restore.py`) quarantines stale `-wal`/`-shm` sidecars and stages a verified candidate before activation, but the documented manual path does neither: `agent_10_01` Manual Recovery Step 5 copies the backup over the live file without moving sidecars, and Step 1 ("ensure no remaining subprocesses") never names the standalone EventBus process that holds `eventbus.sqlite`. Two document self-contradictions are also confirmed: `db_07` section 9.2 says nothing validates a backup's integrity before use while 9.5 says it is, and ADR-008 lists `memories_vec` under both "System of record" and "Derived or rebuildable data". These were verified against current source on 2026-11-10 (HEAD `e700efa5f`).

## Problem
- Copying a backup over a database that still has stale `-wal`/`-shm` files can let SQLite replay those frames onto the restored file on next open, producing a corrupted or mixed database. The automated path treats leaving sidecars as hazardous (it quarantines them); the manual path does not.
- Restoring `eventbus.sqlite` while the standalone EventBus service holds it open can leave the service writing to an unlinked file. The EventBus is a persistent uvicorn HTTP process, separate from the agent process, so Step 1's "no remaining subprocesses" does not cover it.
- `db_07` 9.2 (line 36) and 9.5 (line 62) contradict each other on whether backup integrity is verified before use, so an operator cannot rely on either.
- ADR-008 lists `memories_vec` as both system of record and derived/rebuildable; a store cannot be both.
- ADR-008 Known Deviations says "Not applicable" for the Dry Run journal-mode change that its own Automated Tests table documents, and Decision Details #7/#8 read as contradictory.

## Reason for Change
- Manual recovery is the only restore path for workflow and eventbus (ADR-008 INV-18); an unsafe procedure defeats the purpose of recovery.
- Self-contradictions in normative docs are a documentation-policy violation; an operator cannot follow a matrix that classifies one store two ways.
- Timing: depends on the schema-validation mechanism (adrrev005) for post-restore verification, and the mcp_dedup classification (adrrev008) shares ADR-008.

## Implementation Intent
Bring the manual path up to the automated path's safety bar by documentation alone: stop the EventBus service and the Agent, move sidecars aside, verify the backup, restore, restart, reusing the `recover_corruption` staging logic where the operator can invoke it. Resolve the two confirmed self-contradictions where the fix is unambiguous (db_07 9.2 wording; Decision #7/#8 wording), and route the genuinely ambiguous items (`memories_vec` correct classification, Dry Run fix-vs-record, Negative Consequences, Implementation References, INV numbering) to a maintainer decision, recorded here without fabrication.

## Requirements
- `REQ-001`: The manual recovery procedure in `agent_10_01` MUST stop the EventBus service and the Agent, move `-wal`/`-shm` sidecars aside before the restore `cp`, verify the backup with `PRAGMA integrity_check` (plus the adrrev005 schema-fingerprint check), restore, then start.
- `REQ-002`: `db_07` section 9.2 MUST state that backup integrity IS verified before use, matching 9.5 and `scripts/db/recovery.py::_backup_is_usable()`.
- `REQ-003`: ADR-008 Decision Detail #7 describes the actual correlation keys and Decision Detail #8's accurate statement is preserved; the textual tension between them is removed.
- `REQ-004`: ADR-008 `memories_vec` dual-listing is flagged as a structural contradiction requiring a maintainer decision on the correct classification; the plan documents the contradiction and does not fabricate the resolved classification.
- `REQ-005`: ADR-008 records the Dry Run journal-mode deviation in Known Deviations and the governance ledger per a maintainer decision (or fixes Dry Run in code), and fabricates no approval record.
- `REQ-006`: After the ADR-008 edits, the ADR index (`adr_01_index`) still correctly tracks ADR-008 (title, domain, INV-01–05); update it only if it diverges (governance-gated amendment record).

## Implementation Target Files
**Freeze status**: Frozen (`20261110-233648`; `check_workitem_structure.py` reports No findings; `check_plan_target_overlaps.py` reports one candidate — `agent_10_01` also targeted by adrrev007 — judged compatible, recorded in Assumptions).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Add the EventBus service stop to Manual Recovery; move `-wal`/`-shm` sidecars aside before Step 5's `cp`; reference the adrrev005 fingerprint verification. | REQ-001 | Manual Recovery Step 5 (L127-134) performs only `cp` + `PRAGMA integrity_check` (no sidecar handling); Step 6 (L137-143) removes sidecars; Step 1 (L102-103) says "no remaining subprocesses" without naming the EventBus. | none (doc) | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Correct the stale 9.2 claim (line 36) so backup integrity verification matches 9.5 and the code. | REQ-002 | 9.2 (L36) "Nothing validates the backup's own integrity before it is used — see 9.4 and 9.5" vs 9.5 (L62) "Backup integrity IS verified before use"; `recovery.py::_backup_is_usable()` runs `_run_integrity_check(backup, target)` before any copy. | none (doc) | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Clarify Decision #7/#8 wording; flag `memories_vec` dual-listing (L92/L93) for maintainer resolution; record the Dry Run journal-mode deviation per maintainer decision. Decision items are already explicitly numbered (L114+). | REQ-003, REQ-004, REQ-005 | Decision #7 (L120)/#8 (L121) present and mutually awkward; L121/#8 factually accurate; L92 lists `memories_vec` as system of record, L93 also as derived; Automated Tests L311 documents the rollback-journal edge while Known Deviations L349 says "Not applicable"; Decision items already numbered (L114+). | none (doc) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/recovery.py` | Source of the safe restore sequence (`_restore_from_backup`, `_verify_candidate`, `_backup_is_usable`) the manual procedure should mirror. | `docs/23_agent/agent_10_01...` (REQ-001) |
| `scripts/db/recovery_restore.py` | `_quarantine_sidecar_files` / `_stage_restore` show the sidecar handling the manual path lacks. | `docs/23_agent/agent_10_01...` (REQ-001) |
| `scripts/eventbus/app.py` | Confirms the EventBus is a persistent uvicorn process holding `eventbus.sqlite` open. | `docs/23_agent/agent_10_01...` (REQ-001) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Authority for how fail-open/deviations are registered; read to model the Dry Run deviation record. | `docs/10_adr/adr_02_05_008...` (REQ-005) |
| `docs/10_adr/adr_01_index.md` | Read to confirm the ADR-008 index entry (title, domain, INV-01–05) still tracks ADR-008 after this Plan's edits; verified the edits do not change any indexed field, so no modification is required (REQ-006). | `docs/10_adr/adr_02_05_008...` (REQ-006) |

## Acceptance Criteria
- The manual procedure lists the EventBus service stop and the `-wal`/`-shm` sidecar handling explicitly, before the restore `cp`. (REQ-001)
- `db_07` 9.2 and 9.5 no longer contradict on backup verification. (REQ-002)
- No internal contradiction remains in ADR-008 that the plan resolves; `memories_vec`, Dry Run, Negative Consequences, Implementation References, and INV numbering are each either fixed or explicitly assigned to a maintainer decision. (REQ-003..REQ-005)
- `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain db` and `--domain agent` pass. (REQ-003..REQ-006)

## Tests
- N/A: no code change by the central claims (the automated restore path already quarantines sidecars and verifies backups). Validation is by the documentation and invariant checkers named in the Acceptance Criteria. Any doc/structural checker in `rules/toolchain.md` that runs on `docs/` changes MUST pass. If a maintainer decides the Dry Run code fix, `tests/db/test_db_recovery.py` gains a regression test then.

## Documentation Impact
Documentation-only for the central claims. `agent_10_01`, `db_07`, ADR-008, and the ADR index change. State intent, ownership, and failure behavior without copying command catalogs beyond the minimal operator steps the procedure carries. Name targets via `docs/00_index.md` "Document References by Task": the ADRs live under the database/failure-handling domains; `agent_10_01` under the agent domain; `db_07` under the db domain. ADR amendments require a maintainer approval record written by a maintainer (see Risks); this Plan fabricates none.

## Assumptions
- The automated restore path (`recover_corruption` + staging) is the safety baseline the manual procedure should mirror, and the operator can invoke its staging where practical.
- The two self-contradictions (db_07 9.2/9.5, ADR-008 Decision #7/#8) are fixable by wording without a maintainer decision, whereas the `memories_vec` correct classification, the Dry Run fix-vs-record choice, Negative Consequences, Implementation References completeness, and INV numbering require maintainer input.
- adrrev008 lands before adrrev009 to avoid ADR-008 file contention (both edit ADR-008 in different sections).
- adrrev007 and adrrev009 both name `agent_10_01` as a target but edit different sections: adrrev007 restates posture fail-closed behavior at the operations level (REQ-006); this Plan rewrites the Manual Recovery procedure (REQ-001). Compatible — no design contradiction; both land in the same commit touching non-overlapping sections.
- Fixing the db_07 9.2 claim and the agent_10_01 procedure does not depend on the maintainer-decision items.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the EventBus service holds `eventbus.sqlite` open in a *given* deployment (it does when the EventBus is enabled; the ADR lists it as a distinct target process). | None — resolved: `scripts/eventbus/app.py` is a persistent uvicorn HTTP server (subscribers stay connected for SSE). | State in the procedure as conditional on the EventBus being enabled; name it explicitly regardless (ADR-008 lists it as a target process). | False |
| UNK-02 | The correct `memories_vec` classification (system of record versus derived) — a maintainer business decision. | Maintainer decision. | Record the contradiction and assign resolution to a maintainer; do not fabricate. | False |
| UNK-03 | Whether to fix Dry Run to avoid the journal-mode change or accept and record the deviation in ADR-008 Known Deviations and the governance ledger. | Maintainer decision. | Record as a Known Deviation pending the decision; if a code fix is chosen, add a `tests/db/test_db_recovery.py` regression. | False |
| UNK-04 | Exact current wording of ADR-008 Decision #7/#8, Negative Consequences, Implementation References, and INV numbering at implementation time. | Read once at implementation; the plan cites the verified current state. | Read in `plan-to-implementation-procedure` Step 2. | False |
| UNK-05 | Whether the ADR-008 index entry in `adr_01_index` actually changes (depends on whether indexed ADR-008 fields change). | Read both files at implementation. | Modify `adr_01_index` only if the ADR-008 entry diverges. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Medium (high churn; operations doc read broadly) | 21 | Shared | not applicable (rsynced) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Medium (high churn) | 21 | Shared | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium (ADR read by index and authority checks) | 8 | Shared (governance author) | not applicable (rsynced) |

## Design
Path B classification is driven by file count (4 modification targets across three doc domains), not by runtime impact: no source, config, schema, or public interface changes occur by the central claims. The four analyses:

- **Architecture**: N/A for the Python import graph — the relevant dependency is the document cross-reference graph (which doc cites which invariant/procedure). Editing ADR-008 propagates through `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, and the ADR index; those gates bound the blast radius.
- **Dependency graphing**: the modification set is closed — exactly the four docs named. `agent_10_01` cites ADR-008 INV-18; `db_07` 9.5 is the code-matching half of the 9.2/9.5 pair; `adr_01_index` references ADR-008. No transitive source callers.
- **Historical**: `adr_01_index` (29 commits/30d) and `db_07` (21) and `agent_10_01` (21) are high-churn; re-read these three at implementation to avoid stepping on concurrent edits. ADR-008 (8) is lower churn.
- **Operational**: N/A — no ports, sockets, or database locks are touched. The standalone EventBus service (persistent uvicorn, `scripts/eventbus/app.py`) is the one runtime process relevant to the procedure wording, not to a code change.
- **Persisted schema**: N/A — no SQLite DDL or migration is touched.

The design choices left open are all maintainer decisions (UNK-02 memories_vec classification, UNK-03 Dry Run fix-vs-record). The plan records them as Unknowns and routes them; it does not resolve them. The narrow wording fixes (db_07 9.2, ADR-008 Decision #7/#8) are the only concrete content edits the plan commits to.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Harden the manual recovery procedure**
   - [ ] Add the EventBus service stop and the Agent stop to Manual Recovery Step 1 of `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`; move `-wal`/`-shm` sidecars aside before Step 5's `cp`; reference the adrrev005 fingerprint verification (REQ-001).
2. **Phase 2: Resolve the db_07 9.2/9.5 contradiction**
   - [ ] Correct the stale 9.2 claim (line 36) in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` to state backup integrity IS verified before use (REQ-002).
3. **Phase 3: Clean up ADR-008 wording**
   - [ ] Clarify Decision Detail #7/#8 wording in `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` so the tension between them resolves while preserving the factually accurate #8 (REQ-003).
4. **Phase 4: Route maintainer decisions**
   - [ ] Flag the `memories_vec` dual-listing (L92/L93) as a structural contradiction requiring a maintainer decision; record the Dry Run journal-mode deviation in Known Deviations pending the decision; do not fabricate approvals (REQ-004, REQ-005).
5. **Phase 5: Verify the ADR index still tracks ADR-008**
   - [ ] Confirm `docs/10_adr/adr_01_index.md` still tracks ADR-008 (title, domain, INV-01 to INV-05) after the ADR-008 edits; update only if it diverges (governance-gated amendment record) (REQ-006).
6. **Phase 6: Deployment & Verification**
   - [ ] Run `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain db`, `--domain agent`, and `check_docs_japanese.py`; confirm no invariant/Known Deviation regressed outside intent (all REQs).

### Release units
N/A: no release unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_01...` | Cross-domain claim consistency (manual recovery vs automated path) | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |
| `docs/41_db/db_07...` | Cross-domain claim consistency | `uv run python tools/check_docs_consistency.py --domain db` | Pass |
| `docs/10_adr/adr_02_05_008...` | Structural + invariant + Known Deviation sync | `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py` | No invariant/reference changed outside intent; Dry Run deviation recorded consistently |
| `docs/10_adr/adr_01_index.md` | Index consistency | `uv run python tools/check_adr_structure.py` (ADR-index gate) | ADR-008 entry consistent |
| All edited docs | Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Risks
- **Risk**: ADR content edits trip `check_adr_structure.py` / `check_adr_invariant_matrix.py` / `check_known_deviation_sync.py` (ERROR when an invariant, reference, test citation, Known Deviations, or Approval text changed) because the tools measure any body change. → **Mitigation**: scope each ADR edit to the single clause under change, keep all other text byte-identical, and re-run the checkers against `HEAD` before committing; treat a finding as scope creep to remove.
- **Risk**: ADR amendments require a maintainer approval record. → **Mitigation**: the implementation writes the approval record; this Plan records the requirement and fabricates none.
- **Risk**: The `memories_vec` classification, Dry Run fix-vs-record, Negative Consequences, Implementation References, and INV numbering are maintainer decisions; editing them without a decision risks fabricating policy. → **Mitigation**: leave them as Unknowns (UNK-02/UNK-03/UNK-04) with a Resolution Path; only fix unambiguous wording (db_07 9.2, Decision #7/#8).
- **Risk**: High-churn docs (`adr_01_index` 29, `db_07` 21, `agent_10_01` 21 commits/30d) risk stepping on concurrent doc edits. → **Mitigation**: re-read the files at implementation and re-run the doc checkers.
- **Risk**: adrrev008 and adrrev009 both edit ADR-008. → **Mitigation**: sequence adrrev008 first (it adds the mcp_dedup matrix row); this Plan edits other ADR-008 sections. Recorded as a sequencing dependency in Scope.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Harden the manual recovery procedure in `agent_10_01` | Pending | — | — | |
| 2 | Resolve the db_07 9.2/9.5 contradiction | Pending | — | — | |
| 3 | Clarify ADR-008 Decision #7/#8 wording | Pending | — | — | |
| 4 | Route maintainer decisions (memories_vec, Dry Run) | Pending | — | — | |
| 5 | Update the ADR index | Pending | — | — | |
| 6 | Run documentation and invariant checkers | Pending | — | — | |

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
- **Source issue**: `issues/20261109-112922_adrrev009_adr008-recovery-align.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-233648
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (stale WAL replay + unlinked-file); Adversarial Verification Claim 1/3; Required Changes (rewrite manual procedure) | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | 1 | EventBus stop + sidecar handling before restore | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-002 | Adversarial Verification Claim 5; Required Changes (make 9.2/9.5 consistent) | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | 2 | 9.2 matches 9.5/code | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-003 | Adversarial Verification Claim 8; Required Changes (rewrite Decision #7) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 3 | No internal #7/#8 tension | `check_adr_structure.py`, `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-004 | Adversarial Verification Claim 9; Unresolved Questions (memories_vec classification) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 4 | Contradiction flagged, not fabricated | `check_adr_invariant_matrix.py` | Needs confirmation (maintainer) |
| REQ-005 | Adversarial Verification Claim 7; Required Changes (Dry Run deviation) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 4 | Deviation recorded per maintainer decision | `check_known_deviation_sync.py` | Needs confirmation (maintainer) |
| REQ-006 | Target Files or Areas (adr_01_index listed); Reason for Change (index timing) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 5 | Index tracks ADR-008 after ADR-008 edits | `check_adr_structure.py` | Confirmed by repository evidence |
