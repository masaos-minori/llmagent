## Goal
- Make every `UNK-` or `NC-` identifier cited in an ADR resolve to exactly one `governance_03` entry (or leave the ADR), make the deviation ledger match the code by closing SHARED-001, and replace line-number references, with `tools/check_known_deviation_sync.py` enforcing the identifier rule.

## Priority
Medium

## Scope
- **In-Scope**: registering the pending EventBus producer and consumer item in `governance_03`; citing it from ADR-006 and ADR-013; removing the plan-local identifier from ADR-009; replacing plan-local identifiers and line-number references in the three listed script comments (and regenerating the reference document built from one of them); closing SHARED-001; replacing the line numbers in the SHARED-002 entry; replacing the guide sentence; the checker rule for ADR documents and its tests; the tool and rule descriptions.
- **Out-of-Scope**: renumbering identifiers inside plan files; changing deviation substance; plan-local identifiers in the 11 other `scripts/` files and in the non-ADR documents (UNK-01, UNK-02); the SHARED-001 and SHARED-002 wording in `tools/check_compat_shims.py` (UNK-02).
- **Dependencies**: N/A: none open. The Issue's dependency, the ADR-008 data lifecycle work (adrchk008), is complete and archived. A compatible overlap with the pending adrchk013 procedures is recorded in Assumptions.

## Background
The Issue was filed from the consolidated ADR review (`memo-issue.md`, package `ADRCHK2-H12`) and re-verified against current source in Step 2 of this cycle. Plan-local `UNK-NN` identifiers were written into ADRs, code comments, and generated documents; they are unique only inside their own plan, and `governance_03` holds no `UNK-` entry. The Known Deviation sync check takes its identifier prefixes from the ledger's own ordering convention (RAG, DESIGN, AGENT, MCP, DEPLOY, EVENTBUS, SHARED, CI) and the prefixes of parsed entries, so `UNK-` and `NC-` references are never examined.

## Problem
- `UNK-01` has at least five meanings in current source: the EventBus producer and consumer model (ADR-006 Decision 14, ADR-013), the NACK idempotency key (`scripts/eventbus/ack_route.py`), a resolved FTS5 decision (ADR-009), the dry-run output detection (`scripts/mcp_servers/dispatch.py`), and virtual-table shape handling (`scripts/shared/schema_fingerprint.py`); `UNK-03` is reused in the same way. The sync check cannot detect any of it.
- `governance_03` has no entry for the item that ADR-006 and ADR-013 call `UNK-01`.
- `adr_00_document-guide.md` says "No confirmed deviation remains" while the ledger holds open entries.
- SHARED-001 is fixed in code and covered by `test_run_integrity_check_keeps_rollback_journal_mode`, yet the ledger lists it as open and ADR-008 `## Known Deviations` still cites it.
- The SHARED-002 ledger entry cites line numbers of the ADR-008 matrix, and a `scripts/shared/tool_constants.py` comment cites "lines 4-21".

## Reason for Change
Plan-local identifiers misdirect a reader to the wrong item, a false absence claim hides open deviations, and a closed deviation kept open misleads the operator. Nothing makes the change time-sensitive.

## Implementation Intent
- Identifiers cited outside a plan are global and resolve in `governance_03`; the checker reports a cited identifier that has no entry or more than one.
- The guide points to the ledger and makes no count or absence claim; the ledger reflects the code.
- References name a section or a symbol, never a line number.
- Comments state the current rule without a plan identifier; a pointer, where one is needed, names the plan path.

## Requirements
- `REQ-001`: `governance_03` registers the pending EventBus producer and consumer item as one new entry with a unique identifier (the next free NC number).
- `REQ-002`: ADR-006 Decision 14 and ADR-013 cite that entry instead of the plan-local identifier.
- `REQ-003`: ADR-009 no longer cites the plan-local identifier `UNK-01` (fallout of `REQ-008`, no decision change).
- `REQ-004`: The plan-local identifiers and line-number references in `scripts/eventbus/ack_route.py`, `scripts/agent/services/config_validators.py`, and `scripts/shared/tool_constants.py` are replaced, and the generated reference document built from the `config_validators.py` docstring is regenerated.
- `REQ-005`: SHARED-001 is closed with the result of `test_run_integrity_check_keeps_rollback_journal_mode`: its ledger entry is removed and its ADR-008 `## Known Deviations` bullet is removed.
- `REQ-006`: The SHARED-002 ledger entry cites section names instead of line numbers.
- `REQ-007`: The guide sentence is replaced by a pointer to the ledger.
- `REQ-008`: The sync check reports an `UNK-` or `NC-` reference in `docs/10_adr/` that does not resolve to exactly one `governance_03` heading, with fixtures that fail today.
- `REQ-009`: The same rule covers `scripts/` and the remaining plan-local comments are replaced (gated on UNK-01).
- `REQ-010`: The tool description and the GV-022 rule description state the new rule (fallout of `REQ-008`).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Ledger entries | Add the NC entry for the producer and consumer item, remove the SHARED-001 entry, replace the line numbers in SHARED-002 | REQ-001, REQ-005, REQ-006 / AC-1, AC-4, AC-5 | Part 2 holds NC-001 and NC-002 only; no `UNK-` entry exists; SHARED-001 is at `#### SHARED-001` with `Status: open`; SHARED-002 says "Line 92 ... line 93" (checked in Step 2) | `tools/check_needs_confirmation_inventory.py`, `tools/check_known_deviation_sync.py`, `tools/check_docs_quality.py` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Known Deviations paragraph | Replace the sentence "No confirmed deviation remains." with a pointer to the ledger | REQ-007 / AC-3 | Line 23 of the guide holds the sentence while the ledger holds SHARED-002 as open (checked in Step 2) | `tools/check_docs_quality.py`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Known Deviations | Remove the SHARED-001 bullet | REQ-005 / AC-4 | `## Known Deviations` holds the SHARED-001 and SHARED-002 bullets; the Issue's "Not applicable" claim does not hold for this section (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Decision 14 | Replace `(UNK-01)` with the new NC identifier | REQ-002 / AC-1 | Decision 14 reads "not yet defined (UNK-01)" and points to `governance_03` (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Caller model status | Replace `(Plan UNK-01)` with the new NC identifier | REQ-002 / AC-1 | The paragraph reads "registered through `governance_03` (Plan UNK-01)" (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Basis wording | Remove the plan-local `(UNK-01)` token; fallout of REQ-008, outside the Issue's Target Files | REQ-003 / AC-1 | "Resolved by the owner on 2026-11-19 (UNK-01)" is a third `UNK-` token in `docs/10_adr/` (checked in Step 2) | `tools/check_known_deviation_sync.py`, `tools/check_adr_preservation.py` | Verified |
| `scripts/eventbus/ack_route.py` | Comment | Restate the NACK idempotency-key rule without `UNK-01` | REQ-004 / AC-2 | The comment "UNK-01 (recommended): reject a NACK without an idempotency key" precedes the `idempotency_key` check (checked in Step 2) | `tests/eventbus/` (comment only, no test change) | Verified |
| `scripts/agent/services/config_validators.py` | Docstring | Drop `preserved per UNK-03` from the `validate_diagnostics_retention_days` docstring | REQ-004 / AC-2 | The docstring reads "(<= 0 disables purge; preserved per UNK-03)" (checked in Step 2) | `tests/agent/services/test_typed_validators.py` | Verified |
| `scripts/shared/tool_constants.py` | Comment | Replace "this module's header (lines 4-21)" with a reference to the module header section | REQ-004 / AC-2 | The `ALL_SIDE_EFFECTING_TOOLS` comment says "(lines 4-21)" (checked in Step 2) | `tests/shared/` (comment only, no test change) | Verified |
| `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | Generated reference | Regenerate with the generator (never hand-edit); fallout of the docstring change | REQ-004 / AC-2 | Line 118 renders the `validate_diagnostics_retention_days` docstring including `UNK-03`; `generate_reference_table.py --check` reports no drift today (checked in Step 2 and Step 5) | `tests/tools/test_generate_reference_table.py` | Verified |
| `tools/check_known_deviation_sync.py` | Checker rule | Report an `UNK-` or `NC-` reference in `docs/10_adr/` that does not resolve to exactly one `governance_03` heading; extend to `scripts/` once UNK-01 is resolved | REQ-008, REQ-009 / AC-1, AC-6 | Prefixes come from `_PREFIX_CONVENTION_RE` and parsed entries, so `UNK` and `NC` are ignored; `collect_issues()` has five checks; 23492 bytes against the 24576 byte gate (checked in Step 2 and Step 5) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `tests/tools/test_check_known_deviation_sync.py` | Fixture tests | Add fixtures that fail today: an unresolved `UNK-` reference, a duplicated heading, a resolved `NC-` reference | REQ-008, REQ-009 / AC-1, AC-6 | The file holds 20 tests for the five existing checks (checked in Step 2) | `tests/tools/test_check_known_deviation_sync.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool description | Update the `check_known_deviation_sync.py` row; required by AGENTS.md Global Rule 9 | REQ-010 / AC-7 | The tool list describes the existing checks only (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Rule description | Update the GV-022 row for the new rule | REQ-010 / AC-7 | GV-022 describes the dangling and resolved-bullet checks (checked in Step 2) | `tools/check_docs_consistency.py`, `tools/check_docs_quality.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/recovery.py` | Evidence that the classification and Dry Run path open the database read-only (`_run_integrity_check(..., read_only=True)`) | REQ-005 |
| `tests/db/test_db_recovery.py` | Holds `test_run_integrity_check_keeps_rollback_journal_mode`, the named test | REQ-005 |
| `tools/check_needs_confirmation_inventory.py` | Rules for NC entries and inline markers | REQ-001 |
| `tools/generate_reference_table.py` | Regenerates the agent reference document | REQ-004 |
| `tests/tools/test_generate_reference_table.py` | Drift test for the generated reference | REQ-004 |
| `tools/check_compat_shims.py` | Cites SHARED-001 and SHARED-002 in a different meaning | UNK-02 |
| `implementations/20261120-111659_12_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md` | Pending adrchk013 procedure that edits `governance_03` Part 5 | Assumptions A1 |
| `implementations/20261120-111659_13_tools_TOOL_DESCRIPTIONS.md.md` | Pending adrchk013 procedure that edits other `TOOL_DESCRIPTIONS.md` rows | Assumptions A1 |

## Acceptance Criteria
- `AC-1`: `uv run python tools/check_known_deviation_sync.py` exits 1 on a fixture whose ADR cites an unresolved `UNK-` identifier, one whose identifier has two headings, and one whose `NC-` identifier is unresolved, and the fixtures fail before the rule; the live run exits 0; `grep -rn -E "UNK-[0-9]+" docs/10_adr` returns nothing; ADR-006 and ADR-013 cite the new entry and it resolves to exactly one heading (REQ-001, REQ-002, REQ-003, REQ-008).
- `AC-2`: The three script comments contain no `UNK-` token and no line number; `uv run python tools/generate_reference_table.py --check` reports no drift after regeneration (REQ-004).
- `AC-3`: The guide's Known Deviations paragraph makes no count or absence claim and points to the ledger (REQ-007).
- `AC-4`: `test_run_integrity_check_keeps_rollback_journal_mode` passes, `governance_03` has no `#### SHARED-001` heading, ADR-008 `## Known Deviations` does not cite SHARED-001, and the sync check passes (REQ-005).
- `AC-5`: The SHARED-002 entry cites section names and contains no line number (REQ-006).
- `AC-6`: After UNK-01 resolves, a fixture with an unresolved `UNK-` token in a `scripts/` comment makes the checker exit 1, and `grep -rn -E "UNK-[0-9]+" scripts` returns nothing (REQ-009). Open until UNK-01 resolves.
- `AC-7`: `tools/TOOL_DESCRIPTIONS.md` and the GV-022 row state the new rule and `uv run python tools/check_tool_descriptions_sync.py` passes (REQ-010).

## Tests
- `REQ-008`: fixtures for an unresolved `UNK-` reference, a duplicated heading, a resolved `NC-` reference, and an identifier outside `docs/10_adr/` that stays ignored, in `tests/tools/test_check_known_deviation_sync.py`, written first and shown failing.
- `REQ-009`: a fixture for an unresolved token in a `scripts/` comment, after UNK-01.
- `REQ-005`: run the named integrity test.
- `REQ-001` to `REQ-007`: no new test; the live checker runs, `tools/check_needs_confirmation_inventory.py`, and the reference drift check cover the data.

## Documentation Impact
Yes. Drivers: REQ-001, REQ-005, REQ-006 (the `governance_03` ledger and inventory), REQ-002, REQ-003, REQ-005 (ADR-006, ADR-008, ADR-009, ADR-013), REQ-007 (the ADR document guide), REQ-010 (the GV-022 rule description and the tool description), REQ-004 (the regenerated agent reference). Target documents are named by the Issue and by `docs/00_index.md` "Document References by Task" for the governance and ADR areas.

## Assumptions
- A1: The pending adrchk013 procedures edit `governance_03` Part 5 (ledger entries, gated), other `TOOL_DESCRIPTIONS.md` rows, and `governance_04` section 12; this Plan edits `governance_03` Parts 1 and 2, the `check_known_deviation_sync.py` rows, and the GV-022 row. It is a compatible overlap with adrchk013 (invariant matrix checks); falsified if a pending procedure edits the same entry or row.
- A2: The new entry is NC-003: Part 2 holds NC-001 and NC-002 only, and the item is a pending maintainer decision, which Part 2 tracks. A Known Issue entry would also need a Known Deviations bullet in ADR-006. Falsified if the owner wants the item in Part 1.
- A3: No approval text is written; the new entry records the question with `Assigned To` set to the maintainer and no decision.
- A4: SHARED-001 is closed on this evidence: the named test passes (1 passed in Step 2) and the classification path opens the database read-only (`scripts/db/recovery.py` lines 195, 228, 259, and 609). Falsified if the test fails when re-run before the edit.
- A5: The checker is 23492 bytes against the 24576 byte gate for `tools/` (headroom 1084 bytes), so the new rule is expected to need a split (Risks).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | 11 other `scripts/` files carry plan-local `UNK-` tokens: `agent/workflow/workflow_engine.py`, `agent/workflow/state_store.py`, `mcp_servers/dispatch.py`, `mcp_servers/web_search/web_search_service.py`, `metrics.py`, `health.py`, `search_provider.py`, `db/rag_consistency_queries.py`, `db/session_consistency.py`, `shared/schema_fingerprint.py`, `shared/security/startup_flow.py`; the Issue's Acceptance Criteria name `scripts/`, but its Target Files list only three comments | The owner's approval of a comment-only scope amendment, and for each token the plan path or the restated rule | Owner decision. On approval add the files with `tools/amend_plan.py` (class fallout, since the checker would fail without them). Phase 7 stays gated until then | False |
| UNK-02 | Plan-local tokens remain outside the Acceptance Criteria scope: 7 `UNK-` tokens in 6 non-ADR documents (`docs/41_db/db_07_api_and_operations-recovery-and-reference.md` twice, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`), and `tools/check_compat_shims.py` cites SHARED-001 and SHARED-002 in a different meaning | Whether these are in scope | Owner decision; file a follow-up Issue when out of scope | False |
| UNK-03 | The SHARED-002 entry may be stale: the ADR-008 matrix row for derived data already lists `memories_vec`, and the ADR bullet says the matrix now classifies it as derived only, pending AAL-027 | The owner's decision on the classification (an approval record) | Not changed here; only the line numbers are replaced | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. Bus Factor is 1 for every file: one author accounts for all commits (`git shortlog -sn HEAD`).

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium: read by the sync and NC checkers | 18 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 7 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Low | 18 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | 17 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low | 15 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Low | 5 | 1 | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Modify | Low: comment only | 13 | 1 | not applicable (rsynced) |
| `scripts/agent/services/config_validators.py` | Modify | Low: docstring only; feeds a generated reference | 2 | 1 | not applicable (rsynced) |
| `scripts/shared/tool_constants.py` | Modify | Low: comment only | 4 | 1 | not applicable (rsynced) |
| `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | Modify | Low: regenerated | 1 | 1 | not applicable (rsynced) |
| `tools/check_known_deviation_sync.py` | Modify | Medium: pre-commit hook and CI gate | 1 | 1 | not applicable (rsynced) |
| `tests/tools/test_check_known_deviation_sync.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: read by `check_tool_descriptions_sync.py` | 72 | 1 | not applicable (rsynced) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low | 13 | 1 | not applicable (rsynced) |

## Design
- **D1 Where the pending item lives**: a new Part 2 entry (NC-003) whose Source File is ADR-006 and whose Question is which component defines the EventBus producers and consumers and when. Alternative: a Part 1 Known Issue (rejected for now, A2): it would also need a Known Deviations bullet in ADR-006 and a Type value the item does not fit.
- **D2 Checker rule**: a new function over `discover_adr_docs()` that finds `\b(?:UNK|NC)-\d+\b` and requires exactly one `#### <ID>` heading across all of `governance_03` (Parts 1 and 2); zero or several is an `ERROR`. The scripts rule (UNK-01) reuses it with a different document set. Alternative: add `UNK` to the prefix set of the existing dangling check (rejected: it scans every document under `docs/` and would flag the six non-ADR documents of UNK-02). Alternative: a baseline file of grandfathered tokens (rejected: it is a tolerant mode).
- **D3 Comment text**: restate the rule without an identifier (for example "reject a NACK without an idempotency key"); name a plan path only where a pointer is needed. The identifier is not renamed inside plan files (Issue Constraint).
- **D4 Generated reference**: after the `config_validators.py` docstring change, regenerate `agent_14` with `tools/generate_reference_table.py --type agent`; it is never edited by hand.
- **D5 Validation quality baseline** (checked in Step 5): `radon cc` on the checker shows `parse_canonical_statuses` at C (13) and `parse_canonical_adr_targets` at C (11), neither of which this change touches, and no other function above B (8); `bandit` on the checker reports no issue; `vulture scripts/ --min-confidence 80` reports six findings in `scripts/rag/` and `scripts/shared/runtime_paths.py`, none in a target; diff-cover is N/A because the `scripts/` changes are comments and one docstring.
- **D6 Persisted schema check**: not applicable; no DDL or schema version changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. Phase 7 is gated: it starts only after the owner resolves UNK-01. Phases 1 to 4 and 6 each pass the checker on their own; Phase 5 runs after Phases 1 to 3 so that the ADR documents are clean.

1. **Phase 1: Register the pending EventBus item and cite it**
   - [ ] Add the NC entry (next free number, expected NC-003) with the 15 Part 2 fields, no approval text (REQ-001; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Replace `(UNK-01)` in Decision 14 with the NC identifier (REQ-002; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Replace `(Plan UNK-01)` with the NC identifier (REQ-002; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
2. **Phase 2: Close SHARED-001 and fix the SHARED-002 line numbers**
   - [ ] Re-run `test_run_integrity_check_keeps_rollback_journal_mode`; remove the SHARED-001 entry and replace the line numbers in the SHARED-002 entry with section names (REQ-005, REQ-006; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Remove the SHARED-001 bullet from `## Known Deviations` (REQ-005; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
3. **Phase 3: Guide sentence and ADR-009 token**
   - [ ] Replace the sentence with a pointer to the ledger (REQ-007; `docs/10_adr/adr_00_document-guide.md`)
   - [ ] Remove the plan-local `(UNK-01)` token, keeping the sentence's meaning (REQ-003; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`)
4. **Phase 4: Script comments and the generated reference**
   - [ ] Restate the NACK rule without `UNK-01` (REQ-004; `scripts/eventbus/ack_route.py`)
   - [ ] Drop `preserved per UNK-03` from the docstring (REQ-004; `scripts/agent/services/config_validators.py`)
   - [ ] Replace "lines 4-21" with a reference to the module header (REQ-004; `scripts/shared/tool_constants.py`)
   - [ ] Regenerate the agent reference with the generator and confirm `--check` passes (REQ-004; `docs/23_agent/agent_14_reference-api-subpackages-generated.md`)
5. **Phase 5: Checker rule for ADR documents**
   - [ ] Write the failing fixtures, then add the rule; when the size gate fails, split with `module_nodes.py` and record the new module with `tools/amend_plan.py` as fallout (REQ-008; `tests/tools/test_check_known_deviation_sync.py`, `tools/check_known_deviation_sync.py`)
6. **Phase 6: Documentation sync**
   - [ ] Update the tool row and the GV-022 row (REQ-010; `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`)
7. **Phase 7: Scripts rule and remaining comments (gated on UNK-01)**
   - [ ] Add the files of UNK-01 through `tools/amend_plan.py`, replace their plan-local tokens, then extend the rule to `scripts/` (REQ-009; `tools/check_known_deviation_sync.py`, `tests/tools/test_check_known_deviation_sync.py`)
8. **Phase 8: Validation, deploy hand-off, and close-out**
   - [ ] Run the validation sequence and the checkers named in Validation plan (REQ-001 to REQ-010; every target file)
   - [ ] Deploy hand-off: `scripts/` files change (comments and one docstring only), so hand off to `skills/deploy/SKILL.md` once the change is committed and pushed; deploying is the user's decision (REQ-004; `scripts/eventbus/ack_route.py`, `scripts/agent/services/config_validators.py`, `scripts/shared/tool_constants.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_known_deviation_sync.py` | Unit fixtures, failing first; live-repository run | `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`; `uv run python tools/check_known_deviation_sync.py` | Fixtures fail before and pass after the rule; the live run exits 0 |
| `tools/check_known_deviation_sync.py` | Lint, type, security, size | `uv run ruff format tools/check_known_deviation_sync.py`; `uv run ruff check tools/check_known_deviation_sync.py`; `uv run mypy tools/check_known_deviation_sync.py`; `uv run bandit tools/check_known_deviation_sync.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No finding; module size within the gate |
| `tests/tools/test_check_known_deviation_sync.py` | Lint and type | `uv run ruff check tests/tools/test_check_known_deviation_sync.py`; `uv run mypy tests/tools/test_check_known_deviation_sync.py` | No finding |
| `docs/10_adr/*.md`, `docs/00_governance/*.md` | Static checks | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_known_deviation_sync.py`; `uv run python tools/check_needs_confirmation_inventory.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_preservation.py` | No ERROR; no changed invariant, decision, or approval text |
| `scripts/eventbus/ack_route.py`, `scripts/agent/services/config_validators.py`, `scripts/shared/tool_constants.py` | Regression and generated-reference drift | `uv run pytest tests/eventbus tests/agent/services/test_typed_validators.py tests/shared -q`; `uv run python tools/generate_reference_table.py --check`; `uv run ruff check scripts/eventbus/ack_route.py scripts/agent/services/config_validators.py scripts/shared/tool_constants.py` | All pass; no drift |
| SHARED-001 closure | Named integration test | `uv run pytest tests/db/test_db_recovery.py -k keeps_rollback_journal_mode -q` | 1 passed |
| `tools/TOOL_DESCRIPTIONS.md` | Sync | `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| Whole change | Gate runner | `uv run python tools/run_validation_gates.py` | `Pass` |

## Risks
- **Risk**: The checker grows past the 24576 byte gate (headroom 1084 bytes) → **Mitigation**: Phase 5 re-runs `check_module_size.py`; when it fails, split the identifier rule into a new `tools/` module with `module_nodes.py` and record it with `tools/amend_plan.py` as fallout; keep the names that tests and the pre-commit hook import in the checker.
- **Risk**: The new rule fails on the live repository because an ADR cites an identifier that does not resolve → **Mitigation**: Phases 1 and 3 land first and the live run must exit 0 before Phase 5 ends; the three `UNK-` tokens in `docs/10_adr/` are the complete set (checked in Step 2).
- **Risk**: Removing SHARED-001 hides a still-open behavior → **Mitigation**: A4; the named test is re-run before the edit and a failure stops Phase 2.
- **Risk**: The scripts rule (Phase 7) is enabled before every token is replaced → **Mitigation**: Phase 7 is gated, its Execution Status row carries the gate, and AC-6 stays open until UNK-01 resolves.
- **Risk**: A comment edit in `config_validators.py` leaves the generated reference stale → **Mitigation**: Phase 4 regenerates it in the same phase and runs `generate_reference_table.py --check`, which also runs in CI.
- **Risk**: The new NC entry is read as an approval or a decision → **Mitigation**: A3; the entry records the question only and `check_adr_preservation.py` shows that no ADR decision text changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the pending EventBus item and cite it | Pending | — | — | |
| 2 | Close SHARED-001 and fix the SHARED-002 line numbers | Pending | — | — | |
| 3 | Guide sentence and ADR-009 token | Pending | — | — | |
| 4 | Script comments and the generated reference | Pending | — | — | |
| 5 | Checker rule for ADR documents | Pending | — | — | After Phases 1 to 3 |
| 6 | Documentation sync | Pending | — | — | |
| 7 | Scripts rule and remaining comments | Pending | — | — | Gated: UNK-01 |
| 8 | Validation, deploy hand-off, and close-out | Pending | — | — | |

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
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-124329
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/10_adr/adr_00_document-guide.md`; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`; `scripts/eventbus/ack_route.py`; `scripts/agent/services/config_validators.py`; `scripts/shared/tool_constants.py`; `docs/23_agent/agent_14_reference-api-subpackages-generated.md`; `tools/check_known_deviation_sync.py`; `tests/tools/test_check_known_deviation_sync.py`; `tools/TOOL_DESCRIPTIONS.md`; `docs/00_governance/governance_04_documentation-checks.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `governance_03` holds no entry for the ADR-006 and ADR-013 item (checked in Step 2) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 1 | AC-1 | `tools/check_needs_confirmation_inventory.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; ADR-006 Decision 14 and ADR-013 paragraph (checked in Step 2) | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 1 | AC-1 | `tools/check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; ADR-013 caller model status (checked in Step 2) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 1 | AC-1 | `tools/check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria; a third `UNK-` token in `docs/10_adr/` (checked in Step 2) | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | 3 | AC-1 | `grep` for `UNK-` in `docs/10_adr/` | Derived from confirmed evidence |
| REQ-004 | Required Changes; `ack_route.py` comment (checked in Step 2) | `scripts/eventbus/ack_route.py` | 4 | AC-2 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `config_validators.py` docstring (checked in Step 2) | `scripts/agent/services/config_validators.py` | 4 | AC-2 | `tests/agent/services/test_typed_validators.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `tool_constants.py` "lines 4-21" (checked in Step 2) | `scripts/shared/tool_constants.py` | 4 | AC-2 | `uv run pytest tests/shared -q` | Confirmed by repository evidence |
| REQ-004 | The reference line renders the docstring (checked in Step 2) | `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | 4 | AC-2 | `tools/generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-005 | Required Changes; test passes and the path is read-only (checked in Step 2) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 2 | AC-4 | the named integrity test | Confirmed by repository evidence |
| REQ-005 | Required Changes; ADR-008 `## Known Deviations` (checked in Step 2) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-4 | `tools/check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; SHARED-002 cites line numbers (checked in Step 2) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 2 | AC-5 | `tools/check_docs_quality.py` | Confirmed by repository evidence |
| REQ-007 | Reason for Change; guide line 23 (checked in Step 2) | `docs/10_adr/adr_00_document-guide.md` | 3 | AC-3 | `tools/check_docs_quality.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes; prefix discovery ignores `UNK` and `NC` (checked in Step 2) | `tools/check_known_deviation_sync.py` | 5 | AC-1 | `tests/tools/test_check_known_deviation_sync.py` | Confirmed by repository evidence |
| REQ-008 | Acceptance Criteria; checker test | `tests/tools/test_check_known_deviation_sync.py` | 5 | AC-1 | the new fixtures | Explicit in issue |
| REQ-009 | Acceptance Criteria names `scripts/`; the Target Files do not (UNK-01) | `tools/check_known_deviation_sync.py` | 7 | AC-6 | `tests/tools/test_check_known_deviation_sync.py` | Needs confirmation |
| REQ-009 | Acceptance Criteria; checker test for `scripts/` | `tests/tools/test_check_known_deviation_sync.py` | 7 | AC-6 | the scripts fixture | Needs confirmation |
| REQ-010 | Documentation Impact; AGENTS.md Global Rule 9 | `tools/TOOL_DESCRIPTIONS.md` | 6 | AC-7 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-010 | GV-022 row describes the existing checks (checked in Step 2) | `docs/00_governance/governance_04_documentation-checks.md` | 6 | AC-7 | `tools/check_docs_consistency.py` | Derived from confirmed evidence |
