## Goal
- Correct `registry/component_mandatoriness.yaml`: state its derivation in one direction (the registry is the source; the `agent_08_04` table is generated from it), fix the factually wrong `rag_pipeline` `safety_role`, register the two untracked pending items (the never-performed ADR-004 mandatoriness assessment and the adrauth001 authority/placement note) as governance_03 ledger entries, and remove MDQ's duplicate auth posture check so every MCP server carries exactly one auth posture check (`common.auth_token`).

## Priority
Medium

## Scope
- **In-Scope**:
  - Registry header derivation fix and stale pending-note replacement (`REQ-001`).
  - `rag_pipeline` `safety_role` factual correction (`REQ-002`).
  - governance_03 Part 1 entries MCP-003 (missing ADR-004 assessment, incl. the `failure_category` re-evaluation proposal) and MCP-004 (registry authority/placement reconciliation) (`REQ-003`–`REQ-005`).
  - Removal of `server.auth_token_configured` from the MDQ posture contract and MDQ self-validation (`REQ-006`, `REQ-007`).
  - Regeneration of the generated artifacts and drift gates (`REQ-008`); test updates pinning the MDQ check set (`REQ-009`).
- **Out-of-Scope**:
  - Changing any `classification`, `rationale`, or `failure_category` value in the registry — `failure_category` re-evaluation is recorded as a proposal only (`REQ-005`); classification changes need an owner decision (issue Out of Scope).
  - Performing the ADR-004 Group 3 item 10 per-server assessment itself — this Plan only registers it as a tracked item.
  - The pending `mcp.component-mandatoriness` Resolution Matrix owner-list approval prepared by the completed adrchk010 Plan — that approval decision belongs to the owner, not this Plan.
  - The pre-existing bandit B105 finding at `scripts/shared/security/posture_contract.py:25` (see Risks) — unrelated to this change.
- **Dependencies**: Completion of the canonical-source registration of this registry (adrchk010, done; `config/documentation_canonical_sources.toml` lines 66–71 confirmed present 2026-11-19) — satisfied, so no ordering dependency remains for this Plan.
  - **Depends on**: N/A: none (the soft dependency on the canonical-registration work is already satisfied in current source; checked in Step 2)

## Background
- Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M08`). The issue's claims carry the `Documentation only` label; all four were re-verified against current source in Step 2 (see Problem).
- `ADR-004` Decision Group 3 item 13 (line 81) fixes the division: the approved classification is recorded in machine-readable form at `registry/component_mandatoriness.yaml`, and the `agent_08_04` table is generated from it. The registry header contradicts this. The registry is already registered as the canonical source for `mcp.component-mandatoriness` (`config/documentation_canonical_sources.toml` lines 66–71; the owner-list approval prepared by the completed adrchk010 Plan is still pending and is tracked by MCP-004).
- The MDQ duplicate check was introduced when the posture contract was created (completed Plan 20261015-112526): MDQ self-validation reported its own auth-token fact while the shared flow already reports `common.auth_token` for every server.

## Problem
All claims re-verified against current source (Step 2, 2026-11-20):
- Backwards derivation: `registry/component_mandatoriness.yaml` lines 3–4 say it is "Derived from the table in docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md", while `agent_08_04` line 57 (guard block) says the table is "Generated from `registry/component_mandatoriness.yaml`" and ADR-004 item 13 says the same. A maintainer editing the table sees the edit overwritten on the next regeneration.
- No assessment: all 10 registry entries (cicd, file_delete, file_read, file_write, git, github, mdq, rag_pipeline, shell, web_search) carry `rationale: Not assessed as satisfying Decision Group 3 item 10; status quo default` (lines 21, 33, 45, 57, 69, 81, 93, 105, 117, 129); `rg adrauth001 docs/00_governance` and `rg mandatoriness docs/00_governance/governance_03_issue-and-uncertainty-management.md` return nothing — the pending items are untracked.
- Wrong role/category facts: `rag_pipeline` `safety_role` reads "RAG document ingestion; fail-closed prevents index corruption on posture failure" (line 97), but the server's published tools are `rag_run_pipeline` (search pipeline), `rag_debug_pipeline`, `rag_list_documents`, `rag_delete_document` — no ingestion tool (`scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` TOOL_LIST). All 10 entries say `failure_category: safety-integrity`, while ADR-004 Group 2 item 7 (line 73) classes "unavailability of MCP server" as an availability failure.
- MDQ duplicate auth check: `REQUIRED_CHECK_IDS["mdq"]` (`scripts/shared/security/posture_contract.py` lines 99–107) contains `server.auth_token_configured` (line 101) in addition to `common.auth_token`; no other server has a server-scoped auth check (all 10 `REQUIRED_CHECK_IDS` entries inspected). `scripts/mcp_servers/mdq/mdq_security_validation.py` builds it (`_auth_token_check`, lines 117–131). The issue's "unknown" MDQ posture builder is `scripts/mcp_servers/mdq/mdq_security_validation.py` (`build_mdq_posture`, line 267+; called by `mdq_server.py` line 104).

## Reason for Change
- The registry contradicts ADR-004 item 13 and the generator about which artifact is the source, so the canonical-source contract is stated backwards in the very file the Canonical Source Registry names as authority.
- ADR-004 item 13 requires an *approved* classification, yet every rationale says Not assessed and nothing tracks that gap or the adrauth001 placement note.
- MDQ is the only server whose posture reports the same auth fact twice, once FAILED-class and once WARNING-class (`scripts/shared/security/startup_flow.py::check_auth_token_present` lines 132–144), so its posture can report two different verdicts for one fact.

## Implementation Intent
- Fix the registry header to state the single direction (registry is the source) and replace the stale pending note with pointers to new governance_03 ledger IDs.
- Register the assessment gap and the placement reconciliation as governance_03 Part 1 Known Issues (MCP-003, MCP-004); record the `failure_category` re-evaluation strictly as a proposal inside MCP-003.
- Correct `rag_pipeline` `safety_role` to match the published tool set, keeping `classification`, `failure_category`, and `rationale` byte-identical.
- Remove `server.auth_token_configured` from the MDQ contract and from MDQ self-validation; regenerate every generated artifact with `tools/generate_reference_table.py`; never hand-edit generated files.

## Requirements
- `REQ-001`: The registry header must state the derivation in one direction only — the registry is the machine-readable source (ADR-004 Group 3 item 13) from which the `agent_08_04` table is generated — with no "Derived from the table" sentence and no "pending adrauth001 (U-1)" note; it instead cites the governance_03 IDs registered by REQ-003/REQ-004.
- `REQ-002`: The `rag_pipeline` entry's `safety_role` must describe the server's actual published functions (retrieval pipeline execution/debug, document listing, document deletion) and must not claim document ingestion or index corruption; `classification`, `failure_category`, and `rationale` stay unchanged.
- `REQ-003`: governance_03 Part 1 gains entry `MCP-003` recording that the ADR-004 Group 3 item 10 assessment has never been performed: all 10 rationales are "Not assessed", no approval record exists, and `agent_08_04`'s note that no server is classified non-required restates the unassessed status quo. Type `design-gap`, Area MCP.
- `REQ-004`: governance_03 Part 1 gains entry `MCP-004` recording the registry authority/placement reconciliation the header note carried: the registry home is fixed by ADR-004 item 13 and its canonical registration, while the remaining open piece is the pending owner-list approval for the `mcp.component-mandatoriness` row (prepared by the completed adrchk010 Plan, its REQ-017/UNK-02).
- `REQ-005`: `MCP-003`'s Recommended Action records the `failure_category` re-evaluation as a proposal only: ADR-004 Group 2 item 7 classes MCP-server unavailability as an availability failure, so the uniform `safety-integrity` value across 10 entries awaits an owner classification decision. No `failure_category` value changes in this Plan.
- `REQ-006`: `REQUIRED_CHECK_IDS["mdq"]` must carry exactly one auth check — `common.auth_token` — like the other nine servers; `server.auth_token_configured` is removed from the contract.
- `REQ-007`: MDQ self-validation must no longer build or emit the auth-token check: `validate_mdq_security()` returns the 5 remaining checks in contract order, and no unused import, reason constant, or helper remains after the removal.
- `REQ-008`: Every generated artifact is regenerated from live sources via `tools/generate_reference_table.py` (never hand-edited): `registry/manifests/health_contracts.yaml` and `registry/manifests/component_mandatoriness.yaml`; all `--check` drift gates pass.
- `REQ-009`: Tests pinning the MDQ 6-check set are updated to the 5-check contract, and the parametrized posture-contract mirror matches the new `REQUIRED_CHECK_IDS`.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed
2026-11-20: `check_workitem_structure.py` and `audit_plan_target_paths.py` clean; every
row `Verified` against current source — see `rules/workflow-lifecycle.md`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | governance ledger entries | add Part 1 entries MCP-003 and MCP-004 (17 fields each) tracking the assessment gap, the `failure_category` proposal, and the placement reconciliation | REQ-003, REQ-004, REQ-005; AC-03, AC-04 | Part 1 active MCP group is only MCP-001 (line 94) and MCP-002 (line 114) (checked in Step 2); `rg adrauth001 docs/00_governance` empty | `tools/check_needs_confirmation_inventory.py`; docs checkers per `routing.md` | Verified |
| registry/component_mandatoriness.yaml | registry edit | header single-direction derivation; `rag_pipeline` `safety_role` correction; ledger-ID citation | REQ-001, REQ-002; AC-01, AC-02 | header lines 3–7 contradict ADR-004 line 81 and agent_08_04 line 57 (checked in Step 2); line 97 claims ingestion/index corruption vs `rag_pipeline_tools.py` TOOL_LIST lines 11–104 (4 tools, no ingestion) | `tests/tools/test_check_component_mandatoriness.py`; `tools/check_component_mandatoriness.py` | Verified |
| registry/manifests/component_mandatoriness.yaml | regenerate | manifest mirrors `safety_role`; must be regenerated after the registry edit | REQ-008; AC-07 | generator copies `safety_role`/`failure_category` (`tools/generate_reference_table.py` lines 955–956) (checked in Step 2); manifest already mirrors the entry `safety_role` values (lines 12–121) | `tools/generate_reference_table.py --check`; `tests/tools/test_generate_reference_table.py` | Verified |
| scripts/shared/security/posture_contract.py | code fix | remove `"server.auth_token_configured"` from `REQUIRED_CHECK_IDS["mdq"]` | REQ-006; AC-05 | lines 99–107 contain the only server-scoped auth check among all 10 servers (checked in Step 2) | `tests/shared/test_security_posture_contract.py` | Verified |
| scripts/mcp_servers/mdq/mdq_security_validation.py | code fix | delete `_auth_token_check()` and its call in `validate_mdq_security()`; drop imports that become unused | REQ-007; AC-06 | `_auth_token_check` lines 117–131; call at line 108 (checked in Step 2) | `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Verified |
| registry/manifests/health_contracts.yaml | regenerate | mdq check list must lose `server.auth_token_configured` after regeneration | REQ-008; AC-07 | entry lines 60–70 carry `server.auth_token_configured` at line 66 (checked in Step 2); generator source mapping `tools/generate_reference_table.py` line 498 | `tools/generate_reference_table.py --check`; `tests/tools/test_generate_reference_table.py` | Verified |
| tests/mcp_servers/mdq/test_mdq_security_validation.py | test update | `MDQ_CHECK_IDS` and the auth-check verdict tests must express the 5-check contract | REQ-009; AC-06, AC-08 | `MDQ_CHECK_IDS` includes `server.auth_token_configured` (lines 47–48); auth verdict tests at lines 173–186 (checked in Step 2) | this file | Verified |
| tests/shared/test_security_posture_contract.py | test update | `SERVER_CHECK_IDS` mirror must drop the mdq auth id | REQ-009; AC-05, AC-08 | mirror dict starts line 33 and carries `server.auth_token_configured` at line 90 (checked in Step 2) | this file | Verified |

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
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | The issue lists it as "(regenerated)"; its guard-block table (lines 56–71) renders only Server/Classification/Rationale, none of which this Plan changes, so regeneration must leave the file byte-identical and `generate_reference_table.py --check` must stay green | REQ-001, REQ-008; scope note in Design decision 4 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Group 3 items 10/12/13 (lines 78–81) and Group 2 item 7 (line 73) are the normative basis for the header fix and the `failure_category` proposal; AAL-019 (line 350 / ledger) already tracks the pending RAG availability approval and must be cited as Related | REQ-001, REQ-003, REQ-005 |
| scripts/shared/security/startup_flow.py | `check_auth_token_present` (lines 132–144) is the single surviving auth check with WARNING semantics (verified in Step 2); it must not change | REQ-006 |
| scripts/mcp_servers/mdq/mdq_server.py | Posture build entry (`build_mdq_posture` call, line 104) and the startup-time token rejection that `_auth_token_check`'s docstring references (line 118) | REQ-007 |
| tools/check_component_mandatoriness.py | Three-way registry/table/config consistency checker that must stay exit-0 after the registry edit | REQ-001, REQ-008 |
| config/documentation_canonical_sources.toml | Lines 66–71 show the registry is already the canonical source; MCP-004 text must state the placement state accurately against this row | REQ-004 |
| docs/00_governance/governance_01_documentation-policy.md | Resolution Matrix line 134 (security-policy owners) is the open piece MCP-004 records; the Matrix itself must not be edited by this Plan | REQ-004 |
| tests/mcp_servers/mdq/test_mdq_health_posture.py | Iterates `posture.checks` generically (line 47) with no auth-id literal; confirm it needs no change when the phase-3 suite runs | REQ-009 |

## Acceptance Criteria
- `AC-01` (REQ-001): `rg "Derived from" registry/component_mandatoriness.yaml` returns nothing; the header states the registry as the source cited to ADR-004 Group 3 item 13 and cites MCP-003/MCP-004; `uv run python tools/check_component_mandatoriness.py` exits 0.
- `AC-02` (REQ-002): the `rag_pipeline` `safety_role` names retrieval/list/delete functions and contains neither "ingestion" nor "index corruption"; `classification`, `failure_category`, and `rationale` for all 10 entries are unchanged (diff shows no change on those fields).
- `AC-03` (REQ-003, REQ-004): governance_03 Part 1 contains MCP-003 and MCP-004 with all 17 Part 1 fields; docs checkers listed in `routing.md` Tools pass.
- `AC-04` (REQ-005): MCP-003 Recommended Action states the `failure_category` re-evaluation proposal citing ADR-004 Group 2 item 7, and no `failure_category` value changed in the registry.
- `AC-05` (REQ-006): `rg "server.auth_token_configured" scripts/ registry/ tests/` returns nothing after regeneration and test updates; every entry of `REQUIRED_CHECK_IDS` contains `common.auth_token` exactly once and no server-scoped auth id.
- `AC-06` (REQ-007): `validate_mdq_security()` returns 5 checks in contract order; `uv run ruff check` and `uv run vulture --min-confidence 80` report nothing new on the changed scripts files.
- `AC-07` (REQ-008): `uv run python tools/generate_reference_table.py --check` exits 0; the regenerated `health_contracts.yaml` mdq entry has 8 checks (3 common + 5 server) and `component_mandatoriness.yaml` mirrors the corrected `safety_role`.
- `AC-08` (REQ-009): the full suite passes with no new failures against the recorded baseline (13089 passed, 5 skipped, 2026-11-20) and diff-cover ≥ 90 %.

## Tests
- `T01` (REQ-006): parametrized posture-contract test — `REQUIRED_CHECK_IDS["mdq"] == COMMON_CHECK_IDS + 5 server ids`, and no server key contains a `server.*auth*` id (`tests/shared/test_security_posture_contract.py`).
- `T02` (REQ-007, REQ-009): MDQ self-validation returns exactly the 5 remaining check ids in contract order; the removed-auth verdicts are gone; the token-missing fact remains reported by `common.auth_token` (WARNING) via the shared flow (`tests/mcp_servers/mdq/test_mdq_security_validation.py`).
- `T03` (REQ-008): `tools/generate_reference_table.py --check` and `tools/check_component_mandatoriness.py` exit 0 after regeneration.
- `T04` (REQ-003, REQ-004): governance_03 entries pass `tools/check_needs_confirmation_inventory.py` and the docs checkers from `routing.md` Tools.
- `T05` (REQ-009): full-suite run per `rules/toolchain.md` with diff-cover ≥ 90 %.

## Documentation Impact
Yes. `docs/00_governance/governance_03_issue-and-uncertainty-management.md` gains two Part 1 entries (`REQ-003`–`REQ-005`), and `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`'s guard block is revalidated by regeneration (`REQ-008`; content unchanged, see Design decision 4). Both are rows of the frozen Implementation Target Files / Reference Files tables; after the `docs/` edit, run the checkers listed in `routing.md` Tools → "When to run which tool".

## Assumptions
- `A-1`: Removing the MDQ server-scoped auth check is safe because `mdq_server.py` refuses to start without a token and `check_auth_token_present` (WARNING semantics, verified in Step 2) remains the single auth posture fact (verified in Step 2).
- `A-2`: Rewriting `rag_pipeline`'s `safety_role` to match the published tool set is a factual correction, not a classification decision; the issue's "do not invent rationales" constraint is honored by leaving `rationale` and `classification` untouched and deriving the role text only from `TOOL_LIST` descriptions.
- `A-3`: The header note "Authority/placement reconciliation pending adrauth001 (U-1)" is stale wording: both adrauth001 Plans are done (`plans/done/20261029-214650_...`, `plans/done/20261108-092627_...`) and ADR-004 item 13 already fixes the registry path; what remains open is the owner-list approval prepared by adrchk010 (its REQ-017/UNK-02), which MCP-004 records.
- `A-4`: Ledger IDs `MCP-003`/`MCP-004` are free: the MCP group currently ends at MCP-002 (checked in Step 2); implementation re-checks before writing.
- `A-5`: Removing `server.auth_token_configured` changes no ADR decision, invariant, Blocking value, or authority edge (no ADR or governance doc names the check id — `rg auth_token_configured docs/` is empty), so no approval record is required for it per the issue's Constraints; the change is verified by the contract tests alone.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner preference on the outcome of the `failure_category` re-evaluation (per-server safety-integrity vs availability values) | No maintainer decision exists; the issue forbids changing values without approval | Recorded as the MCP-003 proposal; owner decision lands as an approval record (governance_01/governance_05) in a later change, outside this Plan | False |
| UNK-02 | Whether MCP-003's proposal should additionally open an ADR Approval Ledger (AAL) entry now | AAL entries record approvals; no approval exists yet to record | This Plan registers Part 1 Known Issues only; an AAL entry is created only when the owner decides, per `governance_03` Part 5 semantics | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | Modify | Medium (startup validation reads it via `shared/component_mandatoriness.py`) | 1 | not measured (single-repo owner convention) | rsynced config; restart required for a running agent |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Low | 16 (highest in this Plan — coordinate with concurrent governance work) | not measured | rsynced docs only |
| scripts/shared/security/posture_contract.py | Modify | Medium (agent-side `posture_validator.py` and every server posture consumes the contract) | 0 | not measured | rsynced code; service restart required |
| scripts/mcp_servers/mdq/mdq_security_validation.py | Modify | Low (MDQ only) | 0 | not measured | rsynced code; MDQ restart required |
| registry/manifests/health_contracts.yaml | Regenerate | Low | 0 | not measured | rsynced manifest |
| registry/manifests/component_mandatoriness.yaml | Regenerate | Low | 0 | not measured | rsynced manifest |
| tests/mcp_servers/mdq/test_mdq_security_validation.py | Modify | Low | — | — | not deployed |
| tests/shared/test_security_posture_contract.py | Modify | Low | — | — | not deployed |

## Design
Classification: Path B (8 target files across registry, governance docs, two scripts,
two test files, two generated manifests; contract change with test coupling).

Step 5 analyses (Path B):
- Architecture: `posture_contract.py` imports only `shared.security.result_dto`; `mdq_security_validation.py` imports `mcp_servers.mdq.mdq_tools`, `shared.security.*` — both respect the `.importlinter` hierarchy (shared is a leaf; mcp_servers → shared only). Consumers of `REQUIRED_CHECK_IDS` in `scripts/`: `scripts/agent/services/posture_validator.py` only (generic, no mdq literal). Consumers of `validate_mdq_security`/`build_mdq_posture`: `mdq_server.py`, `health_check.py`, and the two MDQ test files. `lint-imports` must stay green after the edit (checked in Step 5).
- Dependency graph: files requiring changes = the 8 frozen-table rows. `server.auth_token_configured` appears only in `posture_contract.py:101`, `mdq_security_validation.py:121/127`, `registry/manifests/health_contracts.yaml:66`, `tests/shared/test_security_posture_contract.py:90`, `tests/mcp_servers/mdq/test_mdq_security_validation.py:48/173/181/186` — no docs or config reference it (`rg auth_token_configured docs/` empty; `config/` none).
- Historical: 30-day churn — governance_03 16 commits (coordinate edits; re-read before editing), registry yaml 1, both scripts 0. The duplicate check originates from the posture-contract creation Plan (20261015-112526), which intentionally added MDQ self-validation; the removal is a deliberate contract change, not a regression revert.
- Operational: no process holds the repository MDQ db (no listener found on the MCP server ports checked with `ss -ltnp`; `fuser` not installed on this dev host — the file-lock check is recorded as not run). `pip-audit` N/A: no dependency change planned. Persisted-schema check N/A: no DDL or schema version touched; `mdq.sqlite` is not modified.
- Validation quality baseline (Step 5, run on the Python targets): radon — highest complexity `posture_contract.py SecurityPosture.__post_init__ C (12)`, `mdq_security_validation.py _allowed_dirs_exist_check B (6)`; neither is touched by this Plan (edits are data-literal removals and one function deletion). vulture (--min-confidence 80) on both files: 0 items. bandit: 1 pre-existing finding, Low severity/Medium confidence B105 at `posture_contract.py:25` (`CHECK_ID_AUTH_TOKEN = "common.auth_token"` literal) — unrelated to this change and left untouched. diff-cover baseline: clean tree vs master, no diff lines; suite baseline 13089 passed, 5 skipped (2026-11-20, filtered run per `rules/toolchain.md` section 7). The Plan's Completion gate requires diff-cover ≥ 90 % on its own diff.

Design decisions:
1. Ledger placement: the two pending items become governance_03 Part 1 Known Issues (IDs MCP-003, MCP-004), not AAL entries, because AAL records approvals and no approval exists yet (UNK-02). The registry header then cites these IDs instead of carrying an untracked "pending" note.
2. `failure_category` is proposal-only: values are classification decisions needing approval (issue Constraints; ADR-004 Group 3 item 13 "Approved classification"); the plan records the criterion tension (Group 2 item 7 availability vs uniform safety-integrity) in MCP-003 without touching any value.
3. MDQ duplicate removal keeps one auth fact per server: `common.auth_token` (shared flow, WARNING) survives; the FAILED-class `_auth_token_check` is deleted. Startup-time enforcement stays in `mdq_server.py` (fail-fast without a token).
4. `agent_08_04` stays a Reference File, not a target row: its guard-block table renders only Server/Classification/Rationale (verified against `tools/generate_reference_table.py` mandatoriness renderer), all unchanged by this Plan, so the frozen table requires no edit to it; the issue's "(regenerated)" expectation is satisfied by the drift check (`--check` green). If a future rationale change makes the table content differ, regeneration — not hand-editing — applies.
5. Current-Specification-Only: the header rewrite states the current contract only; no "formerly derived from" history wording, no migration notes. `REASON_AUTH_TOKEN_MISSING` stays in use by `startup_flow.py` and is not removed from the shared module; only imports unused in `mdq_security_validation.py` after the deletion are dropped.

## Implementation steps
1. **Phase 1: Governance ledger entries**
   - [ ] Add MCP-003 (assessment gap + failure_category proposal) and MCP-004 (authority/placement reconciliation) to `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 with all 17 fields, `Related` citing AAL-019 and the canonical-source row (REQ-003, REQ-004, REQ-005)
2. **Phase 2: Registry correction and generated-artifact refresh**
   - [ ] Rewrite the header of `registry/component_mandatoriness.yaml` (single-direction derivation, cite MCP-003/MCP-004) and correct the `rag_pipeline` `safety_role`, leaving all other fields byte-identical (REQ-001, REQ-002)
   - [ ] Regenerate `registry/manifests/component_mandatoriness.yaml` and revalidate the `agent_08_04` guard block with `tools/generate_reference_table.py`; run `tools/check_component_mandatoriness.py` (REQ-008)
   - **Unit**: mandatoriness-registry-refresh | **Phases**: 2 | **Reason**: the registry edit changes values mirrored into the generated manifest and table; the drift gate fails until the regeneration lands in the same commit.
3. **Phase 3: MDQ auth-check removal**
   - [ ] Remove `server.auth_token_configured` from `REQUIRED_CHECK_IDS["mdq"]` in `scripts/shared/security/posture_contract.py` (REQ-006)
   - [ ] Delete `_auth_token_check()` and its call in `scripts/mcp_servers/mdq/mdq_security_validation.py`; drop imports that become unused (REQ-007)
   - [ ] Update `tests/mcp_servers/mdq/test_mdq_security_validation.py` (`MDQ_CHECK_IDS`, auth verdict tests) and `tests/shared/test_security_posture_contract.py` (`SERVER_CHECK_IDS` mirror) to the 5-check contract (REQ-009)
   - [ ] Regenerate `registry/manifests/health_contracts.yaml` via `tools/generate_reference_table.py` (REQ-008)
   - **Unit**: mdq-auth-check-removal | **Phases**: 3 | **Reason**: removing the id from the contract breaks the pinned tests and the generated manifest until all four edits land in the same commit; the intermediate state cannot pass gates.
4. **Phase 4: Full validation and deployment sync**
   - [ ] Run the `rules/toolchain.md` sequence: ruff, import-linter, targeted tests (`tests/mcp_servers/mdq/`, `tests/shared/test_security_posture_contract.py`, `tests/tools/test_check_component_mandatoriness.py`, `tests/tools/test_generate_reference_table.py`), full suite + diff-cover ≥ 90 %, `tools/generate_reference_table.py --check`, `tools/check_component_mandatoriness.py`, `tools/check_needs_confirmation_inventory.py` and the `routing.md` docs checkers (REQ-008, REQ-009)
   - [ ] Deployment check: confirm `deploy.sh` rsync coverage for `registry/`, `scripts/shared/security/`, `scripts/mcp_servers/mdq/`, and the two docs files; note that a live agent restart is required for the changed posture contract to take effect (no live service is restarted by this Plan unless requested)

### Release units
**Unit**: mandatoriness-registry-refresh | **Phases**: 2 | **Reason**: registry edit and its manifest regeneration cannot pass the drift gate separately.
**Unit**: mdq-auth-check-removal | **Phases**: 3 | **Reason**: contract edit, MDQ validation edit, manifest regeneration, and test updates cannot pass the suite separately.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| registry/component_mandatoriness.yaml | Consistency integration | `uv run python tools/check_component_mandatoriness.py` | exit 0; three-way agreement unchanged |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Docs gate | `uv run python tools/check_needs_confirmation_inventory.py`; `routing.md` docs checkers | exit 0; entries well-formed |
| scripts/shared/security/posture_contract.py | Unit | `uv run pytest tests/shared/test_security_posture_contract.py` | 5-check mdq contract passes |
| scripts/mcp_servers/mdq/mdq_security_validation.py | Unit | `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py` | 5 checks, contract order, no auth id |
| registry/manifests/health_contracts.yaml / component_mandatoriness.yaml | Drift gate | `uv run python tools/generate_reference_table.py --check` | exit 0 after regeneration |
| whole change | Suite + coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | no new failures vs baseline 13089 passed / 5 skipped; diff-cover ≥ 90 % |

## Risks
- **Risk**: governance_03 is the highest-churn file here (16 commits/30d); concurrent governance work could collide with the MCP-003/MCP-004 IDs or edit Part 1 concurrently → **Mitigation**: re-read Part 1 and re-scan for `MCP-003`/`MCP-004` immediately before editing (Assumption A-4); abort and report on ID collision rather than renumbering silently.
- **Risk**: the posture-contract change is consumed by every server posture path (agent-side `posture_validator.py`) and a live MDQ server in production would cache the old posture until restart → **Mitigation**: phase 3 lands as one unit; Phase 4 records the restart requirement explicitly; no live service is restarted without an explicit request.
- **Risk**: the pre-existing bandit B105 (Low/Medium confidence) at `posture_contract.py:25` stays after this change and could be mistaken for a regression → **Mitigation**: recorded as a baseline finding in Design; out of scope.
- **Risk**: MCP-004 text could misstate the placement state if the pending adrchk010 owner-list approval is confused with the already-fixed registry home → **Mitigation**: cite the canonical-source row and the adrchk010 REQ-017/UNK-02 status verbatim from `config/documentation_canonical_sources.toml` lines 66–71 and the adrchk010 plan record.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: governance_03 entries MCP-003/MCP-004 (REQ-003–REQ-005) | Completed | 2026-11-20 | 20261120-072325 |  |
| 2 | Phase 2: registry header + rag_pipeline safety_role edit, regenerate manifests (Unit: mandatoriness-registry-refresh) | Completed | 2026-11-20 | 20261120-072325 |  |
| 3 | Phase 3: MDQ auth-check removal, tests, regenerate health_contracts (Unit: mdq-auth-check-removal) | Completed | 2026-11-20 | 20261120-072325 |  |
| 4 | Phase 4: full validation sequence and deployment sync check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261120-043919_01 | 1 | Procedure | Pending | Repository owner | — |
| 20261120-043919_02 | 2 | Procedure | Pending | Repository owner | — |
| 20261120-043919_03 | 2 | Procedure | Pending | Repository owner | — |
| 20261120-043919_04 | 3 | Procedure | Pending | Repository owner | — |
| 20261120-043919_05 | 3 | Procedure | Pending | Repository owner | — |
| 20261120-043919_06 | 3 | Procedure | Pending | Repository owner | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-001311
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `registry/component_mandatoriness.yaml`; `registry/manifests/component_mandatoriness.yaml`; `scripts/shared/security/posture_contract.py`; `scripts/mcp_servers/mdq/mdq_security_validation.py`; `registry/manifests/health_contracts.yaml`; `tests/mcp_servers/mdq/test_mdq_security_validation.py`; `tests/shared/test_security_posture_contract.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change bullet 1; ADR-004 line 81 | registry/component_mandatoriness.yaml | Phase 2 | AC-01 | T03 | Confirmed by repository evidence |
| REQ-002 | Problem bullet 3; `rag_pipeline_tools.py` TOOL_LIST | registry/component_mandatoriness.yaml | Phase 2 | AC-02 | T03 | Confirmed by repository evidence |
| REQ-003 | Problem bullet 2 (Not assessed rationales; governance_03 search empty) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 1 | AC-03 | T04 | Confirmed by repository evidence |
| REQ-004 | Problem bullet 2; registry header line 6; adrchk010 plan REQ-017/UNK-02 record | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 1 | AC-03 | T04 | Confirmed by repository evidence |
| REQ-005 | Problem bullet 3; ADR-004 line 73 | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 1 | AC-04 | T04 | Confirmed by repository evidence |
| REQ-006 | Reason for Change bullet 3; `posture_contract.py` lines 99–107 | scripts/shared/security/posture_contract.py | Phase 3 | AC-05 | T01 | Confirmed by repository evidence |
| REQ-007 | Unresolved Questions resolved: builder is `mdq_security_validation.py` lines 108, 117–131 | scripts/mcp_servers/mdq/mdq_security_validation.py | Phase 3 | AC-06 | T02 | Confirmed by repository evidence |
| REQ-008 | Constraints bullet 6 (regenerate, never hand-edit) | registry/manifests/health_contracts.yaml | Phase 3 | AC-07 | T03 | Derived from confirmed evidence |
| REQ-008 | Constraints bullet 6 | registry/manifests/component_mandatoriness.yaml | Phase 2 | AC-07 | T03 | Derived from confirmed evidence |
| REQ-009 | Testing Expectations (`rg auth_token_configured tests` hits) | tests/mcp_servers/mdq/test_mdq_security_validation.py | Phase 3 | AC-08 | T02, T05 | Confirmed by repository evidence |
| REQ-009 | Testing Expectations | tests/shared/test_security_posture_contract.py | Phase 3 | AC-08 | T01, T05 | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-043919 -->