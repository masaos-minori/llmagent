## Goal
Remove change-history passages from the current-specification documents (amendment sections and narratives, "replaces the previous", renamed-field notes, plan and issue IDs, dates in parentheses), align the policy text that still allows ADR Amendments, and correct the two runtime statements that contradict ADR-004 and the code (the subprocess retry wording in `security_01` and the definition of FATAL in `mcp_06_09`), without changing any normative decision, approval record, or invariant.

## Priority
Medium

## Scope
- **In-Scope**: History wording in ADR-001, ADR-003, ADR-008, ADR-010 (Amendment sections only), ADR-013, the ADR index Status cells and one paragraph, `db_01`, `db_03_07`, `db_07`, `eventbus_06`, `mcp_03_03`; the `governance_01` paragraph that keeps ADR Amendments as an exception; the `security_01` retry row and the `mcp_06_09` FATAL definition. A decision hidden in a history passage is rewritten in current tense, not deleted.
- **Out-of-Scope**: Changing runtime behavior of reload or retry; the `/reload` and `DiagnosticStore` live-read exception for ADR-002 (maintainer decision, UNK-01); approval records and invariants (untouched); hardening the checkers (the checker-hardening issue, which this work precedes); the ADR-010 Withdrawal record and any ADR-010 content other than its two Amendment sections; adding approval records (the approval-ledger Plan, which must not add per-amendment records for amendments removed here); items verified as not history (ADR-003 "Across Environments" and its Out of Scope line, `eventbus_03`, any `schema version mismatch` text).
- **Dependencies**: None to start. This Plan blocks the checker-hardening issue (adrrev018), which needs a clean corpus. Sequencing: several of these documents are also edited by other ADR and documentation Plans; the edits are to different passages (see Assumptions).

## Background
The Current-Specification-Only Policy (`governance_01`) keeps only the current system in active documents. A maintainer decision of 2026-11-09 says ADR amendment history is not needed in ADRs: remove amendment sections and narratives and keep the current decision text and the current approval record. Verification (2026-11-11) found every passage named in the issue still present and further history the issue did not list: ADR-001's `wflease001` Amendment, ADR-010's `ragcorpus001` and `adrrag002` Amendments, "amended 2026-11-10 ..." in three index Status cells, ADR-013's plan ID and "owner decision 2026-10-30" note, `db_01`'s "facade was deleted (2026-11-07)", `eventbus_06`'s "was removed at version 6", and `db_03_07`'s `wfaudit010`. Three items the issue could not confirm are refuted (`eventbus_03` plan IDs, ADR-003's title and scope lines, a `security_01` schema-version phrase). `governance_01` still says an ADR Amendment is the one allowed exception, which contradicts the decision. `security_01` calls the subprocess recovery an "Automatic retry" although ADR-004 allows one startup retry and a crashed server is only restarted on the next dispatch; `mcp_06_09` defines FATAL as "may be partially functional" while `agent_10_01` and its own rules say startup is aborted.

## Problem
- History in current documents forces readers to work out which parts are current, and a superseded amendment can be mistaken for a valid decision; git and the issues already keep the history.
- The policy paragraph that permits Amendments contradicts the maintainer decision and the removal.
- Inconsistent runtime statements mislead operators (waiting for an automatic retry that does not happen; two definitions of FATAL make startup logs ambiguous).

## Reason for Change
The forbidden-pattern checks from the checker-hardening issue should start green, so the corpus must be clean first.

## Implementation Intent
Every listed document describes only current behavior; each retry and FATAL statement is stated once and identically, with other documents referencing the owning ADR. Removing history changes no normative decision: where an amendment holds a still-valid rule, that rule must already be in the current sections or is rewritten there in current tense before the amendment is removed.

## Requirements
- `REQ-001`: Remove the history passages from the ADR bodies: ADR-008's Amendment section, its "removed by compatrm001" Review Trigger wording (rewritten as the current trigger), and the Amendment Approval Mapping paragraph; ADR-001's Amendment (`wflease001`); ADR-010's two Amendment sections; ADR-013's plan ID and "breaking change (owner decision 2026-10-30)" wording; ADR-003's "regardless of Profile" leftovers, keeping every decision, invariant, and the current approval record intact.
- `REQ-002`: Remove the history wording from the ADR index (the "amended ... / superseded ..." parentheticals in the ADR-004, ADR-006, ADR-008, and ADR-013 Status cells and the ADR-008 amendment paragraph), leaving the Status value and the generated sections untouched.
- `REQ-003`: Update `governance_01` "ADR Responsibilities and Historical Content" so an ADR holds no Amendment section: current-contract sections are complete on their own, and the Amendment-as-exception sentence is removed.
- `REQ-004`: Remove the history wording from the reference documents: `db_01` (facade deletion date), `db_03_07` (compatrm001, dbmig001, `wfaudit010` references), `db_07` (the former `migrate` policy note, the "formerly (mis)labeled" field note, and the rename blockquote), `eventbus_06` ("removed at version 6"), and `mcp_03_03` ("replaces the previous ... before this change"), each rewritten as current behavior.
- `REQ-005`: `security_01` states the recovery behavior as ADR-004 and the code define it (one retry at subprocess startup, restart on the next tool dispatch otherwise, manual restart for persistent servers), and `mcp_06_09` defines FATAL as "startup is aborted", identical to `agent_10_01`.
- `REQ-006`: A final search of `docs/` for the history patterns (amendment, superseded, "replaces the previous", "was removed", "renamed", "formerly", plan and issue IDs, dates in parentheses) finds no remaining current-specification passage in the listed documents; each remaining match is classified as legitimate current text.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | Remove the "ADR Amendment is the one exception" sentence and the in-force/superseded marking text (line 304) | REQ-003 / AC-3 | Line 304 "An ADR Amendment is the one exception to the Current-Specification-Only Policy: it may remain ... marked either in force ... or superseded" (checked in Step 2; missing from the issue's target list) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Remove the Amendment section (lines 73-75), rewrite the Review Trigger (line 363), remove the Amendment Approval Mapping bullet (line 384) | REQ-001 / AC-1 | Line 73 "### Amendment (dbmig001, 2026-10-30)", line 75 "Historical, superseded 2026-11-07 (source compatrm001)", line 363 "removed by compatrm001", line 384 mapping; the current-only schema policy is already stated in the current sections (line 60) (checked in Step 2) | `tools/check_adr_preservation.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Remove the Amendment (`wflease001`) section (lines 58-60) | REQ-001 / AC-1 | Line 58 "### Amendment (wflease001, 2026-11-01)"; Decision Details item 11 already states the lease-expiry rule (checked in Step 2; missing from the issue's target list) | `tools/check_adr_preservation.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Remove the two Amendment sections (lines 94-100); the Withdrawal record is untouched | REQ-001 / AC-1 | Lines 94 and 98 "### Amendment (ragcorpus001, 2026-10-31)" and "### Amendment (adrrag002, 2026-11-08)" (checked in Step 2; missing from the issue's target list) | `tools/check_adr_preservation.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Remove "regardless of Profile" at line 47 and in Decision Detail 7 (line 77) | REQ-001 / AC-1 | Lines 47 and 77; ADR-004 applies one policy to every environment and mentions Profile only in a rejected alternative (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Remove the plan ID `EBAUTHGEN001` and the "deliberate breaking change ... (owner decision 2026-10-30)" wording in Decision Detail 12 (line 95), keeping the 422 rule | REQ-001 / AC-1 | Line 95 (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | Remove "amended ..." and "superseded ..." from the ADR-004, ADR-006, ADR-008, ADR-013 Status cells (lines 48, 50, 52, 56) and the ADR-008 amendment paragraph (line 63) | REQ-002 / AC-2 | Lines 48, 50, 52, 56, 63 (checked in Step 2) | `tools/generate_adr_authority.py --check`, `tools/check_adr_structure.py` | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | Rewrite "the `db.store` re-export facade was deleted (2026-11-07) and must not be reintroduced" as a current rule (line 36) | REQ-004 / AC-4 | Line 36 (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Rewrite lines 50, 80, 84, and 145 (compatrm001, wfaudit010, dbmig001 history) as current statements | REQ-004 / AC-4 | Lines 50 "the former migration machinery was removed by the compatrm001 plan", 80 "(wfaudit010)", 84, 145 "established by dbmig001 was removed by the compatrm001 plan" (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Remove the "former per-domain `migrate` policy" note (line 179), the "formerly (mis)labeled `rpo_window_seconds`" sentence (line 182), and the rename blockquote (lines 188-190) | REQ-004 / AC-4 | Lines 179, 182, 188-190 (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Rewrite "the duplicate table-level `FOREIGN KEY` was removed at version 6" as the current schema fact (line 35) | REQ-004 / AC-4 | Line 35 (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Remove "This replaces the previous per-call random key: before this change ..." (lines 42-44), keeping the current key derivation | REQ-004 / AC-4 | Line 42 (checked in Step 2) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Modify | Define FATAL as "startup is aborted" (line 36), replacing "The system may be partially functional" | REQ-005 / AC-5 | Line 36 versus lines 50, 56, 59, 60 ("startup blocked") and `agent_10_01` line 63 ("aborting startup") (checked in Step 2) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify | Correct "Automatic retry (subprocess), manual restart (persistent)" (line 188) | REQ-005 / AC-5 | Line 188 versus ADR-004 Exceptions (single startup retry), line 213 (already correct), and `agent_10_05` (`ensure_ready()` on the next dispatch) (checked in Step 2) | `tools/check_docs_consistency.py --domain overview` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Owns the single-retry rule and the FATAL/abort semantics; the other documents reference it | REQ-005 |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | States "A configuration change requires restarting the owning process"; unchanged here (UNK-01) | REQ-006 |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | FATAL definition "aborting startup" (line 63) that `mcp_06_09` must match; no change needed | REQ-005 |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Runtime restart on the next dispatch (`ensure_ready()`), the behavior `security_01` must state | REQ-005 |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Documents `/reload` scope and the `diagnostics.*` live read | REQ-006 |
| `scripts/agent/shared/retry_helper.py` | `retry_once_with_delay()` single retry | REQ-005 |
| `scripts/agent/startup_mcp_starter.py` | Subprocess start with its single retry and `[fatal]` re-raise | REQ-005 |
| `tools/check_docs_content_policy.py` | Detects change-history forms in active documents; run, not modified | REQ-006 |
| `tools/check_compat_shims.py` | `--check-removed-names` detection (opt-in); run, not modified | REQ-006 |
| `tools/check_adr_preservation.py` | Reports Approval-text and decision-wording changes that must be explained | REQ-001 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | An ADR edit that does not change the decision does not reopen approval | REQ-001 |

## Acceptance Criteria
- AC-1: ADR-001, 003, 008, 010, and 013 contain no amendment section, plan or issue ID, or change-history parenthetical in the edited passages, and every decision, invariant, and current approval record is unchanged except the removed Amendment Approval Mapping bullet (`REQ-001`).
- AC-2: The ADR index Status cells and paragraph carry no "amended" or "superseded" history (`REQ-002`).
- AC-3: `governance_01` no longer permits an ADR Amendment section (`REQ-003`).
- AC-4: `db_01`, `db_03_07`, `db_07`, `eventbus_06`, and `mcp_03_03` describe only current behavior in the edited passages (`REQ-004`).
- AC-5: `mcp_06_09` and `agent_10_01` define FATAL identically, and `security_01` states the recovery and retry behavior as ADR-004 and the code define it (`REQ-005`).
- AC-6: A final `docs/` search finds no unclassified history match in the listed documents (`REQ-006`).
- AC-7: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_adr_authority.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `generate_adr_authority.py --check`, and `check_docs_consistency.py` for each touched domain pass; `check_adr_preservation.py` reports only intended, justified changes (the removed Amendment text and the Amendment Approval Mapping bullet).

## Tests
N/A: documentation-only; no Python file is modified. The checkers in the Validation plan gate the edits.

## Documentation Impact
All fourteen documents above change; locate them through `docs/00_index.md` "Document References by Task" (governance, db, eventbus, mcp, security areas). State current behavior and failure behavior only; no change narratives. Write in English.

## Assumptions
- The maintainer decision of 2026-11-09 also covers ADR-001 and ADR-010 (the issue named only the ADR-008 Amendment as an example of "amendment history"); ADR-010's Withdrawal record is a status record, not an Amendment, and stays (UNK-02 confirms ADR-010).
- Removing an Amendment is a wording edit, not a decision change (`governance_05`: an ADR edit that does not change the decision does not reopen approval), so no new approval record is required; `check_adr_preservation.py` reports the removed Approval-section bullet as an ERROR, which is the intended, explained change.
- Where an Amendment holds a still-valid rule, the rule is already in the current sections (ADR-008 line 60 states the current-only schema policy; ADR-001 Decision Detail 11 states lease expiry); the implementer confirms this per Amendment before removing it and rewrites in current tense where it is not.
- Overlap judgment (`tools/check_plan_target_overlaps.py`): ADR-008 and the ADR index are also targeted by other ADR Plans (recovery, ledger, EventBus specification, index matrix, authority format), ADR-013 by the EventBus authorization and authority-format Plans, `db_07` by the recovery and RAG consistency Plans, and `security_01` by the RAG consistency Plan; compatible, because this Plan edits only the history passages and Status wording, not the decision text or tables those Plans change.
- The `/reload` and `DiagnosticStore` live-read contradiction with ADR-002 is not resolved here; the documents keep their current statements until the maintainer decides (UNK-01).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `/reload` hot reload and the live `DiagnosticStore` read of `agent.toml` become explicit ADR-002 exceptions or require a restart | Maintainer decision; ADR-002 says "A configuration change requires restarting the owning process" and registers no exception | Maintainer decides; a follow-up ADR-002 edit or a behavior issue implements it, with a pending approval record | False |
| UNK-02 | Whether ADR-010's Amendment sections are removed with the others | The maintainer decision named ADR amendment history generally; ADR-010 is withdrawn | Assumed yes; the maintainer confirms at review, and the rows can be dropped by plan amendment | False |
| UNK-03 | Whether each Amendment's rule already exists in the current sections | Each Amendment was read, not compared line by line with the current sections | Phase 1 compares them; any rule only in an Amendment is rewritten into the current sections first | False |
| UNK-04 | Whether further history passages exist in the listed documents beyond those found | The search patterns found the listed passages and the extras above; other phrasings may exist | Phase 3 re-runs the search and the content-policy checker and classifies every match | False |
| UNK-05 | Whether a Known Issue or Needs Confirmation entry cites a removed passage | Not searched | Run `check_known_deviation_sync.py` and `check_needs_confirmation_inventory.py` after the edits | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Modify | Medium (policy read by every documentation workflow) | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium | 8 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium | 7 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Low (withdrawn ADR) | 7 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Medium | 7 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Medium | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (CI-checked; high churn) | 30 | N/A | not applicable (docs) |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | Low | 8 | N/A | not applicable (docs) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Low | 4 | N/A | not applicable (docs) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Low | 20 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Low | 12 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Modify | Low | 9 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Modify | Low | 5 | N/A | not applicable (docs) |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify | Low | 15 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files; ADR bodies and a governance policy). Findings from the inspection:
- Architecture and dependency graph: documentation only; no import, port, or process involved. The removed passages are referenced by no checker as required content: `check_adr_structure.py` requires an in-force/superseded marker only for an Amendment that exists, and `check_adr_preservation.py` compares invariants, references, test citations, Known Deviations, and Approval text against `HEAD`.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: none. Persisted schema: not applicable. Consumer scan: no persisted schema, public API, or shared constant changes (`not affected`).
- Ordering: `governance_01` is edited in the same phase as the ADR Amendment removals so the policy never permits what the ADRs no longer contain; the ADR index is edited after the ADR bodies.
- Approval handling: the removed ADR-008 Amendment Approval Mapping bullet is the only Approval-section text change; `check_adr_preservation.py` reports it as ERROR and the report explains it as the maintainer-decided removal of amendment history (no approval record is added, per the ledger Plan's scope).
- Why current-tense rewriting rather than deletion: the issue forbids deleting a normative decision hidden in history; each rewrite states the rule as a present fact (for example the current-only schema policy and the single canonical DDL).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirmation and baseline** (all target files; documentation only)
   - [ ] Re-run the history search over `docs/` and the content-policy checker; compare each Amendment's rule with the current sections (UNK-03) and record what each removal keeps in current tense.
   - [ ] Run `uv run python tools/check_adr_preservation.py` for a baseline.
2. **Phase 2: Policy and ADR bodies** (REQ-001, REQ-003; `docs/00_governance/governance_01_documentation-policy.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
   - [ ] Remove the Amendment sections and the Amendment Approval Mapping bullet; rewrite the ADR-008 Review Trigger, ADR-013 Decision Detail 12, and ADR-003 "regardless of Profile" wording in current tense.
   - [ ] Update the `governance_01` Amendment-exception paragraph in the same phase.
3. **Phase 3: ADR index** (REQ-002; `docs/10_adr/adr_01_index.md`)
   - [ ] Remove the history parentheticals and the ADR-008 paragraph; run `generate_adr_authority.py --check` (the guarded sections are not hand-edited).
4. **Phase 4: Reference documents and runtime statements** (REQ-004, REQ-005; `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`)
   - [ ] Rewrite each history passage as current behavior; fix the FATAL definition and the `security_01` retry row.
5. **Phase 5: Verification** (REQ-006; all target files)
   - [ ] Re-run the history search and classify each remaining match; run the Validation plan commands.
   - [ ] Run `check_adr_preservation.py` and explain every reported change; report the maintainer decisions still open (UNK-01, UNK-02) and write no approval.
   - [ ] No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All target documents | Structure and formatting | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` | Pass |
| All target documents | Content policy and change-history forms | `uv run python tools/check_docs_content_policy.py --strict` | Pass |
| All target documents | No Japanese text | `uv run python tools/check_docs_japanese.py` | Pass |
| ADR files | ADR structure, authority, matrix, generated sections | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `generate_adr_authority.py --check` | Pass |
| ADR files | Decision-change guard | `uv run python tools/check_adr_preservation.py` | Only the removed Amendment text and the Amendment Approval Mapping bullet, each explained |
| Touched domains | Claims against code and config | `uv run python tools/check_docs_consistency.py --domain db`, `--domain eventbus`, `--domain mcp`, `--domain overview` | Pass |
| Governance and ADR docs | Deviation and Needs Confirmation inventories | `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` | Pass |
| All target documents | History search (opt-in removed-name check) | `uv run python tools/check_compat_shims.py --check-removed-names` | No unclassified match in the listed documents |

Validation quality baseline: `N/A: no Python target` (documentation-only).

## Risks
- **Risk**: Removing an Amendment deletes a rule that exists only there. → **Mitigation**: Phase 1 compares each Amendment with the current sections first (UNK-03); a rule found only in an Amendment is rewritten into the current sections before removal.
- **Risk**: `check_adr_preservation.py` reports ERROR for the removed Approval-section bullet and the report is read as an unapproved decision change. → **Mitigation**: The report states that it is the maintainer-decided removal of amendment history, that no decision, invariant, or current approval record changes, and the ERROR is not suppressed.
- **Risk**: Editing `governance_01` while ADRs still carry Amendments (or the reverse) leaves the policy and the corpus inconsistent mid-change. → **Mitigation**: Both are edited in Phase 2 of the same change.
- **Risk**: Rewriting history as current text changes meaning (for example the schema-fingerprint or retry rules). → **Mitigation**: Each rewrite is checked against code through `check_docs_consistency.py` and the cited source before the passage is removed.
- **Risk**: Edits to high-churn files (`adr_01_index.md`, `db_07`, `security_01`) conflict with sibling Plans. → **Mitigation**: Edit only the listed passages and rerun `tools/check_plan_target_overlaps.py`.
- **Risk**: The ADR-002 reload contradiction stays unresolved after this change. → **Mitigation**: Recorded as UNK-01 and reported; this Plan changes no reload statement.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirmation and baseline | Pending | — | — | |
| 2 | Policy and ADR bodies (REQ-001, REQ-003) | Pending | — | — | |
| 3 | ADR index (REQ-002) | Pending | — | — | |
| 4 | Reference documents and runtime statements (REQ-004, REQ-005) | Pending | — | — | |
| 5 | Verification (REQ-006) | Pending | — | — | |

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
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-110144
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_01_index.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/22_mcp/mcp_03_03_transport-and-health.md`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Constraints: remove amendment sections, including the ADR-008 Amendment and Amendment Approval Mapping | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Step 2 | AC-1 | `check_adr_preservation.py`, `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes: re-run the search; verification found the ADR-001 Amendment | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Step 2 | AC-1 | `check_adr_preservation.py` | Derived from confirmed evidence |
| REQ-001 | Same; verification found two ADR-010 Amendments | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Step 2 | AC-1 | `check_adr_preservation.py` | Derived from confirmed evidence |
| REQ-001 | Needs confirmation resolved: ADR-003 leftover terms (Profile) | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Step 2 | AC-1 | `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-001 | Needs confirmation resolved: ADR-013 "breaking change (2026-10-30)" | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 2 | AC-1 | `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-002 | Background: the index line describing ADR-008 as amended and superseded | `docs/10_adr/adr_01_index.md` | Step 3 | AC-2 | `generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-003 | Constraints: maintainer decision that ADR amendment history is not needed | `docs/00_governance/governance_01_documentation-policy.md` | Step 2 | AC-3 | `check_docs_quality.py` | Derived from confirmed evidence |
| REQ-004 | Background: `db_01` "facade deleted (2026-11-07)" (resolved as present) | `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Step 4 | AC-4 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Background: `db_03_07` migration-history passages | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Step 4 | AC-4 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Background: `db_07` renamed-field note | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Step 4 | AC-4 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Needs confirmation resolved: `eventbus_06` "removed in version 6" | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Step 4 | AC-4 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-004 | Background: `mcp_03_03` "replaces the previous" | `docs/22_mcp/mcp_03_03_transport-and-health.md` | Step 4 | AC-4 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-005 | Required Changes: define FATAL as "startup is aborted" in `mcp_06_09` and `agent_10_01` | `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Step 4 | AC-5 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-005 | Required Changes: correct the retry wording in `security_01` | `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Step 4 | AC-5 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-006 | Required Changes: re-run the search and remove every passage found | `docs/10_adr/adr_01_index.md` | Step 5 | AC-6 | `check_compat_shims.py --check-removed-names`, `check_docs_content_policy.py --strict` | Explicit in issue |
