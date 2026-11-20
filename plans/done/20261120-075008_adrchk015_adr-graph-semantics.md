## Goal
- Make the ADR graph semantics explicit (edge types, decision-owner direction, and what counts as a reference), close the verified gaps in the authority model data, and close the verified checker gaps (duplicate edges, ADR status validation, EventBus host assertion, front matter check skipping, stale rule citations, and the circular header-list definition) so that the checkers report every violation class named in the source issue.

## Priority
Medium

## Scope
- **In-Scope**:
  - Checker fixes that need no maintainer decision: duplicate-edge detection, ADR status validation, EventBus/loopback host assertion, front matter cross-check independence, stale docstring citations, header-list single source with a readable generated list, standalone documentation for ADR-010, and related-list fixes backed by edges that already exist in the model (Index front matter and ADR-007 adding ADR-017).
  - Approval-gated proposals (prepared, then stopped per the issue constraint): edge-type semantics definitions including decision-owner direction, the reversed `ADR-001 -> ADR-004` `Requires` edge, the missing decision targets (`platform.config-isolation` for ADR-002; `agent.tool-approval` supplemental `ADR-001`), the ADR-004/ADR-005 unlisted-mention additions, and replacing the hard-coded circular-pair count in ADR-016.
  - Tests under `tests/tools/` for each new check and the independence fix; regeneration of the guarded graph sections; tool-description and governance-table sync.
- **Out-of-Scope**: Decision substance of any ADR other than graph and authority semantics (per the issue). Editing scripts/ runtime guards (the loopback binding guards in `scripts/mcp_servers/server.py` and `scripts/eventbus/config.py` stay as-is).
- **Dependencies**: The status set consumed by the new status check is defined by the closed adrchk011 work (its plan is merged; `governance_01` now defines `Proposed` / `Accepted` / `Withdrawn` and `check_adr_structure.py` enforces them — re-verified in Step 2).
  - **Depends on**: plans/done/20261118-092611_adrchk011_adr-approval-governance.md | phase all | the allowed ADR Status set and the pending-amendment/ledger form used by REQ-018 and the approval record for REQ-021..REQ-025; dependency already satisfied (that plan is implemented and merged).

## Background
The issue was filed from the consolidated ADR review (`memo-issue.md`, package `ADRCHK2-M03`). Every review claim was re-verified against current source in Step 2 of this cycle before planning; the verification results are recorded per claim in the Problem section (Confirmed / Partially confirmed / Not confirmed). The ADR index graph sections, the authority model `config/adr_authority.toml`, the shared validator core `tools/_adr_authority_core.py`, and the two governance documents were each read in full.

## Problem
Step 2 re-verification outcome per issue claim:

- Confirmed — Index edge definition vs model: `docs/10_adr/adr_01_index.md` defines an edge as "listed in Related ADRs", while `ADR-016` Decision 7 and the core's `FRONTMATTER_DIVERGENCE` rule permit model-only `Reference` edges; "referenced in the body" is undefined anywhere.
- Confirmed — incomplete lists: Index front matter omits `adr_02_03_017_mcp-authentication.md`; ADR-007 front matter and its `## Related ADRs` (lines 343-346, lists only ADR-002 and ADR-004) omit ADR-017 although the model carries the intentional `ADR-007 --Reference--> ADR-017` pair; ADR-004 body mentions ADR-006/ADR-008 (only reverse model edges exist: `ADR-006 -> ADR-004`, `ADR-008 -> ADR-004`); ADR-005 body mentions ADR-009 (only `ADR-009 -> ADR-005` exists); ADR-010 has no node in the generated graphs and no standalone note.
- Confirmed — reversed decision-owner direction: `ADR-001 --Requires--> ADR-004` (owner -> non-owner) contrasts with `ADR-004 --Requires--> ADR-002` and `ADR-004 --Extends--> ADR-003` (non-owner -> owner) with the same pair structure.
- Confirmed — missing targets: no `[[authority]]` row names ADR-002 as primary or supplemental (Config Isolation unregistered); `agent.tool-approval` primary `ADR-003`, supplemental only `ADR-012`. ADR-016 owning no target is already documented as intentional in ADR-016 Decision 10 (issue claim partially resolved — no fix needed for that half).
- Confirmed — checker gaps: `tools/check_adr_reference.py` cites a non-existent governance anchor (`GV-012 Implementation intent §3` — `grep -n "Implementation intent" governance_04` returns zero matches); `collect_issues()` early-returns on a matrix with no source references, skipping `check_frontmatter_vs_model()`; the core's `_check_config_key` implements only the `mcp_servers.*.url` pattern and never inspects the EventBus host (verified: `_check_config_key` fail-closes on any other `config_keys` pattern; `config/eventbus.toml` carries no host key while `scripts/eventbus/config.py` supports an optional `host` key defaulting to `127.0.0.1`); the core has no duplicate-edge detection (duplicate `(from,to)` pairs are kept in `model.edges` but silently overwritten in `by_pair` during the cycle/bidirectional checks); the core never validates ADR `## Status` values.
- Confirmed — header-list circularity: `governance_01` "ADR Section Header Standardization" defers the list to `check_adr_structure.py` (citing governance_04 "§17 ADR Section Header Compliance" — the actual heading is §18; §17 is Evidence Label Validation), while `check_adr_structure.py` check (c) defers the allowed list to the governance_01 "list" that does not enumerate it. No readable list exists.
- Confirmed — ADR-016 hard-codes "seven" intentional circular pairs in Summary and Problem. Adversarial finding: the same lines are the target of the pending `AAL-018` approval bullet (pair count 6->7 and section rename "awaiting maintainer approval"), so the count replacement is decision-text territory and is folded into the approval-gated package, not an ungated fix.
- Not confirmed as stated — "`check_adr_reference.py` labels a check with another checker's rule ID": GV-012's Tool column does list `check_adr_reference.py`, so the attribution is defensible; the real defect is the fabricated `Implementation intent §3` anchor and the incomplete GV-024 Tool column (§12 documents that `check_adr_reference.py` owns the `FRONTMATTER_DIVERGENCE` half of GV-024, but the row lists only `check_adr_authority.py`).

## Reason for Change
- Undefined semantics leave the reversed edge and the missing targets undetectable and unfixable, while the checker gaps (vacuous front matter pass, duplicate overwrite, no status/host assertion) let whole violation classes ship silently. The circular header-list definition means no reader can see the required heading list at all.

## Implementation Intent
- Land every ungated checker, data, and documentation fix first. Prepare the approval-gated semantics/edge/target changes as written proposals inside this Plan (Design section), and stop before implementing them; nothing gated is edited until an approval record exists. Generate the readable header list into governance_01 inside a guard block from the checker's constant (scope amendment recorded below). Regenerate the guarded graph sections with `tools/generate_adr_authority.py` only; never hand-edit guarded blocks.

## Requirements
- `REQ-001`: `tools/_adr_authority_core.py` reports a duplicate `(from, to)` pair in `[[adr_edge]]` as a new finding code `EDGE_DUPLICATE` (ungated).
- `REQ-002`: `tools/check_adr_authority.py` wires the duplicate check and its docstring lists the new code (ungated).
- `REQ-003`: `tools/generate_adr_authority.py` refuses to generate while `EDGE_DUPLICATE` findings exist (ungated).
- `REQ-004`: `tools/_adr_authority_core.py` parses the allowed ADR Status set from `governance_01` and adds `ADR_STATUS_INVALID` for any model-referenced ADR whose `## Status` value is outside it; ungated.
- `REQ-005`: The core reports `ADR_STATUS_INVALID` when a `Withdrawn` ADR owns a decision target, holds a non-`Reference` edge, or an authority target lists a `Proposed` ADR as primary (governance_01: `Proposed` is not a current specification; `Withdrawn` no longer applies) (ungated).
- `REQ-006`: The core implements a loopback assertion for a new `eventbus.host` config-key pattern against `config/eventbus.toml` (absent key asserts the `127.0.0.1` default of `scripts/eventbus/config.py`) (ungated).
- `REQ-007`: `config/adr_authority.toml` ARCH-002 declares `config_keys = ["mcp_servers.*.url", "eventbus.host"]` and its `current_value` states the server-side loopback guarantee as a code guard (`scripts/mcp_servers/server.py` pre-bind allow-list; no server toml carries a host key — verified), which the config-check does not police (ungated registration wording).
- `REQ-008`: `tools/check_adr_reference.py` runs `check_frontmatter_vs_model()` independently of the matrix: a vacuous-matrix error no longer early-returns and suppresses the cross-check (ungated).
- `REQ-009`: `tools/check_adr_reference.py` docstring drops the non-existent `GV-012 Implementation intent §3` anchor and cites governance_04 §12 plus GV-012 (marker check) and ADR-016 Decision 7 plus GV-024 (front matter check) (ungated).
- `REQ-010`: governance_04 GV-024 Tool column includes `check_adr_reference.py` (registration fix matching §12) (ungated).
- `REQ-011`: `docs/00_governance/governance_01_documentation-policy.md` `## ADR Section Header Standardization` fixes the wrong section reference (§17 -> §18) and states that the readable list in its guarded block is a generated mirror of `check_adr_structure.py`'s constant (ungated wording; block generated per REQ-012).
- `REQ-012`: governance_04 §18 documents the generated-list mechanism and its guard (ungated).
- `REQ-013`: `tools/check_adr_structure.py` exposes its normative heading constant and its docstring states it is the single normative source (ungated).
- `REQ-014`: `tools/generate_adr_authority.py` writes a readable heading list into the governance_01 guarded block from the checker's constant and detects drift in `--check` (scope amendment: this file is outside the issue Target Files list; recorded in Assumptions/Unknowns) (ungated).
- `REQ-015`: `tools/TOOL_DESCRIPTIONS.md` rows updated for the three tools' new behaviors (sync mandated by `check_tool_descriptions_sync.py`) (ungated).
- `REQ-016`: `docs/10_adr/adr_01_index.md` front matter adds `adr_02_03_017_mcp-authentication.md` (no model change needed: the Index front matter is a navigation list excluded from the cross-check) (ungated).
- `REQ-017`: ADR-007 front matter and `## Related ADRs` add ADR-017 (the intentional `ADR-007 --Reference--> ADR-017` edge already exists in the model, so Decision 7 is satisfied without a model change) (ungated).
- `REQ-018`: ADR-010 `## Status` body gains a standalone note: it contributes no authority target or edge and therefore has no node in the generated graphs (first Status line stays `Withdrawn`, per the adrchk011 form) (ungated documentation).
- `REQ-019`: Define in ADR-016 Decision 3 the per-type endpoint semantics — proposal convention: in every normative edge the source ADR is the dependent side and the target ADR owns the decision the source depends on — and define what counts as a reference in an ADR body; `governance_01` carries one short pointer paragraph (approval required; proposal in Design, implementation stopped until approved).
- `REQ-020`: The Index body edge definition is reworded to match the approved semantics (approval required, carried with REQ-019).
- `REQ-021`: Fix the reversed pair: replace `ADR-001 --Requires--> ADR-004` with `ADR-004 --Requires--> ADR-001` and preserve the bidirectional pair as `ADR-001 --Reference (intentional)--> ADR-004` with an ownership-split note; adjust both ADRs' front matter per Decision 7 (approval required).
- `REQ-022`: Register `platform.config-isolation` (primary ADR-002; supplemental ADR-004 limited to failure classification of isolation violations) (approval required).
- `REQ-023`: Add ADR-001 as a supplemental ADR of `agent.tool-approval` with a stated limit (approval required).
- `REQ-024`: List the unlisted body mentions once their edges exist as model edges — add `ADR-004 -> ADR-006`, `ADR-004 -> ADR-008`, `ADR-005 -> ADR-009` `Reference` edges plus the corresponding front matter/Related ADRs entries (approval required as edge additions).
- `REQ-025`: Replace the hard-coded "seven" pair counts in ADR-016 Summary/Problem with a pointer to the generated Intentional Circular References section; fold into the pending AAL-018 approval scope rather than treating it as editorial (approval required).
- `REQ-026`: Regenerate the three guarded graph sections after any approved model change, in the same commit as the model change (ungated mechanism).
- `REQ-027`: Fixture tests: non-loopback EventBus host, duplicate edge, unknown/forbidden status each fail; front matter cross-check runs with an empty matrix; generated governance_01 header block matches the checker constant (ungated).
- `REQ-028`: Final full validation (`rules/toolchain.md` sequence, `generate_adr_authority.py --check`, `check_adr_authority.py`, `check_adr_reference.py`, docs checkers) and `deploy/deploy.sh` sync confirmation for `docs/` and `config/` (ungated).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Front matter navigation list; edge-definition body wording (gated); regenerate guarded graph sections | Add `adr_02_03_017_mcp-authentication.md`; reword edge definition after approval; regenerate `adr-reference-graph`, `adr-authority-graph`, `adr-intentional-cycles` sections after approved model changes | REQ-016, REQ-020, REQ-021, REQ-022, REQ-023, REQ-026 / AC-2, AC-4, AC-6 | Front matter lists ADR-001..ADR-016 but not ADR-017 (read in Step 2); graph sections sit between guard comments | `tools/generate_adr_authority.py --check`, `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Edge-type semantics definition (gated); replace hard-coded pair count (gated, AAL-018 scope); Implementation Notes sync | Decision 3 semantics per REQ-019 proposal; Summary/Problem "seven" -> generated-section pointer; Implementation Notes reflect new finding codes | REQ-019, REQ-025, REQ-026 / AC-5 | Summary and Problem state "seven" (lines 31, 47); pending bullet at line 165 cites AAL-018 for the 6->7 and rename changes awaiting maintainer approval | `tools/check_adr_structure.py`, `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Front matter `related` adjustment after the approved edge reversal | Decision 7 requires non-`Reference` model edges in the owning ADR's front matter; the reversal changes which ADR owns the `Requires` edge | REQ-021 / AC-6 | Model holds `ADR-001 --Requires--> ADR-004` (config read in Step 2) | `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Front matter and Related ADRs additions (gated) | Body cites ADR-006/ADR-008 (line 247 area); unlisted until the approved `ADR-004 -> ADR-006` / `ADR-004 -> ADR-008` edges exist; also front matter change from the approved reversal | REQ-021, REQ-024 / AC-2 | Step 2 grep: ADR-006/ADR-008 mentions in body; no matching forward model edges | `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Front matter and Related ADRs additions (gated) | Body mentions ADR-009; only the reverse `ADR-009 -> ADR-005` edge exists | REQ-024 / AC-2 | Step 2 grep of ADR-009 mentions; config edge list read in full | `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Front matter and `## Related ADRs` add ADR-017 | Body Decisions 9/10 rely on ADR-017; the intentional `ADR-007 -> ADR-017` model edge already exists | REQ-017 / AC-2 | `## Related ADRs` (line 343) lists only ADR-002 and ADR-004; front matter has no ADR-017 entry | `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Standalone note in `## Status` body | Document that the Withdrawn ADR owns no target and no edge, hence no graph node (AC-3 alternative) | REQ-018 / AC-4 | ADR-010 appears in no `[[authority]]` or `[[adr_edge]]` row (config read in full in Step 2) | `tools/check_adr_structure.py` | Verified |
| `config/adr_authority.toml` | ARCH-002 config_keys and current_value (ungated); edge reversal, new targets, new Reference edges (all gated) | Extend loopback assertion coverage; approval-gated graph corrections | REQ-007, REQ-021, REQ-022, REQ-023, REQ-024 / AC-4, AC-6 | `config_keys = ["mcp_servers.*.url"]` only; no authority row names ADR-002; `agent.tool-approval` supplemental lists only ADR-012 | `tools/check_adr_authority.py`, `tools/generate_adr_authority.py --check` | Verified |
| `tools/_adr_authority_core.py` | Duplicate-edge check; status-set parsing and status/ownership validation; EventBus loopback validator | Close the three verified core gaps | REQ-001, REQ-004, REQ-005, REQ-006 / AC-1 | `_check_config_key` implements only `LOOPBACK_PATTERN` and fail-closes otherwise; no duplicate detection in load or cycle/bidirectional checks; no status inspection | `tests/tools/test_adr_authority.py` | Verified |
| `tools/check_adr_reference.py` | Run front matter cross-check independently; docstring citation fix | `collect_issues()` early-returns before `check_frontmatter_vs_model()`; docstring cites non-existent `GV-012 Implementation intent §3` | REQ-008, REQ-009 / AC-3 | Lines 243-266 early return; `grep "Implementation intent" governance_04` -> zero matches | `tests/tools/test_check_adr_reference.py` | Verified |
| `tools/check_adr_structure.py` | Expose normative heading constant; docstring states single-source role | Break the governance_01 <-> checker reference loop by making the checker the declared normative source | REQ-013 / AC-5 | Docstring check (c) defers to a governance_01 "list" that does not enumerate headings | `tests/tools/test_check_adr_structure.py` | Verified |
| `tools/generate_adr_authority.py` | Generate the governance_01 header-list guarded block; refuse generation on model findings incl. new codes | Provide the readable list the issue requires; scope amendment file (see Assumptions) | REQ-003, REQ-014 / AC-5 | Generator already owns three guard blocks in the Index; governance_01 has no guard block today (grep in Step 2) | `tests/tools/test_generate_adr_authority.py` | Verified |
| `docs/00_governance/governance_01_documentation-policy.md` | Fix §17 -> §18 reference; guarded generated header-list block | Single readable list for the required ADR headings inside a guard block | REQ-011, REQ-014 / AC-5 | Section cites "governance_04 §17 'ADR Section Header Compliance'" but governance_04 §17 is Evidence Label Validation and §18 is ADR Section Header Compliance | `tools/check_adr_structure.py`, `tools/check_docs_structure.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | GV-024 Tool column; §18 wording for the generated list | Registration fixes so governance matches the tools | REQ-010, REQ-012 / AC-3 | GV-024 Tool column lists only `check_adr_authority.py` though §12 documents check_adr_reference's cross-check | `tools/check_tool_descriptions_sync.py`, `tools/check_docs_structure.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Rows for `check_adr_authority.py`, `check_adr_reference.py`, `generate_adr_authority.py` | New finding codes and behaviors must stay in sync (mandated by the Tool Descriptions Sync Check) | REQ-015 / AC-3 | Rows 183/185/203 describe current behaviors that this Plan changes | `tools/check_tool_descriptions_sync.py` | Verified |
| `tools/check_module_size_tools_baseline.txt` | Raise the `_adr_authority_core.py` baseline after the three new validators | The baseline check fails when the file grows past its recorded size | REQ-001, REQ-004, REQ-006 / AC-1 | Row `_adr_authority_core.py	25689` exists; three new validators will exceed it | `tools/check_module_size.sh` CI step | Verified |
| `tests/tools/test_adr_authority.py` | Fixtures: duplicate edge, unknown status, Withdrawn/Proposed misuse, non-loopback EventBus host, eventbus path override | Regression coverage for the new core validators | REQ-027 / AC-1 | Existing fixture-based unit tests import the core (scan_change_consumers) | — | Verified |
| `tests/tools/test_check_adr_reference.py` | Fixture: matrix with no source references still runs the front matter cross-check | Lock the independence fix | REQ-027 / AC-3 | Current tests cover the vacuity error but not cross-check independence | — | Verified |
| `tests/tools/test_generate_adr_authority.py` | Tests for the governance_01 header-list block generation and `--check` drift detection; refusal on new findings | Lock the generator behavior | REQ-027 / AC-5 | Existing tests cover the three Index sections only | — | Verified |

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
| `tools/check_adr_authority.py` | Shows which core validators are wired into the CI validator and its docstring's finding-code list; not modified because no change is required beyond wiring already exercised through the core | REQ-002 |
| `config/eventbus.toml` | Confirms the EventBus host is an optional key absent in the live file (REQ-006 asserts the default) | REQ-006 |
| `scripts/eventbus/config.py` | Documents the `host` key default `127.0.0.1` and `_is_public_host` semantics the new assertion mirrors | REQ-006 |
| `scripts/mcp_servers/server.py` | Documents the server-side loopback guard (http_host allow-list) that the config-check cannot police | REQ-007 |
| `plans/done/20261118-092611_adrchk011_adr-approval-governance.md` | Defines the status set and pending/withdrawal forms reused by REQ-004, REQ-005, REQ-018 | REQ-004, REQ-005, REQ-018 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Part 5 ADR approval ledger (AAL entries) that the approval record for REQ-021..REQ-025 must cite | REQ-019..REQ-025 |
| `rules/toolchain.md` | Full validation sequence for REQ-028 | REQ-028 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-004, REQ-005, REQ-006, REQ-027): Fixtures for a non-loopback EventBus host, a duplicate edge, an unknown Status value, and a Withdrawn ADR owning a target each produce a failing finding; the live model passes `tools/check_adr_authority.py` unchanged.
- `AC-2` (REQ-016, REQ-017, REQ-024): After the ungated additions (and the gated ones once approved), GV-004 and the model cross-check report no mismatch.
- `AC-3` (REQ-008, REQ-009, REQ-010, REQ-015): `tools/check_adr_reference.py` runs the front matter cross-check even when the matrix yields no source references; its citations resolve against governance_04; `tools/check_tool_descriptions_sync.py` passes.
- `AC-4` (REQ-018): Each ADR owns or contributes to a target, or is documented as standalone (ADR-010 note; ADR-016 already documented by Decision 10).
- `AC-5` (REQ-011, REQ-012, REQ-013, REQ-014, REQ-025): The required ADR heading list is readable in exactly one place (the governance_01 guarded block, generated from the checker constant); governance_01's section reference resolves to §18; ADR-016 contains no hard-coded pair count (only after the gated change is approved and implemented).
- `AC-6` (REQ-021, REQ-022, REQ-023, REQ-026): After approval and implementation, every normative edge points from the dependent ADR to the decision-owner ADR; ADR-002 and `agent.tool-approval` appear in the authority matrix; the guarded graph sections match `generate_adr_authority.py --check`.
- `AC-7` (REQ-028): `rules/toolchain.md` full sequence passes, `tools/generate_adr_authority.py --check` reports no drift, and the deploy check confirms `docs/` and `config/` are synced (config/adr_authority.toml row synced or documented as repo-local).

## Tests
- `tests/tools/test_adr_authority.py`: duplicate-edge fixture (REQ-001, AC-1); invalid status fixture (REQ-004, AC-1); Withdrawn-owns-target and Proposed-as-primary fixtures (REQ-005, AC-1); non-loopback `eventbus.host` fixture via the new path override, absent-key passes (REQ-006, AC-1).
- `tests/tools/test_check_adr_reference.py`: empty-matrix fixture asserts `FRONTMATTER_DIVERGENCE` findings are still produced alongside the vacuity error (REQ-008, AC-3).
- `tests/tools/test_generate_adr_authority.py`: generated governance_01 block equals the checker constant; `--check` flags a hand-edited block; generation refuses on `EDGE_DUPLICATE` (REQ-003, REQ-014, AC-5).
- Governance/ADR doc edits are validated by the existing docs checker suite run per `routing.md` (REQ-028, AC-7), and ruff/mypy/bandit cover the tool changes per `rules/toolchain.md`.

## Documentation Impact
Yes. ADR-016 (semantics and count wording, gated), `docs/10_adr/adr_01_index.md` (front matter, edge-definition wording gated, regenerated guarded sections), ADR-004/ADR-005/ADR-007/ADR-010 lists and notes, `docs/00_governance/governance_01_documentation-policy.md` (corrected reference plus generated header-list block), and `docs/00_governance/governance_04_documentation-checks.md` (GV-024 row, §18 wording) — all rows above, driven by REQ-009..REQ-025. `tools/TOOL_DESCRIPTIONS.md` syncs under REQ-015.

## Assumptions
- Status set single source: `ADR-016` carries the canonical allowed-values sentence; `governance_01`'s `## ADR Status Definitions` body (which the adrchk011 work already expanded) is read as the descriptive definition and cross-checked against the ADR-016 sentence (drift reported as `ADR_STATUS_INVALID`). Verified current equality: `Proposed`, `Accepted`, `Withdrawn`.
- Scope amendment (reported per the issue constraint): `tools/generate_adr_authority.py` is required to generate the governance_01 guarded block and the baseline file update is required by CI, although neither is in the issue's Target Files list. Both are recorded here as the required report; the rest of the plan changes only issue targets.
- Server-side bind hosts are enforced by code guards, not configuration (verified: no `config/*mcp_server.toml` carries a host key; `scripts/mcp_servers/server.py` hard-codes the loopback allow-list). The config-check extension therefore asserts EventBus host only; ARCH-002 `current_value` records the code-guard half as an assertion the config-check does not police.
- Per the issue's own classification, checker semantics on existing data (status values, duplicate edges, host loopback, list entries backed by existing edges) need no maintainer decision; every change that alters an edge, a target, an ADR decision/invariant text, or a governance definition of semantics (REQ-019..REQ-025) is gated on an approval record citing the governance_03 Part 5 ledger.
- `tools/TOOL_DESCRIPTIONS.md` updates are mandatory sync for tool behavior changes (`check_tool_descriptions_sync.py`) and do not need an approval record.
- The AAL-018 pending bullet already covers the ADR-016 pair-count sentence; REQ-025 extends that pending scope rather than creating a competing edit.
- Plan review 20261120-091749 (user decision): the scope amendment is confirmed, and UNK-01/UNK-03 are reclassified `Blocking? = False` — the Phase 3 approval gate is carried by Execution Status row 3 (`Blocked`), the Blocker Log, and the `Gated:` markers on Phase-3 procedure rows, mirroring the phase-gate form used by the closed adrchk011 plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Maintainer approval for REQ-019..REQ-025 (edge semantics definition, edge reversal, new targets, new Reference edges, ADR-016 count wording) | No approval record exists; ADR-016 line 165 shows the count wording itself is still pending (AAL-018) | Prepare the proposal text in the Design section; stop; implementation of those phases begins only when an approval record citing an AAL entry exists. Reclassified from `True` at plan review 20261120-091749 (user decision): the gate is Phase 3-only and is carried by Execution Status row 3 (`Blocked`), the Blocker Log, and the `Gated:` markers on Phase-3 procedure rows; Phases 1-2 proceed | False |
| UNK-02 | Maintainer sign-off of the recorded scope amendment (generate_adr_authority.py + baseline file) | The issue constraint requires the amendment to be reported and accepted | Recorded in Assumptions and here; confirmed at plan review 20261120-091749 (user decision), so the REQ-014/REQ-015 steps proceed | False |
| UNK-03 | Whether REQ-025 merges under the existing AAL-018 entry or needs a new ledger entry | governance_03 Part 5 entry scope wording | Resolve at proposal review with the ledger owner. Reclassified from `True` at plan review 20261120-091749 (user decision): REQ-025 stays inside the gated Phase 3 package and its procedure rows carry the `Gated:` marker | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Front matter; regenerated guarded sections | All ADR cross-checks read it | 19 | Not measured (single-maintainer repo) | Required: `deploy/deploy.sh` rsyncs `docs/` |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Semantics wording (gated) | Governance docs and checkers cite it | 7 | Not measured | Required: docs rsync |
| `config/adr_authority.toml` | ARCH-002 keys; gated edge/target changes | Core, generator, cross-checker read it | 7 | Not measured | Required: `config/*.toml` is copied to `/opt/llm/config` (no binary rebuild) |
| `tools/_adr_authority_core.py` | Three new validators | Imported by 3 tools + 3 test modules (scan_change_consumers) | 1 | Not measured | None (tools stay repo-local) |
| `tools/check_adr_reference.py` | Flow + docstring fix | CI lint job | 3 | Not measured | None |
| `tools/generate_adr_authority.py` | Governance_01 block generation | CI drift check | — | Not measured | None |
| `docs/00_governance/governance_01_documentation-policy.md` | Guarded generated block | Read by every docs task | 4 | Not measured | Required: docs rsync |
| `docs/00_governance/governance_04_documentation-checks.md` | GV-024 row; §18 wording | CI governance checks | 12 | Not measured | Required: docs rsync |

## Design
- Consumer scan (`tools/scan_change_consumers.py --seed tools/_adr_authority_core.py`): candidates are `tools/check_adr_authority.py` (reference row), `tools/check_adr_reference.py`, `tools/generate_adr_authority.py` (target rows), `tests/tools/test_adr_authority.py`, `tests/tools/test_generate_adr_authority.py`, `tests/tools/test_tool_report_output.py` (target/reference rows), `tools/TOOL_DESCRIPTIONS.md` and `docs/10_adr/adr_02_07_016_adr-authority-model.md` Implementation Notes (target rows). `tests/tools/test_tool_report_output.py` is not affected: the `Finding` shape is unchanged (recorded per the scan procedure).
- Duplicate edges: detect in model load — after `edges` validation, group `(from,to)` pairs and report `EDGE_DUPLICATE` naming every duplicate location; `by_pair` consumers stay as-is (the duplicate can no longer pass silently because it now fails).
- Status validation: `load_model` (or a new `validate_status` step) collects every ADR id referenced by authorities, edges, and assumptions; resolves each via `adr_files_by_id`; parses the first non-empty line of `## Status` (the same convention `check_adr_structure.py` (e) uses); reports `ADR_STATUS_INVALID` for values outside the set parsed from the ADR-016 canonical sentence (cross-checked with governance_01), for a `Withdrawn` ADR owning a target or holding a non-`Reference` edge, and for a `Proposed` ADR listed as primary.
- EventBus assertion: new pattern constant `EVENTBUS_HOST_PATTERN = "eventbus.host"`; the core reads `config/eventbus.toml` (path overridable for fixtures, mirroring the existing `config_path` override), asserts `host` loopback when present and the documented default `127.0.0.1` when absent, and cross-checks that the assumption `current_value` still names the loopback values (existing pattern behavior). Any unknown `config_keys` pattern still fail-closes.
- check_adr_reference flow: `collect_issues()` builds `issues = ([] if refs else [vacuity error]) + check_adr_reference(refs) + check_frontmatter_vs_model()` — no early return.
- Generator: `generate_adr_authority.py` gains a second output target: the governance_01 guarded block `adr-section-header-list`, generated from the constant exported by `check_adr_structure.py` (import direction: generator imports the checker constant; the checker stays the normative source). `--check` verifies both the Index blocks and the governance_01 block. Generation refuses while any model finding (including `EDGE_DUPLICATE`, `ADR_STATUS_INVALID`) exists.
- Approval-gated proposal text (prepared here; NOT implemented until an approval record exists):
  - P1 (REQ-019): "A dependency edge `A --T--> B` (T in Requires/Governs/Specializes/Extends/Exception-to) means A depends on, governs, specializes, extends, or exceptions the decision owned by B; B is the decision-owner endpoint. `Reference` is informational and carries no direction claim. A body reference is normative only when the referenced decision changes behavior of the citing ADR; normative references must appear as a model edge and in the citing ADR's front matter."
  - P2 (REQ-021): reverse `ADR-001 --Requires--> ADR-004` to `ADR-004 --Requires--> ADR-001`; preserve the bidirectional pair as `ADR-001 --Reference (intentional)--> ADR-004` with the ownership-split note — the preserved `Reference` half flips sides together with the reversal, matching the REQ-021 text (aligned at procedure generation 20261120-092705); ADR-001's front matter keeps both entries.
  - P3 (REQ-022): add `decision_target = "platform.config-isolation"`, `primary_adr = "ADR-002"`, supplemental `ADR-004` limited to "failure classification of Config Isolation violations only".
  - P4 (REQ-023): add supplemental `{ adr = "ADR-001", limit = "workflow-level approval gate mandatoriness only; tool-level approval semantics stay under ADR-003" }` to `agent.tool-approval`.
  - P5 (REQ-024): add `ADR-004 -> ADR-006`, `ADR-004 -> ADR-008`, `ADR-005 -> ADR-009` `Reference` edges and matching front matter/Related ADRs entries.
  - P6 (REQ-025): Summary/Problem "seven intentional circular pairs" -> "the intentional circular pairs enumerated by the generated Intentional Circular References section".
  - Each proposal records its own ledger entry requirement (governance_03 Part 5 form established by the adrchk011 work).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Core validator extensions (ungated)**
   - [ ] Implement `EDGE_DUPLICATE`, status validation, and the `eventbus.host` loopback validator with fixture-friendly path overrides (REQ-001, REQ-004, REQ-005, REQ-006; `tools/_adr_authority_core.py`)
   - [ ] Wire the new validators into the CI validator and extend its docstring finding-code list (REQ-002; `tools/check_adr_authority.py` — frozen-table reference row; wiring already exercises through the core, no edit required unless imports change — stop and report if an edit becomes necessary)
   - [ ] Generator refuses generation while any model finding exists (REQ-003; `tools/generate_adr_authority.py`)
   - [ ] ARCH-002 `config_keys`/`current_value` update (REQ-007; `config/adr_authority.toml`)
   - [ ] Fixture tests for the three failure classes and the absent-key pass (REQ-027; `tests/tools/test_adr_authority.py`)
   - [ ] Raise the module-size baseline row after the growth is measured (REQ-001/004/006 validation gate; `tools/check_module_size_tools_baseline.txt`)
2. **Phase 2: Checker independence, single readable header list, ungated documentation (ungated; the recorded scope amendment was confirmed at plan review 20261120-091749, so REQ-014/REQ-015 steps proceed)**
   - [ ] Run the front matter cross-check independently of the matrix result; fix the docstring citations (REQ-008, REQ-009; `tools/check_adr_reference.py`) + independence fixture (REQ-027; `tests/tools/test_check_adr_reference.py`)
   - [ ] Expose the normative heading constant; docstring states single-source role (REQ-013; `tools/check_adr_structure.py`)
   - [ ] Generate the governance_01 header-list guarded block and extend `--check` (REQ-014; `tools/generate_adr_authority.py`, `docs/00_governance/governance_01_documentation-policy.md`) + generator tests (REQ-027; `tests/tools/test_generate_adr_authority.py`)
   - [ ] governance_01 §17->§18 reference fix and generated-mirror wording (REQ-011; `docs/00_governance/governance_01_documentation-policy.md`); governance_04 GV-024 row and §18 wording (REQ-010, REQ-012; `docs/00_governance/governance_04_documentation-checks.md`)
   - [ ] Tool-description rows sync (REQ-015; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Index front matter adds ADR-017 (REQ-016; `docs/10_adr/adr_01_index.md`); ADR-007 front matter + Related ADRs add ADR-017 (REQ-017; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`); ADR-010 standalone Status-body note (REQ-018; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
3. **Phase 3: Approval-gated semantics and model corrections (STOP — prepare proposals, do not edit)**
   - [ ] Submit proposals P1-P6 (Design section) for maintainer decision; record an approval record citing the governance_03 Part 5 ledger (REQ-019, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025); this step ends the Plan until approval arrives
   - [ ] After approval only: edge reversal + target registrations + Reference edges (REQ-021..REQ-024; `config/adr_authority.toml`), ADR-016 semantics and count wording (REQ-019, REQ-025; `docs/10_adr/adr_02_07_016_adr-authority-model.md`), Index edge-definition wording (REQ-020; `docs/10_adr/adr_01_index.md`), front matter/Related ADRs adjustments (REQ-021, REQ-024; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`)
4. **Phase 4: Regeneration, full validation, deployment check**
   - [ ] Regenerate the three guarded graph sections in the same commit as any approved model change (REQ-026; `docs/10_adr/adr_01_index.md`)
   - [ ] Run the full validation sequence per `rules/toolchain.md` plus `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/generate_adr_authority.py --check` and the docs checkers named in `routing.md` (REQ-028; all target rows)
   - [ ] Deployment validation/scripts check: confirm `deploy/deploy.sh` syncs `docs/` and `config/adr_authority.toml` (or documents the repo-local decision) (REQ-028; `config/adr_authority.toml`, `docs/` rows)

### Release units
**Unit**: model-regen | **Phases**: 3, 4 | **Reason**: approved `config/adr_authority.toml` edge/target changes break `generate_adr_authority.py --check` drift detection until the guarded sections are regenerated; the two phases must land in one commit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_adr_authority_core.py` | Unit fixtures | `uv run pytest tests/tools/test_adr_authority.py` | duplicate-edge, invalid-status, Withdrawn/Proposed misuse, non-loopback eventbus host fixtures each produce the new finding codes; live model clean |
| `config/adr_authority.toml` | Integration | `uv run python tools/check_adr_authority.py` | exit 0 with the new keys; live config passes |
| `tools/check_adr_reference.py` | Unit | `uv run pytest tests/tools/test_check_adr_reference.py`; `uv run python tools/check_adr_reference.py` | cross-check runs on empty matrix; live run reports only gated-pending state (clean) |
| `tools/generate_adr_authority.py` | Unit + integration | `uv run pytest tests/tools/test_generate_adr_authority.py`; `uv run python tools/generate_adr_authority.py --check` | governance_01 block matches the checker constant; no drift on Index sections |
| `tools/check_adr_structure.py` | Unit | `uv run pytest tests/tools/test_check_adr_structure.py` | constant export and single-source wording keep all ADRs passing |
| `docs/` target rows | Docs suite | `routing.md` docs checkers incl. `check_docs_structure.py`, `check_docs_quality.py`, `check_adr_structure.py`, `check_known_deviation_sync.py`, `check_canonical_source_conflicts.py` | no findings; §18 reference resolves |
| All tools | Static + full suite | `rules/toolchain.md` sequence (ruff, mypy, bandit, `uv run pytest`) | all green; baseline file updated once with the diff |

## Risks
- **Risk**: Gated phases stall while Phases 1-2 land, leaving AC-4/AC-5 partially satisfied (ADR-002 target missing) → **Mitigation**: phases are split so every ungated fix lands independently; AC-4 documents ADR-010 and ADR-016 as standalone now, and the ADR-002 gap remains an open approved-pending item tracked in Execution Status, not a silent pass.
- **Risk**: A model edit lands without regeneration, breaking `--check` → **Mitigation**: release unit model-regen forces same-commit regeneration; the generator refuses to run with findings.
- **Risk**: Status parsing diverges between `check_adr_structure.py` and the core → **Mitigation**: single documented convention (first non-empty line), asserted by tests on both sides; any drift surfaces as a cross-check failure.
- **Risk**: Duplicate-edge semantics flag legitimate intentional duplicates → **Mitigation**: the model carries no legitimate duplicate pairs (verified in Step 2); the finding message names both locations for review.
- **Risk**: The new EventBus assertion reports drift when the assumption wording changes → **Mitigation**: REQ-007 wording is written in the same commit as the validator (Phase 1 single commit), mirroring the existing `current_value` cross-check.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: core validator extensions (REQ-001..REQ-007, REQ-027) | Completed | — | — | ungated procedures generated 20261120-092705 (rows 08,09,12,16 + companion tests) landed 20261120: core validator (EDGE_DUPLICATE, status/ownership, eventbus.host), ARCH-002 ungated half, ADR-016 Implementation Notes sync, module-size baseline 36123 |
| 2 | Phase 2: independence + header list + ungated docs (REQ-008..REQ-018, REQ-027) | Completed | — | — | scope amendment confirmed 20261120-091749; procedures generated 20261120-092705 (rows 01,06,07,10,11,12,13,14,15 + companion tests) landed 20261120: cross-check independence, header-list generator + governance_01 guard block, governance_04 GV-024/§18, TOOL_DESCRIPTIONS sync, Index/ADR-007/ADR-010 doc fixes; 10 procedures archived 20261120 |
| 3 | Phase 3: approval-gated proposals P1-P6 (REQ-019..REQ-025) | Blocked | — | — | STOP after proposal submission until an approval record exists (issue constraint) |
| 4 | Phase 4: regeneration + full validation + deploy check (REQ-026, REQ-028) | Pending | — | — | same commit as any Phase 3 model change procedures generated 20261120-092705; execution waits on Phase 3 approval for the model-regen commit gated on row 3 approval; ungated full-suite validation run 20261120 (13113 passed, diff-cover clean) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | No maintainer approval record for edge/target/ADR-text changes (UNK-01); count wording itself pending under AAL-018 (UNK-03) | No | — |
| 2 | Scope amendment (generate_adr_authority.py, baseline file) requires plan-review confirmation (UNK-02) | Yes | 20261120-091749 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261120-092705_01_docs_10_adr_adr_01_index.md.md` | 2, 3, 4 | Procedure | Pending | — | — |
| `implementations/20261120-092705_02_docs_10_adr_adr_02_07_016_adr-authority-model.md.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261120-092705_03_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-092705_04_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-092705_05_docs_10_adr_adr_02_06_005_rag-source-derived-index-relationships.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-092705_06_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_07_docs_10_adr_adr_02_06_010_rag-fallback.md.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_08_config_adr_authority.toml.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261120-092705_09_tools__adr_authority_core.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261120-092705_10_tools_check_adr_reference.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_11_tools_check_adr_structure.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_12_tools_generate_adr_authority.py.md` | 1, 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_13_docs_00_governance_governance_01_documentation-policy.md.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_14_docs_00_governance_governance_04_documentation-checks.md.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_15_tools_TOOL_DESCRIPTIONS.md.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261120-092705_16_tools_check_module_size_tools_baseline.txt.md` | 1 | Procedure | Completed | — | — |
| `tests/tools/test_adr_authority.py` | 1 | Companion | Pending | — | — |
| `tests/tools/test_check_adr_reference.py` | 2 | Companion | Pending | — | — |
| `tests/tools/test_generate_adr_authority.py` | 1, 2 | Companion | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-075008
- **Related target files**: `docs/10_adr/adr_01_index.md`; `docs/10_adr/adr_02_07_016_adr-authority-model.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `docs/10_adr/adr_02_06_010_rag-fallback.md`; `config/adr_authority.toml`; `tools/_adr_authority_core.py`; `tools/check_adr_reference.py`; `tools/check_adr_structure.py`; `tools/generate_adr_authority.py`; `docs/00_governance/governance_01_documentation-policy.md`; `docs/00_governance/governance_04_documentation-checks.md`; `tools/TOOL_DESCRIPTIONS.md`; `tools/check_module_size_tools_baseline.txt`; `tests/tools/test_adr_authority.py`; `tests/tools/test_check_adr_reference.py`; `tests/tools/test_generate_adr_authority.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem — duplicate edges overwrite each other (verified in core) | `tools/_adr_authority_core.py` | Phase 1 | AC-1 | test_adr_authority.py duplicate fixture | Confirmed by repository evidence |
| REQ-002 | Unresolved Questions — check_adr_authority.py not reviewed (reviewed in Step 2) | `tools/check_adr_authority.py` | Phase 1 | AC-1 | test_adr_authority.py | Confirmed by repository evidence |
| REQ-003 | Unresolved Questions — generate_adr_authority.py not reviewed (reviewed in Step 2) | `tools/generate_adr_authority.py` | Phase 1 | AC-1, AC-5 | test_generate_adr_authority.py | Confirmed by repository evidence |
| REQ-004 | Problem — ADR status never checked; Dependencies — status set from adrchk011 | `tools/_adr_authority_core.py` | Phase 1 | AC-1 | test_adr_authority.py status fixture | Confirmed by repository evidence |
| REQ-005 | Governance rule (governance_01 ADR Status Definitions) applied to model ownership | `tools/_adr_authority_core.py` | Phase 1 | AC-1, AC-4 | test_adr_authority.py ownership fixtures | Derived from confirmed evidence |
| REQ-006 | Problem — assumption check verifies only part of ARCH-002 | `tools/_adr_authority_core.py` | Phase 1 | AC-1 | test_adr_authority.py eventbus fixture | Confirmed by repository evidence |
| REQ-007 | config/adr_authority.toml ARCH-002 row (read in Step 2) | `config/adr_authority.toml` | Phase 1 | AC-1 | check_adr_authority live run | Confirmed by repository evidence |
| REQ-008 | Problem — early return skips the front matter check (verified lines 243-266) | `tools/check_adr_reference.py` | Phase 2 | AC-3 | test_check_adr_reference.py independence fixture | Confirmed by repository evidence |
| REQ-009 | Problem — wrong rule ID label; verified as non-existent anchor | `tools/check_adr_reference.py` | Phase 2 | AC-3 | docstring citation check in review | Confirmed by repository evidence |
| REQ-010 | governance_04 GV-024 row vs §12 text mismatch | `docs/00_governance/governance_04_documentation-checks.md` | Phase 2 | AC-3 | check_tool_descriptions_sync.py | Confirmed by repository evidence |
| REQ-011 | Problem — section reference points at the wrong section number | `docs/00_governance/governance_01_documentation-policy.md` | Phase 2 | AC-5 | check_docs_structure.py | Confirmed by repository evidence |
| REQ-012 | Problem — header rules point at each other | `docs/00_governance/governance_04_documentation-checks.md` | Phase 2 | AC-5 | check_docs_quality.py | Confirmed by repository evidence |
| REQ-013 | Header circularity — checker docstring check (c) | `tools/check_adr_structure.py` | Phase 2 | AC-5 | test_check_adr_structure.py | Confirmed by repository evidence |
| REQ-014 | Required Changes — generate readable list into governance_01 guard block (scope amendment UNK-02) | `tools/generate_adr_authority.py` | Phase 2 | AC-5 | test_generate_adr_authority.py governance block test | Derived from confirmed evidence |
| REQ-015 | Tool Descriptions Sync Check requirement for changed tools | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-3 | check_tool_descriptions_sync.py | Derived from confirmed evidence |
| REQ-016 | Problem — Index front matter omits ADR-017 | `docs/10_adr/adr_01_index.md` | Phase 2 | AC-2 | check_docs_structure.py | Confirmed by repository evidence |
| REQ-017 | Problem — ADR-007 omits ADR-017 | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Phase 2 | AC-2 | check_adr_reference.py | Confirmed by repository evidence |
| REQ-018 | Problem — ADR-010 has no node and no standalone note | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 2 | AC-4 | check_adr_structure.py | Confirmed by repository evidence |
| REQ-019 | Required Changes (decision) — define reference and edge types | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 3 | AC-5, AC-6 | proposal review (N/A: gated) | Explicit in issue |
| REQ-020 | Problem — Index edge definition mismatch | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-6 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-021 | Problem — reversed decision-owner direction (decision) | `config/adr_authority.toml` | Phase 3 | AC-6 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-021 | Same (front matter side) | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 3 | AC-6 | check_adr_reference.py after approval | Confirmed by repository evidence |
| REQ-021 | Same (ADR-004 side) | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 3 | AC-2, AC-6 | check_adr_reference.py after approval | Confirmed by repository evidence |
| REQ-022 | Problem — Config Isolation not registered (decision) | `config/adr_authority.toml` | Phase 3 | AC-4, AC-6 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-023 | Problem — agent.tool-approval omits ADR-001 (decision) | `config/adr_authority.toml` | Phase 3 | AC-6 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-024 | Problem — ADR-004/ADR-005 unlisted mentions (edge additions = decision) | `config/adr_authority.toml` | Phase 3 | AC-2, AC-6 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-024 | Same (ADR-004 lists) | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 3 | AC-2 | check_adr_reference.py after approval | Confirmed by repository evidence |
| REQ-024 | Same (ADR-005 lists) | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Phase 3 | AC-2 | check_adr_reference.py after approval | Confirmed by repository evidence |
| REQ-025 | Problem — hard-coded pair count; adversarial finding: pending AAL-018 scope | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 3 | AC-5 | proposal review (N/A: gated) | Confirmed by repository evidence |
| REQ-026 | Constraint — regenerate guarded blocks only via the generator | `docs/10_adr/adr_01_index.md` | Phase 4 | AC-6 | generate_adr_authority.py --check | Explicit in issue |
| REQ-027 | Testing Expectations | `tests/tools/test_adr_authority.py` | Phase 1 | AC-1 | new fixtures | Explicit in issue |
| REQ-027 | Testing Expectations | `tests/tools/test_check_adr_reference.py` | Phase 2 | AC-3 | independence fixture | Explicit in issue |
| REQ-027 | Testing Expectations | `tests/tools/test_generate_adr_authority.py` | Phase 2 | AC-5 | governance block test | Explicit in issue |
| REQ-028 | Testing Expectations / Validation sequence | `tools/check_module_size_tools_baseline.txt` | Phase 1 | AC-7 | CI module-size step | Derived from confirmed evidence |
| REQ-028 | Validation sequence and deploy check | `docs/10_adr/adr_01_index.md` | Phase 4 | AC-7 | full validation run | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-092705 -->