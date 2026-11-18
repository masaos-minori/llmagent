# Plan: Unify the MCP authentication contract across ADR-002, ADR-007, ADR-013, and ADR-017

## Goal
- Make ADR-017 the only document that defines MCP token supply, validation, and failure; fix the verified wording defects in ADR-007, ADR-013, and ADR-017; and prepare the ADR-002 INV-04 amendment as a pending-amendment proposal that awaits the maintainer's approval without ever writing approval text.

## Priority
High

## Scope
- **In-Scope**:
  - Fix the INV reference in the ADR-017 Negative Consequences section (`INV-03` -> `INV-02`).
  - Reduce ADR-007 Decision item 10 and its Implementation References token wording to a reference to ADR-017; remove the stale `secret files` mention; add the disabled-server exclusion to the ADR-007 Fail-Fast token wording.
  - Describe the ADR-013 token storage as a `${ENV:...}` reference resolved at load time, pointing at ADR-017 for the MCP token convention.
  - Prepare the ADR-002 INV-04 amendment in the pending-amendment form (bullet under `### Approval Record` citing a new `AAL-030` ledger entry), proposal only.
  - Scope amendment (reported, per the Issue's "Change only the Target Files" constraint): `docs/00_governance/governance_03_issue-and-uncertainty-management.md` must gain the `AAL-030` ledger entry because `tools/check_adr_structure.py` rejects a pending bullet that cites a ledger entry that does not exist (governance_01 ADR Pending Amendment Form). This deviation requires user acknowledgement before Phase 2 runs.
- **Out-of-Scope**:
  - Changing `scripts/agent/startup_validation.py` or any token-loading code (Issue Out of Scope).
  - Hot-reload behavior of the config (tracked by the hot-reload validation issue).
  - Writing, paraphrasing, or simulating any maintainer approval statement, Approver, or Date.
  - Editing ADR front matter `related` lists or `config/adr_authority.toml` (no authority edge changes: verified that `mcp.authentication` already has ADR-017 as its sole primary ADR).
- **Dependencies**: the adrchk011 (ADR Approval Governance) plan registers the pending-amendment form and ledger this Plan uses; that plan's Execution Status still has Step 5 (`Validation and hand-off`) Pending, but the forms and the enforcing checker are already applied in the governance documents and verified this cycle, so this Plan does not wait for it (judgement recorded as UNK-02).
  - No `Depends on` bullet: the adrchk011 plan's remaining step is not a prerequisite this Plan must wait for (verified against the governance documents this cycle).

## Background
Filed from the consolidated ADR review task list (`ADRCHK2-H01` package). ADR-002, ADR-007, ADR-013, and ADR-017 describe MCP token handling differently. ADR-017 was created as the deferred record of ADR-007 Decision 9 (`ADR-007 → ADR-017`, intentional pair) and already carries the implemented rules. This Plan makes the other ADRs point at it instead of restating the rule.

## Problem
ADR-002 INV-04 ("The Agent can start without being given MCP-specific Secrets") contradicts ADR-017 INV-01 and ADR-007 Decision item 9: `scripts/agent/startup_validation.py` records a fatal `mcp_auth` finding for every enabled server with an empty `auth_token`. The supply mechanism is described three ways: ADR-007 Implementation References say "environment variables or secret files" (line 356) but no secret-file loading path exists in `scripts/`; ADR-013 says the token is "stored as a plain string in config"; ADR-017 describes the `${ENV:MCP_<SERVER_KEY>_AUTH_TOKEN}` resolution that the code actually implements. ADR-017's Negative Consequences cites `INV-03` where the `require_auth_token()` rule is `INV-02`. ADR-007's Fail-Fast wording omits the disabled-server exclusion that ADR-017 and the code apply.

## Reason for Change
A reviewer who applies ADR-002 could approve removing the startup check; readers who rely on ADR-007 or ADR-013 may provision secrets in a way the code does not read, so startup fails in production. The mis-citation and the missing exclusion misdirect any change that touches token handling.

## Implementation Intent
Body-text-only edits in the four ADR documents. ADR-017 stays the sole normative definition (matching its existing authority entry `mcp.authentication`). Every other ADR keeps its own subject-specific text but replaces restated MCP token rules with references to ADR-017. The INV-04 contradiction is a decision change: it is written only in the governance pending-amendment form (proposal bullet + ledger entry with `Not recorded` Approver/Date), never as an approved text change.

## Requirements
- `REQ-001`: Confirm the token-loading claim and record the evidence: `config/agent.toml` and every `config/<key>_mcp_server.toml` carry `auth_token = "${ENV:MCP_<KEY>_AUTH_TOKEN}"` (resolved by `scripts/shared/config_utils.py`); `scripts/mcp_servers/server.py` `require_auth_token()` enforces the non-empty token at server startup; no secret-file loading path exists anywhere in `scripts/` (`rg -ri "secret file|read_secret" scripts/` — no matches). Resolved this cycle from `Needs confirmation`.
- `REQ-002`: Fix the ADR-017 Negative Consequences citation: the `require_auth_token()` bypass bullet MUST cite `INV-02`, not `INV-03`.
- `REQ-003`: Reduce ADR-007 Decision item 10 and the Implementation References token bullet to a reference to ADR-017; remove the `secret files` phrase; state the Fail-Fast token condition with the enabled-server scope and the disabled-server exclusion.
- `REQ-004`: Describe the ADR-013 token storage as a `${ENV:...}` reference resolved at load time (verified behavior in `scripts/eventbus/config.py`) and point at ADR-017 for the MCP token convention.
- `REQ-005`: Prepare the ADR-002 INV-04 amendment as a proposal in the pending-amendment form: one bullet under `### Approval Record` stating the changed text and citing `AAL-030`, plus the `AAL-030` entry in the ADR approval ledger with `Approver: Not recorded` and `Date: Not recorded`. The INV-04 line, ADR Status (`Accepted`), and Blocking values stay unchanged until the maintainer's approval is recorded. The Plan adds no ADR front matter `related` entry and no authority edge (see Risks).
- `REQ-006`: Validation: `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py`, and the `routing.md` docs checkers pass after the edits. No authority edge or front matter change is made: verified that ADR-002's only authority edges are `ADR-002 → ADR-001` and `ADR-002 → ADR-004` (`config/adr_authority.toml` lines 136-146) and that the file cites no invariant IDs (`rg "INV-03" config/adr_authority.toml` — no matches; checked in Step 5).

## Implementation Target Files
**Freeze status**: Frozen (issue-to-plan Step 8 Implementation Target Files Validation
passed 20261118-210631: every row `Verified`, `tools/audit_plan_target_paths.py` 0 findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Add the pending-amendment bullet under `### Approval Record` citing `AAL-030`; update the INV-04 Verification-table row and Open-Items checkboxes only when an approval is recorded (not this cycle) | REQ-005; AC-001, AC-005 | INV-04 text at line 182; its Verification row "Not verified (no automated test exists)" at line 233; Open Items at lines 339-340; Approval Record section exists (checked in Step 2) | None (docs-only row; contradicting behavior is covered by `tests/agent/test_startup.py::test_mcp_auth_fatal_when_any_server_missing_token`) | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Reduce item 10 and the Implementation References token bullet to a reference to ADR-017; remove "or secret files"; add the enabled-scope / disabled-exclusion wording to the Fail-Fast token condition | REQ-003; AC-003 | Item 10 at line 78 restates token supply; Fail-Fast bullet "empty authentication token (Agent startup validation)" omits the disabled-server exclusion; Implementation References line 356 says "environment variables or secret files"; `rg -ri "secret file\|read_secret" scripts/` found no secret-file path (checked in Step 2) | `tests/mcp_servers/test_require_auth_token.py::TestRequireAuthToken::test_empty_token_raises` (cited by ADR-017 Verification; unchanged) | Verified |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Modify | Fix the Negative Consequences bullet to cite `INV-02` | REQ-002; AC-002 | Bullet "a new server that bypasses it violates INV-03"; `INV-02` is the `require_auth_token()` routing rule and `INV-03` is the middleware 401 rule (checked in Step 2) | `tests/mcp_servers/test_require_auth_token.py::test_every_server_routes_through_shared_enforcement_point` (cited by ADR-017 Verification; unchanged) | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Reword the token-storage Assumption as a `${ENV:...}` reference resolved at load time and reference ADR-017 for the MCP token convention | REQ-004; AC-004 | Assumption at line 62 "stored as a plain string in config (following the existing `auth_token = \"${ENV:...}\"` convention...)"; `scripts/eventbus/config.py` lines 260 and 317 resolve `${ENV:VAR_NAME}` references before validating token values (checked in Step 2) | `tests/eventbus/test_eventbus_auth.py` (cited by the ADR-013 matrix row; unchanged) | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Add the `AAL-030` ledger entry (ADR-002, INV-04 amendment, Approver/Date `Not recorded`) required by the pending-amendment form (scope amendment, see Scope) | REQ-005; AC-005 | Part 5 rules: every cited ID must have an entry; entries run AAL-001..AAL-029, so the next ID is `AAL-030` (checked in Step 2) | `tools/check_adr_structure.py` enforces the citation (checked in Step 2) | Verified |

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
| `scripts/agent/startup_validation.py` | Lines 152-161: fatal `mcp_auth` finding for each enabled server without a token; disabled servers exempt | REQ-001; `docs/10_adr/adr_02_01_002_platform-config-isolation.md` |
| `scripts/shared/config_utils.py` | Lines 19-43: `${ENV:VAR_NAME}` reference resolution (the only loading mechanism) | REQ-001; REQ-003 |
| `scripts/mcp_servers/server.py` | Line 226: `require_auth_token()` shared enforcement point that ADR-017 INV-02 names | REQ-001; REQ-002 |
| `scripts/eventbus/config.py` | Lines 260 and 317: EventBus resolves `${ENV:VAR_NAME}` token references before validation | REQ-004; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` |
| `config/agent.toml` | Agent-side `auth_token = "${ENV:MCP_<KEY>_AUTH_TOKEN}"` entries for all ten servers | REQ-001 |
| `config/mdq_mcp_server.toml` | Representative server-side config carrying the same `${ENV:MCP_MDQ_AUTH_TOKEN}` reference (grep evidence covers every `*_mcp_server.toml`) | REQ-001 |
| `tests/agent/test_startup_validation.py` | `TestMcpAuthDisabledServers` names the enabled-fatal and disabled-exempt behavior the wording must match | REQ-001; REQ-003 |
| `tests/mcp_servers/test_require_auth_token.py` | Tests cited by the ADR-017 Verification section; they must keep existing after the citation fix | REQ-002 |
| `docs/10_adr/adr_01_index.md` | Verified this cycle: the Invariant Matrix has no ADR-002 INV-04 row and no ADR-017 row, so the Issue's "update the Index matrix row" instruction has no row to update; the generated blocks stay untouched because no authority edge changes | REQ-005; REQ-006 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Pending Amendment Form (lines 298-313): exact form the bullet must take | REQ-005; `docs/10_adr/adr_02_01_002_platform-config-isolation.md` |
| `config/adr_authority.toml` | Confirms `mcp.authentication` primary is ADR-017 with no supplemental, and the ADR-002→ADR-017 `INV-03` edge (line 203) is already correct; no edit | REQ-006 |

## Acceptance Criteria
- `AC-001` (REQ-001, REQ-005): No ADR ends the cycle claiming the Agent starts without an MCP token while another requires one — with the explicit caveat that the INV-04 line itself stays unchanged until the maintainer records approval; the cycle deliverable is the proposal bullet plus ledger entry. Full closure of this criterion belongs to the approval-recording change.
- `AC-002` (REQ-002): the ADR-017 Negative Consequences bypass bullet cites `INV-02` and no remaining ADR-017 text mis-cites a token rule.
- `AC-003` (REQ-003): `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` contains no mention of secret files, its item 10 and Implementation References reference ADR-017, and its Fail-Fast token condition names the enabled-server scope and disabled-server exclusion.
- `AC-004` (REQ-004): `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` describes token storage as a `${ENV:...}` reference resolved at load time.
- `AC-005` (REQ-005): the pending bullet and `AAL-030` exist, `AAL-030` shows `Approver: Not recorded` / `Date: Not recorded`, and the Plan, ADR text, and ledger contain no approval statement, reviewer name, or approval date.
- `AC-006` (REQ-006): `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, and the `routing.md` docs checkers (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`) exit 0.

## Tests
- Documentation-only. No pytest target. Validation items per Requirement: `tools/check_adr_structure.py` (REQ-005 pending bullet/ledger citation rule), `tools/check_adr_reference.py` (front matter/model cross-check stays clean because no front matter changes; REQ-002, REQ-006), `tools/check_adr_authority.py` (no authority edge change; REQ-006), `tools/check_adr_invariant_matrix.py` (cited tests still exist; REQ-006), docs checkers per `routing.md` (all REQ rows).
- Validation quality baseline: `N/A: no Python target` (no `scripts/` or `tools/` row in Implementation Target Files).

## Documentation Impact
Yes. The Plan's own Implementation Target Files are the documentation updates (ADR and governance documents named in the frozen table). The MCP-domain docs cross-checked by `tools/check_docs_consistency.py --domain mcp` must remain claim-consistent; no additional Reference doc edit is planned.

## Assumptions
- The Issue's Target list includes `docs/10_adr/adr_01_index.md`, but this cycle's verification found no matrix row for ADR-002 INV-04 and no ADR-017 row; the generated blocks must not be hand-edited and no regeneration is triggered, so the file is kept as a Reference File row instead of a modification target.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is a scope amendment against the Issue's "Change only the Target Files" constraint, mandated by the pending-amendment form's ledger-citation rule; user acknowledgement is required before Phase 2 executes.
- The adrchk011 plan's remaining Step 5 (`Validation and hand-off`) does not gate this Plan: the forms and the enforcing checker are already present in the governance documents (verified this cycle).
- Overlap with the already-completed adrchk plans that touched the same ADR files (adrchk005, adrchk006, adrchk011) is compatible: their changes are archived in `plans/done/` and already applied; the Step 8b overlap report confirmed no active Frozen Plan shares these paths.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The maintainer's decision on the INV-04 amendment (approve the proposal wording, approve different wording, or choose the formal-exception alternative) and its approval record | No approval record exists; only the recommended amendment path is stated by the Issue | Phase 2 writes the proposal in the pending-amendment form only; the approval step belongs to the maintainer. `tools/check_adr_structure.py` enforces the form while unapproved | False |
| UNK-02 | adrchk011 (ADR Approval Governance) plan Step 5 (`Validation and hand-off`) is still Pending; its Issue is already archived | None missing: judged by reading its Execution Status rows | `plans/20261118-092611_adrchk011_adr-approval-governance.md` — its Steps 1-4 (forms, ledger, checker enforcement) are `Completed`, which is what this Plan needs; not blocking | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Medium (its Approval Record is enforced by `tools/check_adr_structure.py`; INV-04 wording feeds the Issue's AC-001) | 6 | High (100% single author) | None: docs file, not deployed by deploy.sh |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Medium (ADR-007 INV-09 is a Confirmed Blocking matrix row in the index; wording feeds CI evidence) | 3 | High (100% single author) | None: docs file, not deployed by deploy.sh |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Modify | Low (single bullet citation fix) | 1 | High (100% single author) | None: docs file, not deployed by deploy.sh |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Low (Assumption-section wording only; Decision text untouched) | 14 | High (100% single author) | None: docs file, not deployed by deploy.sh |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium (ledger is cited by every pending bullet; highest churn) | 16 | High (100% single author) | None: docs file, not deployed by deploy.sh |

## Design
Path B analysis (lightweight tooling only; heavy tools skipped per the Tool availability guard — no Python target exists):
- Architecture analysis: the ADR governance layer already encodes the Issue's intent — `config/adr_authority.toml` gives `mcp.authentication` exactly one primary ADR (`ADR-017`, no supplemental), and `ADR-007 → ADR-017` is a registered intentional pair. The design therefore keeps every edit at body-text level, adds no front matter `related` entry and no authority edge, and leaves the generated blocks of `adr_01_index.md` untouched; `tools/check_adr_authority.py` and the front matter/model cross-check stay clean by construction. Import-graph tooling (`grimp`, `pyan3`, `lint-imports`) is `N/A`: no Python file changes.
- Dependency graphing: the concrete changed-file list is the five Implementation Target Files rows. Cross-reference scans: "INV-04" is cited only inside `adr_02_01_002` (lines 182, 233, 339-340); "secret file" appears in ADRs only at `adr_02_03_007` line 356; the index matrix contains no ADR-002 INV-04 row and no ADR-017 row. `config/adr_authority.toml` contains no invariant citations, and ADR-002's only authority edges are `→ ADR-001` and `→ ADR-004` (verified in Step 5), so no authority edge change or generated-block regeneration is triggered; an ADR-017 ↔ ADR-002 edge does not exist today and this Plan does not add one.
- Historical analysis: churn (30d) governance_03 16, adr_002 6, adr_007 3, adr_017 1 (adr_013 14 full history; 0 in the last 30 days); all five files are 100% single-author (High bus factor) — merge conflicts with concurrently edited ADRs are the main historical risk; `git-fame` not installed (author counts from `git log`). No known regression to bisect.
- Operational dependency inspection: `N/A` — no `scripts/`, config, DB, or port change; no locks to check, no dependency upgrade to audit (`pip-audit` N/A). Persisted schema check: `N/A`.
- Open design decision (per the Issue's "(decision) Amend or record a formal exception"): the recommended amendment is prepared in pending form; the exception alternative stays available. Draft proposal wording (subject to maintainer decision, never merged without approval): "INV-04: The Agent's configuration files carry no MCP-server-owned settings. The only MCP-specific value the Agent is given is each enabled server's connection token, supplied through the environment-variable mechanism owned by ADR-017; an enabled server resolving to an empty token aborts startup per ADR-017." Recorded as UNK-01.

## Implementation steps
1. **Phase 1: No-decision wording fixes**
   - [ ] Fix the Negative Consequences citation `INV-03` -> `INV-02` (REQ-002; `docs/10_adr/adr_02_03_017_mcp-authentication.md`)
   - [ ] Reduce item 10 to a reference to ADR-017, remove "or secret files" from the Implementation References, and add the enabled-scope / disabled-exclusion wording to the Fail-Fast token condition (REQ-003; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`)
   - [ ] Reword the token-storage Assumption as a `${ENV:...}` reference resolved at load time and reference ADR-017 for the MCP token convention (REQ-004; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`)
2. **Phase 2: INV-04 decision-task proposal (gated)**
   - [ ] Gate: execute only after the user acknowledges the governance_03 scope amendment and the maintainer authorizes filing the proposal (REQ-005)
   - [ ] Add the `AAL-030` entry to the ADR approval ledger with `Approver: Not recorded` / `Date: Not recorded` (REQ-005; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Add the `**Current Decision Approval (pending)**` bullet under `### Approval Record` stating the proposed INV-04 text and citing `AAL-030`; leave the INV-04 line, Status, and Blocking values unchanged; never write approval text (REQ-005; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`)
3. **Phase 3: Validation and hand-off**
   - [ ] Run the full validation plan below and record results (REQ-001, REQ-006; all target files)
   - [ ] Deploy hand-off: `N/A` — no `scripts/` or `config/` file changes, so no deployment step; commit and push go through `git-commit-and-sync` (REQ-006)

### Release units
N/A: no release unit (each Phase passes validation alone; Phase 2's two file edits land in the same phase row and are internally complete)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Static docs check | `uv run python tools/check_adr_structure.py` | exit 0, no ADR-017 finding |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Static docs check | `uv run python tools/check_adr_structure.py && uv run python tools/check_docs_content_policy.py` | exit 0; no `secret file` string remains (`rg -i "secret file" docs/10_adr/` returns only non-ADR or zero hits) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Static docs check | `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | exit 0 |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Static governance check | `uv run python tools/check_adr_structure.py` | exit 0: pending bullet cites `AAL-030`, which exists |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Static governance check | `uv run python tools/check_adr_structure.py` | exit 0: every cited ledger ID has an entry |
| All target files | Docs quality/format | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py <globs>`, `uv run python tools/check_docs_japanese.py` | exit 0 |
| ADR reference graph | Static cross-check | `uv run python tools/check_adr_reference.py` | exit 0: matrix source refs and front matter/model consistent |
| Authority model | Static model check | `uv run python tools/check_adr_authority.py` | exit 0: no DUP_PRIMARY / DANGLING_ADR / cycle / drift findings |
| Cited test nodes | Static existence check | `uv run python tools/check_adr_invariant_matrix.py` | exit 0: all cited tests still exist |

## Risks
- **Risk**: an implementer writes approval text, a reviewer name, or a date for the INV-04 amendment → **Mitigation**: Phase 2 writes only the pending form with `Not recorded` fields; `tools/check_adr_structure.py` enforces the citation; the Issue's AI Implementation Instruction and AC-005 restate the prohibition.
- **Risk**: the governance_03 scope amendment is not acknowledged and Phase 2 stalls mid-execution → **Mitigation**: the deviation is stated in Scope and Assumptions up front; Phase 2 carries an explicit gate row; Phases 1 and 3 are unaffected by the gate.
- **Risk**: other adrchk plans edit the same ADR files concurrently and a rebase conflict lands in the pending-amendment region → **Mitigation**: high-churn files (`adr_01_index.md` excluded from edits; governance_03 16 commits) are touched with one small appended entry each; `git-commit-and-sync` rebases onto upstream and aborts with a report on conflict.
- **Risk**: fixing the ADR-017 `INV-03` mis-citation could invite adding a new ADR-017 ↔ ADR-002 authority edge or a front matter `related` entry (neither exists today), dragging the change into authority-model and generated-block territory that requires its own approval → **Mitigation**: REQ-006 and the Out-of-Scope list prohibit front matter and authority-edge edits; `config/adr_authority.toml` stays a Reference File row, never a target.
- **Risk**: AC-001 reads as "no contradiction remains" and could tempt an implementer to rewrite the INV-04 line before approval → **Mitigation**: AC-001 carries the explicit caveat; the pending form keeps the INV-04 line unchanged until approval (governance_01).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: no-decision wording fixes in `docs/10_adr/adr_02_03_017_mcp-authentication.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | In Progress | — | — |  |
| 2 | Phase 2: gated proposal — `AAL-030` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and pending bullet in `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | In Progress | — | — | Gated on user acknowledgement of the scope amendment and maintainer authorization |
| 3 | Phase 3: validation and hand-off — full validation plan run, no deploy step (`N/A`: no `scripts/` or `config/` change) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-212828_01_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-212828_02_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-212828_03_docs_10_adr_adr_02_03_017_mcp-authentication.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-212828_04_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-212828_05_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-210631
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes "(no decision needed) Confirm the token loading..."; Unresolved Questions `Needs confirmation` | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Phase 3 (evidence record in the frozen table) | AC-001 | `rg` scans of `config/agent.toml`, `config/*_mcp_server.toml`, `scripts/` (no secret-file path); `scripts/shared/config_utils.py` lines 19-43 (checked in Step 2) | Verified |
| REQ-002 | Reason for Change ("cites INV-03 where the `require_auth_token()` rule is INV-02") | `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Phase 1 | AC-002 | `tools/check_adr_structure.py` | Verified |
| REQ-003 | Required Changes "(no decision needed) Reduce ADR-007 item 10..."; Problem ("environment variable or secret file") | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Phase 1 | AC-003 | `tools/check_adr_structure.py`; `rg -i "secret file" docs/10_adr/` | Verified |
| REQ-004 | Required Changes "(no decision needed) Describe ADR-013 token storage..."; Problem ("plain string in configuration") | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Phase 1 | AC-004 | `scripts/eventbus/config.py` lines 260, 317 (checked in Step 2) | Verified |
| REQ-005 | Required Changes "(decision) Amend ADR-002 INV-04"; Constraints; AI Implementation Instruction | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 2 (gated) | AC-001, AC-005 | `tools/check_adr_structure.py` pending-bullet/ledger citation rule | Verified (form and ledger mechanics confirmed in governance_01/governance_03 this cycle) |
| REQ-005 | Same as above (ledger entry half of the form) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 2 (gated) | AC-005 | `tools/check_adr_structure.py` | Verified (AAL-001..AAL-029 present; next ID AAL-030, checked in Step 2) |
| REQ-006 | Testing Expectations; Acceptance Criteria (checker pass) | `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 3 | AC-006 | `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py`, docs checkers per `routing.md` | Verified (all tools exist and are named in `routing.md` Tools, checked in Step 2) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-212828 -->