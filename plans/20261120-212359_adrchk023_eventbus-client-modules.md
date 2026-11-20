## Goal
- Record the governance decision for the two unused EventBus client modules (`scripts/agent/eventbus_subscriber.py`, `scripts/agent/eventbus_topic_admin_client.py`): register one `design-gap` Known Issue entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1, and make the adrrev002 Plan's UNK-02 text reference that entry, so the code, the inventory, and the reference documents agree.

## Priority
Low

## Scope
- **In-Scope**: one new `design-gap` entry in governance_03 Part 1 `### Active Items` (17 template fields, Area/ID decision in Design); one Resolution Path cell update in the UNK-02 row of `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`; the Issue's named validation checks.
- **Out-of-Scope**: deleting the modules; EventBus behavior changes; edits to `docs/23_agent/agent_02_runtime-architecture.md`, `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`, or any `scripts/`, `tests/`, `tools/`, `config/`, `deploy/` file; any ADR edit or approval record (no ADR decision, invariant, Blocking value, or authority edge changes in this Plan, so governance_01/governance_05 approval records are not triggered); writing, paraphrasing, or simulating a maintainer approval statement.
- **Dependencies**: `N/A: none` — the Issue's sibling dependency adrchk009 is closed: its Issue is in the issue archive and its Plan's `Execution Status` shows every row `Completed` (checked in Step 2). The ordering question the Issue raised is resolved because adrchk009 finished before this Plan was written.

## Background
- Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-L02`, merged from ADRCHK-L21, the round-2 Low finding adrrev002 UNK-02). The adrrev002 Plan left UNK-02 undecided with the path "Owner decides; if yes, file a follow-up Issue (this Plan leaves both in place and documents them accurately)" (`plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`, Unknowns table; checked in Step 2). This Issue is that follow-up: governance requires a recorded decision.

## Problem
- The two modules exist under `scripts/agent/` and are imported only by their own unit tests: `rg -n "eventbus_subscriber|eventbus_topic_admin_client" scripts/ tools/ deploy/ config/ .github/` returns only the modules' own docstring headers and `registry/manifests/agent_api.yaml` entries (checked in Step 2). Their public classes are listed in the generated API reference `docs/23_agent/agent_13_reference-api-generated.md` AUTO-GENERATED block, and `docs/23_agent/agent_02_runtime-architecture.md` "EventBus Client Modules" describes them as current libraries while stating no runtime component imports them. The modules therefore look like a supported API.
- The governance_03 `### Unused Features` rule requires such items to be registered as a `design-gap` when a document describes them as current behavior. Part 1 contains no entry naming these modules and no `AGENT-*` or `EVENTBUS-*` item at all (checked in Step 2), so the decision the rule demands is unrecorded.

## Reason for Change
- Under the governance_03 Unused Features rule, unused code must be either registered as a design gap or removed; adrrev002 UNK-02 left this undecided. The decision is now required by governance, and the Issue's decision is the registration branch: register a design-gap entry (the Issue and its `AI Implementation Instruction` forbid deleting the modules in this package).

## Implementation Intent
- Record the decision in the canonical inventory, not in code: one design-gap Known Issue entry following the existing open-pending-decision entry pattern (SHARED-002, MCP-005), and one minimal cell edit in the adrrev002 UNK-02 row that points to that entry. The generated reference and its manifest are regenerated artifacts of the unchanged source and stay untouched; the Agent architecture doc already states the unused status accurately and needs no edit.

## Requirements
- `REQ-001`: Add one `design-gap` Known Issue entry to `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 `### Active Items`, containing the 17 fields required by `### Entry Template`, honoring the Active Items ID-prefix group ordering. The entry records: the two unused agent-side EventBus client modules; their test-only usage evidence; that they are retained per the adrrev002 owner decision pending a future EventBus integration; and a Recommended Action leaving keep-versus-remove as the maintainer's future decision ("Recorded pending that decision; no approval is written here" phrasing pattern). Status `open`, Type `design-gap`, Severity `Low`.
- `REQ-002`: Update the UNK-02 row of `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` so its Resolution Path cell names the new entry's ID as the recorded decision reference. The row's question text and `Blocking?` value `False` stay unchanged; the new cell text is present-tense (no "was undecided", "formerly", or other history-style wording).
- `REQ-003`: Run the Issue's named validation items and the `routing.md` Tools docs checkers, and confirm the diff touches exactly the two target files; all checks pass with no findings.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; Step 8 validation passed — see
`rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Add the design-gap entry | Insert one 17-field `design-gap` entry into Part 1 `### Active Items` at its ID-prefix group position; no other Part changes | REQ-001; AC-01, AC-03 | Part 1 `#### <ID>` headings currently cover only `MCP-001`–`MCP-005` and `SHARED-002`; `rg -n "eventbus_subscriber\|eventbus_topic_admin_client"` over this file returns zero hits; `### Unused Features` states the registration rule (checked in Step 2) | `tests/tools/test_check_issue_inventory_conformance.py`; `tools/check_issue_inventory_conformance.py`; `tools/check_known_deviation_sync.py` | Verified |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Update the UNK-02 Resolution Path cell | Rewrite the cell to name the new entry ID as the recorded decision; question text and `Blocking? False` unchanged | REQ-002; AC-02 | Unknowns table UNK-02 row reads "Owner decides; if yes, file a follow-up Issue (this Plan leaves both in place and documents them accurately)" with no decision reference; in-place editing of this archived Plan as a frozen target row is established precedent (adrchk009 Plan's `Verified` target row and its archived procedure recording the user-confirmed method on 2026-11-18) (checked in Step 2) | `tools/check_workitem_structure.py --archived-status`; `tools/manage_workitem_stage.py show plan plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Verified |

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
| `scripts/agent/eventbus_subscriber.py` | Confirm the module's public surface and the test-only import claim for the entry's `Observed Implementation` field | REQ-001 |
| `scripts/agent/eventbus_topic_admin_client.py` | Same as above for the admin client | REQ-001 |
| `docs/23_agent/agent_02_runtime-architecture.md` | Its `EventBus Client Modules` section states "No runtime component of the Agent process imports these modules; only their unit tests do"; confirms the Unused Features trigger and that no edit is needed there | REQ-001 |
| `docs/23_agent/agent_13_reference-api-generated.md` | Confirm the classes are listed only inside the guarded AUTO-GENERATED block; never edited by hand (Issue constraint) | REQ-001 |
| `registry/manifests/agent_api.yaml` | The generated manifest behind the reference table; listed for the "looks like a supported API" claim; never edited by hand (Issue constraint) | REQ-001 |
| `plans/done/20261118-164413_adrchk009_plan-code-reconcile.md` | Read back the dependency-closure evidence (`Execution Status` all `Completed`) and the archived-plan-edit precedent | REQ-002; Scope |

## Acceptance Criteria
- `AC-01` (REQ-001): governance_03 Part 1 contains exactly one new entry whose `Type` is `design-gap`, that names both modules, carries all 17 `### Entry Template` fields, sits at its group position per the Active Items ordering convention, and `uv run python tools/check_issue_inventory_conformance.py` reports no findings.
- `AC-02` (REQ-002): the UNK-02 row's Resolution Path cell names the new entry ID; `rg -n "UNK-02" plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` shows the reference; `uv run python tools/check_workitem_structure.py --archived-status` reports no finding for this Plan file.
- `AC-03` (REQ-003): `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and `uv run python tools/check_docs_content_policy.py` report no findings, and `git diff --name-only` after the phases lists exactly the two `Implementation Target Files` paths.

## Tests
- No test changes (documentation-only per the Issue's Testing Expectations). Regression coverage is the checker suite that validates the edited documents: `tests/tools/test_check_issue_inventory_conformance.py` and `tests/tools/test_check_needs_confirmation_inventory.py` keep the new entry and the inventory conformance covered (REQ-001, REQ-003).

## Documentation Impact
- Yes. The governance inventory itself is the document updated by REQ-001 (design-gap entry), and the archived adrrev002 Plan is updated by REQ-002 (decision reference). No other `docs/*.md` document requires updating: the Agent architecture and generated API reference were verified in Step 2 as already accurate, and their content is a regeneration of unchanged `scripts/agent/` source. Target doc mapping: Governance row of `docs/00_index.md` "Document References by Task".

## Assumptions
- The recorded decision is retention plus design-gap registration, not removal: the Issue forbids deleting the modules in this package, and the adrrev002 owner decision already left both modules in place with the maintainer planning a future EventBus integration.
- Editing an archived Plan in place is allowed when it is listed as a frozen Plan target row: precedent is the closed adrchk009 Plan, whose `Verified` target row edited this same adrrev002 file and whose archived procedure records the user-confirmed method on 2026-11-18.
- The new entry stays `open` pending the maintainer's future keep-versus-remove decision; the Plan records no approval statement and no ADR change, so no governance_01/governance_05 approval record is required.
- The entry ID prefix is available: Part 1 has no `AGENT-*` or `AGENT`-group or `EVENTBUS-*` entry at write time; the Phase 1 procedure re-runs the prefix search before choosing the ID, per the Issue's re-run constraint.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether archived Plans may be edited (the Issue's Unresolved Question) | N/A: resolved in Step 2 by repository evidence | Resolved: the closed adrchk009 Plan lists `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` as a `Verified` frozen target row, its archived procedure states the in-place method was user-confirmed on 2026-11-18, and `check_workitem_structure.py --archived-status` passed on the result | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Low: governance inventory read by governance checkers and docs readers | N/A (Path A) | N/A (Path A) | not applicable (rsynced) |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Modify | Low: archived workflow document read by plan tools only | N/A (Path A) | N/A (Path A) | not applicable (rsynced) |

## Design
- Path A classification (2 target files, no interface or schema change), recorded in Step 3. Validation quality baseline: `N/A: no Python target` — both targets are Markdown; no `radon`/`vulture`/`bandit`/`diff-cover` baseline applies. Consumer scan: `N/A: no persisted-schema, public-API, or shared-constant change`.
- Entry mechanism: the governance_03 `### Unused Features` rule — a symbol production code exposes but never reads (only tests or documents reference it) is registered as a `design-gap` when a document describes it as current behavior; closely related items share one entry. Both modules are closely related (same layer, same unused status, same adrrev002 UNK-02 question), so one entry covers both, matching the rule's wording.
- Area and ID decision: Area `Agent` (the modules live under `scripts/agent/` and are described by the Agent docs; the EventBus service itself is out of scope), so the ID is `AGENT-001` — the `AGENT-*` group precedes `MCP-*` under the Active Items ordering convention, so the entry is inserted directly after the `### Active Items` ordering-convention paragraph, before `#### MCP-001`. Alternative considered: Area `EventBus` / `EVENTBUS-001` (EventBus domain docs track their issues under Area EventBus); rejected because code ownership and the describing docs are Agent-side. Phase 1 re-verifies no `AGENT-*`/`EVENTBUS-*` entry exists before inserting.
- Entry content pattern: follows the open-pending-decision pattern of `SHARED-002` and `MCP-005` — Status `open`, `Recommended Action` states the maintainer's future choice (retain for the planned EventBus integration, or remove via a follow-up Plan), and an explicit "no approval is written here" statement, satisfying the Issue constraint against approval statements. The entry cites the Issue's `rg` evidence for the test-only status, names both `scripts/agent/` modules, and its `Target` is the Agent docs pair (`docs/23_agent/agent_02_runtime-architecture.md`) only as a document path value of the field — no edit to those docs.
- adrrev002 edit scope: only the UNK-02 `Resolution Path` cell changes. Execution Status, Blocker Log, Work Items Created, and `Freeze status: Frozen` rows are untouched, so the `--archived-status` checker (Status-vocabulary rule) has nothing new to flag. Present-tense wording keeps the Current-Specification-Only policy.
- Generated artifacts untouched: `registry/manifests/agent_api.yaml` and the `agent_13` AUTO-GENERATED block are regenerated from source by `tools/generate_reference_table.py`; `scripts/agent/` is unchanged, so `tools/generate_reference_table.py --check` has no drift to report.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Register the design-gap entry**
   - [ ] Re-run the searches before editing: Part 1 `#### <ID>` heading scan for `AGENT-*`/`EVENTBUS-*` prefixes and the module-name `rg` over `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; record zero-hit output (REQ-001; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Insert the 17-field `AGENT-001` `design-gap` entry after the `### Active Items` ordering-convention paragraph, per the Design section's content pattern (REQ-001; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
2. **Phase 2: Reference the decision from the archived Plan**
   - [ ] Rewrite the UNK-02 Resolution Path cell to name `AGENT-001` as the recorded decision reference, leaving the question text and `Blocking? False` unchanged (REQ-002; `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`)
3. **Phase 3: Verification and deploy hand-off**
   - [ ] Run `uv run python tools/check_issue_inventory_conformance.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_workitem_structure.py --archived-status`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py` (REQ-003; both Implementation Target Files)
   - [ ] Confirm scope with `git diff --name-only` (exactly the two target files) and run the diff's validation gates via `uv run python tools/run_validation_gates.py` (REQ-003; both Implementation Target Files)
   - [ ] Deploy: `N/A: no scripts/ or config/ change` — neither target is a deployed service file (`not applicable (rsynced)` per `skills/DESIGN.md` Change-impact table); no deploy hand-off is required by this Plan

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Structural conformance (automated checker) | `uv run python tools/check_issue_inventory_conformance.py` | Pass; vocabulary, 17-field template, and reference integrity hold for the new entry |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Docs structural/quality/content-policy checks | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py` | Pass with no findings |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issue ID integrity (pre-commit hook also runs it) | `uv run python tools/check_known_deviation_sync.py` | Pass; the new ID has exactly its one heading and no dangling citation |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Needs-confirmation marker registration | `uv run python tools/check_needs_confirmation_inventory.py` | Pass; no new NC marker is introduced and none is left unregistered |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Archived workitem status vocabulary and structure | `uv run python tools/check_workitem_structure.py --archived-status` | Pass; no finding for this Plan file |
| `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | Reference presence read-back | `rg -n "UNK-02" plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` | The Resolution Path cell names `AGENT-001` |
| Both target files | Scope discipline | `git diff --name-only` after Phase 1 and Phase 2 | Exactly the two Implementation Target Files paths |
| Whole diff | Repository gate sequence | `uv run python tools/run_validation_gates.py` (then `uv run pre-commit run --all-files` at commit time per `rules/toolchain.md`) | All applicable gates Pass |

## Risks
- **Risk**: an accidental edit to the generated API reference or its manifest (guarded blocks, Issue constraint) → **Mitigation**: they are Reference Files only; Phase 1 and Phase 2 cite only the two frozen target paths; `tools/generate_reference_table.py --check` (pre-commit) detects any drift in the guarded block.
- **Risk**: ID collision or duplicate entry if a sibling adrchk item edits the same governance file concurrently → **Mitigation**: Phase 1 re-runs the prefix and module-name searches immediately before inserting (Issue constraint); `check_issue_inventory_conformance.py` and `check_known_deviation_sync.py` report duplicate IDs or dangling citations.
- **Risk**: the entry text could read like a maintainer approval statement (Issue constraint forbids writing one) → **Mitigation**: the entry follows the SHARED-002/MCP-005 "Recorded pending that decision … no approval is written here" pattern and changes no ADR decision, invariant, Blocking value, or authority edge, so no approval record is triggered.
- **Risk**: the archived-Plan edit is flagged by the archived-status checker → **Mitigation**: only the Unknowns `Resolution Path` cell changes; no Execution Status row or Status value is touched; `check_workitem_structure.py --archived-status` runs in Phase 3.
- **Risk**: history-style wording leaks into either edit (Current-Specification-Only policy) → **Mitigation**: both edits are written present-tense per the Design section; the compatibility-leftover pre-commit checks (`tools/check_compat_shims.py` family) run at commit time.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: re-run searches, then register the AGENT-001 design-gap entry | Pending | — | — | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` |
| 2 | Phase 2: update the adrrev002 UNK-02 Resolution Path cell | Pending | — | — | `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` |
| 3 | Phase 3: validation gates and scope confirmation (no deploy) | Pending | — | — | Both Implementation Target Files |

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
- **Source issue**: issues/20261117-123023_adrchk023_eventbus-client-modules.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-212359
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem + Required Changes; Step 2 searches: zero production importers, Part 1 has no entry naming the modules, `### Unused Features` rule | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 1 | AC-01, AC-03 | check_issue_inventory_conformance.py; check_known_deviation_sync.py; check_docs_quality.py | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria + Dependencies note; adrrev002 Unknowns UNK-02 row text (checked in Step 2) | plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md | Phase 2 | AC-02 | check_workitem_structure.py --archived-status; rg UNK-02 read-back | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 3 | AC-03 | check_needs_confirmation_inventory.py; check_docs_structure.py; check_docs_content_policy.py | Explicit in issue |
| REQ-003 | Testing Expectations | plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md | Phase 3 | AC-03 | check_workitem_structure.py --archived-status; git diff --name-only | Explicit in issue |
