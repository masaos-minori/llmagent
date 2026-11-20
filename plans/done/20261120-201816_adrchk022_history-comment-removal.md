## Goal
- Remove every history-style statement (commit references, rename/move/removal notes, removal dates, search-result notes) from the five active documents and configuration files named below, rewriting each as a statement of the current specification, with no behavior change and no configuration-value change.

## Priority
Low

## Scope
- **In-Scope**: Rewrite or delete the history statements in `docs/10_adr/adr_02_03_017_mcp-authentication.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, and `config/documentation_canonical_sources.toml`; re-run the history searches before each edit and skip any statement already gone (per the source issue's AI Implementation Instruction).
- **Out-of-Scope**: `docs/10_adr/adr_02_06_010_rag-fallback.md` (ADR-010 is `Withdrawn` in the current source and in the archived adrchk011 governance plan, so the issue's skip constraint applies); behavior changes; any configuration value change; any file outside the Implementation Target Files table.
- **Dependencies**: N/A: none open. The predecessors the source issue names (rmcompat007, adrchk011, agentcfg001, agentcfg002) are closed (archived issue/plan records); agentcfg002's generated procedures are still in flight and edit `config/agent.toml` (compatible overlap, recorded in Assumptions); agentcfg003 and agentcfg004 are open issues with no required order — the later change re-runs the history searches.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-L01`; merged from ADRCHK-L12 round 2 and round 5 Low findings) as `issues/20261117-123022_adrchk022_history-comment-removal.md`. The review claims carried the evidence label `Documentation only`; this Plan re-verified each claim against current source (Steps 2-3) and confirmed every claim except the ADR-010 item, which the issue's own skip constraint excludes because ADR-010 is now `Withdrawn`.

## Problem
Change history is written into active documents and configuration: ADR-017 cites a removal commit twice (lines 56 and 97); governance_05 records a removed import (line 138); `config/agent.toml` carries a move note (lines 28-30) and three removed-key NOTE blocks with removal dates and re-add instructions (lines 42-49, 51-56, 371-377); `config/rag_pipeline_mcp_server.toml` carries a removed-key NOTE block (lines 24-30); `config/documentation_canonical_sources.toml` carries two "candidate replacement for" migration notes (lines 22 and 29). All were re-confirmed present in the current working tree in Step 2/3. The source issue's open question about whether the earlier rmcompat007 sweep already removed these statements is resolved: the statements are still present, so the sweep did not remove them.

## Reason for Change
- The Current-Specification-Only policy and the `check_docs_quality` rules forbid history in active documents.
- History text makes readers think the old behavior still matters. Nothing makes the change time-sensitive.

## Implementation Intent
- Active documents and configuration describe only the current specification. History stays in git and in the plans. Each history statement is deleted outright (config NOTE blocks) or rewritten as a present-tense specification statement (ADR and governance prose), keeping every normative claim intact.

## Requirements
- `REQ-001`: Rewrite the two commit-reference statements in ADR-017 (Decision Details item 4 and Alternative B Disadvantages) as current-specification statements; keep the normative content (fail-closed middleware, no bypass mode) unchanged and change no decision, invariant, Blocking value, or authority edge.
- `REQ-002`: Rewrite the governance_05 removed-import sentence (line 138) as a present-tense statement of the current import boundary; do not touch the `## Software Runtime Dependency Graph` edge-list lines that `tools/check_dependency_graph_cycles.py` parses.
- `REQ-003`: In `config/agent.toml`, delete the move note (lines 28-30) and the three removed-key NOTE blocks (lines 42-49, 51-56, 371-377); keep every configuration value byte-identical and keep a short current-field comment (purpose, unit, special values, security meaning, restart requirement) for each current field.
- `REQ-004`: In `config/rag_pipeline_mcp_server.toml`, delete the removed-key NOTE block (lines 24-30); keep every configuration value byte-identical.
- `REQ-005`: In `config/documentation_canonical_sources.toml`, rewrite the two `notes` values (lines 22 and 29) so they state the current canonical role only, deleting the "candidate replacement for docs/architecture.md" and "candidate replacement for deploy.sh" migration framing.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8's Implementation Target Files Validation passed on 20261120-201816 — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Modify | Rewrite the two commit-reference history statements (lines 56, 97) as current-specification statements | REQ-001; AC-1, AC-2 | Lines 56 and 97 contain "was removed (commit `cad5e91ea`)" / "was already removed in commit `cad5e91ea`" (checked in Step 2) | `tools/check_docs_quality.py`; `tools/check_adr_preservation.py`; `tools/check_adr_structure.py` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Rewrite the removed-import note (line 138) as a present-tense boundary statement | REQ-002; AC-1 | Line 138: "its former `rag.corpus_identity` import was removed with RAGCORPUS001 Option B" (checked in Step 2) | `tools/check_docs_quality.py`; `tools/check_docs_structure.py`; `tools/check_dependency_graph_cycles.py` | Verified |
| `config/agent.toml` | Modify | Delete the move note (lines 28-30) and the removed-key NOTE blocks (lines 42-49, 51-56, 371-377); keep all values | REQ-003; AC-1, AC-3, AC-5 | Lines 28, 42, 51, 371 matched the history search `moved from|removed on|formerly|grep for|is empty` and the NOTE/date scan `NOTE|2026-|removed` (checked in Step 2) | `tests/agent/test_removed_config_keys_rejected.py`; `tests/agent/test_config_builders.py`; `tools/generate_reference_table.py --check` | Verified |
| `config/rag_pipeline_mcp_server.toml` | Modify | Delete the removed-key NOTE block (lines 24-30); keep all values | REQ-004; AC-1, AC-5 | Lines 24-30 NOTE block names removed keys `host`, `port`, `http_timeout` with removal date 2026-07-13 and a re-add instruction (checked in Step 2) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py`; `tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Verified |
| `config/documentation_canonical_sources.toml` | Modify | Rewrite the two migration-framed `notes` values (lines 22, 29) as current-role statements | REQ-005; AC-1, AC-4 | Lines 22 and 29 contain "candidate replacement for docs/architecture.md" and "candidate replacement for deploy.sh" (checked in Step 3) | `tools/check_canonical_source_registry.py` | Verified |

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
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Confirm at implementation time that ADR-010 still reads `Withdrawn` (line 28) so the skip constraint still holds before touching any neighboring ADR | REQ-001 (skip rationale); Out-of-Scope |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Canonical current description of `config/rag_pipeline_mcp_server.toml` keys; confirms no doc depends on the NOTE block text being deleted | REQ-004 |
| `docs/23_agent/agent_08_02_configuration-llm-rag.md` | Canonical current description of the Agent-side RAG config boundary; confirms no doc depends on the agent.toml NOTE block text | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001..REQ-005): `uv run python tools/check_docs_quality.py` passes, and the history search re-run (`rg -n -i "moved from|removed on|renamed from|was removed|candidate replacement|grep for" <the five target files>`) returns no history-style hit in those files. Two retained lines are explicitly classified as current specification, not history: governance_05 line 23 (conditional policy text "removed or renamed") and `config/agent.toml` line 250 ("Accepted posture (Option B, 2026-10-25)", a current-posture statement).
- `AC-2` (REQ-001): `uv run python tools/check_adr_preservation.py` reports no ERROR for `docs/10_adr/adr_02_03_017_mcp-authentication.md` (no invariant, reference, test citation, Known Deviations, or Approval text changed).
- `AC-3` (REQ-003): `uv run python tools/generate_reference_table.py --check` passes and the `config/agent.toml` diff is comment-only (no value changed, including values equal to code defaults).
- `AC-4` (REQ-005): `uv run python tools/check_canonical_source_registry.py` passes.
- `AC-5` (REQ-003, REQ-004): the config-rejection and config-build tests pass unchanged: `uv run pytest tests/agent/test_removed_config_keys_rejected.py tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py tests/agent/test_config_builders.py`.

## Tests
- No new tests: the change is comments-only and documentation prose with no behavior change (source issue Out of Scope: "Behavior changes").
- Regression coverage (REQ-003, REQ-004): run the existing removed-key rejection tests (`tests/agent/test_removed_config_keys_rejected.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py`) — they pin the load-time rejection behavior that the deleted NOTE blocks describe.
- Documentation consistency (REQ-001, REQ-002): `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_adr_preservation.py`, `tools/check_dependency_graph_cycles.py` (AC-1, AC-2).
- Configuration integrity (REQ-003, REQ-004, REQ-005): `tools/generate_reference_table.py --check`, `tools/check_canonical_source_registry.py`, and the pytest run under AC-5 (AC-3, AC-4, AC-5).

## Documentation Impact
Yes. The documentation edits are the change itself: the ADR and governance rows named by `docs/00_index.md` "Document References by Task" are updated through the Implementation Target Files rows (REQ-001, REQ-002). No additional `docs/*.md` file requires updating; no new document is required.

## Assumptions
- The overlap on `config/agent.toml` with the in-flight agentcfg002 procedures (the open procedure documents `implementations/20261120-132256_11_config_agent.toml.md` and `implementations/20261120-154254_01_config_agent.toml.md`) is compatible: this Plan edits comments only; those procedures edit values/structure; the source issue states no required order and that the later change re-runs the history searches.
- The same compatibility applies to the future agentcfg003 and agentcfg004 plans, which the source issue also lists with no required order.
- `config/agent.toml` line 250 ("Accepted posture (Option B, 2026-10-25)") states the current accepted posture and is not a removal/rename/move statement; it is kept.
- governance_05 line 23 is conditional policy text ("if a documented command is removed or renamed"), not history; it is kept.
- ADR-010 is skipped per the source issue's constraint, verified against current source: the file reads `Withdrawn` (line 28) and the adrchk011 governance Plan is archived under `plans/done/`.
- The removed config keys stay rejected at config load after the NOTE blocks are deleted; the rejection behavior lives in code and tests, not in the comments (Step 3: no match for `web_search_max_results|use_two_stage_fetch|two_stage_max_docs|healthcheck_mode|HealthcheckMode` under `scripts/` or `tools/`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The deleted NOTE blocks currently carry the only in-file guidance for the four removed keys; the source issue routes that guidance to the agentcfg006 reduction-integration-verification migration table, which does not exist yet (agentcfg006 has no Plan) | No agentcfg006 Plan or migration table yet | Implementer follows this Plan's deletion as stated (history stays in git and plans); guidance placement is confirmed when the agentcfg006 issue is planned | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Modify | Low | 4 | N/A (git-fame not installed) | not applicable (rsynced) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Low | 5 | N/A (git-fame not installed) | not applicable (rsynced) |
| `config/agent.toml` | Modify | Medium | 15 | N/A (git-fame not installed) | not applicable (rsynced) |
| `config/rag_pipeline_mcp_server.toml` | Modify | Low | 3 | N/A (git-fame not installed) | not applicable (rsynced) |
| `config/documentation_canonical_sources.toml` | Modify | Low | 5 | N/A (git-fame not installed) | not applicable (rsynced) |

## Design
Path B analysis results (Step 3 inspection plus `workflow-path-b.md` analyses):

- Architecture analysis: no Python target file; the five targets are two Markdown documents and three TOML files. Consumer scan by `rg`: `governance_05` is parsed only in its edge-list lines (`- A → B`) by `tools/check_dependency_graph_cycles.py` and named by `tools/manage_frontmatter.py` and `tools/check_needs_confirmation_inventory.py`; `config/agent.toml` is read by the Agent config loaders and drives the guarded `AUTO-GENERATED` reference blocks checked by `tools/generate_reference_table.py --check`; `config/rag_pipeline_mcp_server.toml` is loaded by `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (`RAG_PIPELINE_OWN_CONFIG_FILE`, line 62); `config/documentation_canonical_sources.toml` is validated by `tools/check_canonical_source_registry.py`. Comment-only and prose-only edits change none of the parsed data, so no consumer needs a change.
- Dependency graphing: exactly the five table rows require changes; no scripts, tests, or generated manifests change. The `## Software Runtime Dependency Graph` edge lines in governance_05 MUST NOT be touched (REQ-002 boundary).
- Historical analysis: 30-day churn (git log): agent.toml 15, governance_05 5, canonical registry 5, ADR-017 4, rag_pipeline_mcp_server.toml 3. agent.toml is the highest-churn target and has in-flight agentcfg002 procedures editing it — the reason for the re-verify-before-edit step constraint and the Medium blast radius. `git-fame` not available: Bus Factor recorded as N/A per the Tool availability guard.
- Operational dependency inspection: `deploy/deploy.sh` already copies `config/agent.toml` (line 152) and `config/rag_pipeline_mcp_server.toml` (line 162); no `cp` line changes are needed, so every `deploy.sh Impact` is `not applicable (rsynced)`. No port, socket, or DB-lock interaction exists in this scope (comment-only edits; no service or database access), so the `ss`/`fuser` checks are N/A. `pip-audit` N/A: no dependency change. No persisted schema, public API, or shared constant changes, so the consumer scan (`tools/scan_change_consumers.py`) and `rules/persisted-schema-change.md` do not apply.
- Validation quality baseline: `N/A: no Python target` — no Implementation Target Files row is a Python file under `scripts/` or `tools/`, so the radon/vulture/bandit/diff-cover baseline is not run (per `workflow.md` Step 5).
- Design decisions: no open design choice (no module boundary, contract, or config-ownership question); history is deleted outright where it guards nothing current, and rewritten in place where normative content must survive (ADR-017, governance_05, registry notes).

## Implementation steps
1. **Phase 1: ADR and governance prose rewrite**
   - [ ] Re-run the acceptance-criterion history search on `docs/10_adr/adr_02_03_017_mcp-authentication.md` and `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; record evidence; skip any statement already gone (REQ-001, REQ-002; per the source issue's AI Implementation Instruction)
   - [ ] Rewrite ADR-017 lines 56 and 97 as current-specification statements, keeping every normative keyword and decision content unchanged (REQ-001)
   - [ ] Rewrite governance_05 line 138 as a present-tense boundary statement without touching the edge-list lines (REQ-002)
   - [ ] Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_adr_preservation.py`, `tools/check_dependency_graph_cycles.py` (AC-1, AC-2)
2. **Phase 2: Configuration comment cleanup**
   - [ ] Re-run the acceptance-criterion history search on `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, and `config/documentation_canonical_sources.toml`; record evidence; skip any statement already gone (REQ-003, REQ-004, REQ-005; per the source issue's AI Implementation Instruction)
   - [ ] Delete the move note and the three removed-key NOTE blocks from `config/agent.toml`; keep every value byte-identical and keep short current-field comments (REQ-003)
   - [ ] Delete the removed-key NOTE block from `config/rag_pipeline_mcp_server.toml`; keep every value byte-identical (REQ-004)
   - [ ] Rewrite the two migration-framed `notes` values in `config/documentation_canonical_sources.toml` (REQ-005)
   - [ ] Run `tools/generate_reference_table.py --check`, `tools/check_canonical_source_registry.py`, and the AC-5 pytest set (AC-3, AC-4, AC-5)
3. **Phase 3: Full validation and deploy hand-off**
   - [ ] Run the validation sequence of `rules/toolchain.md` applicable to a docs/config-only diff (`uv run python tools/run_validation_gates.py` fast and full modes) (REQ-001..REQ-005)
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md`: the change is committed and pushed first; deploying is the user's decision (approval gate). Prerequisite stated per plan; no deploy action is taken by the implementer (REQ-003, REQ-004)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Doc-quality + ADR-preservation check | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py` | Pass; no ERROR from `check_adr_preservation.py`; no commit-reference hit |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Doc-quality + structure + graph-cycle check | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_dependency_graph_cycles.py` | Pass; edge list unchanged and acyclic; no removal-note hit |
| `config/agent.toml` | Comment-only diff + generated-block drift + config tests | `git diff -- config/agent.toml` (comment-only review); `uv run python tools/generate_reference_table.py --check`; `uv run pytest tests/agent/test_removed_config_keys_rejected.py tests/agent/test_config_builders.py` | Pass; every value unchanged; tests pass unchanged |
| `config/rag_pipeline_mcp_server.toml` | Comment-only diff + config tests | `git diff -- config/rag_pipeline_mcp_server.toml` (comment-only review); `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` | Pass; values unchanged; tests pass unchanged |
| `config/documentation_canonical_sources.toml` | Registry schema validation | `uv run python tools/check_canonical_source_registry.py` | Pass; schema conforms; every registered path exists |

## Risks
- **Risk**: `config/agent.toml` edit conflicts with the in-flight agentcfg002 procedures editing the same file → **Mitigation**: re-run the history searches immediately before editing (Phase 1/2 step constraint), commit early, and let the later change re-run the searches per the source issue; git conflicts resolved in favor of the later re-verification.
- **Risk**: Rewriting ADR-017 prose trips `tools/check_adr_preservation.py` (ERROR on changed invariant/reference/test-citation text) → **Mitigation**: change only the history clauses, keep every normative keyword, decision, and invariant string byte-identical elsewhere; on ERROR, revert the ADR edit (`git checkout -- docs/10_adr/adr_02_03_017_mcp-authentication.md`) and report it as a scope amendment instead of forcing the rewrite.
- **Risk**: Deleting the NOTE blocks removes the in-file guardrail against re-adding removed keys → **Mitigation**: the guardrail is enforced by code and the removed-key rejection tests (`tests/agent/test_removed_config_keys_rejected.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py`); history stays in git per the Implementation Intent (source issue: no maintainer-approval or migration-shim text is written into the config).
- **Risk**: A governance_05 edit accidentally changes a graph edge line and breaks `tools/check_dependency_graph_cycles.py` → **Mitigation**: edit only the prose paragraph around line 138; run the cycle checker as part of Phase 1.
- **Risk**: A registry `notes` rewrite breaks registry validation → **Mitigation**: change only the `notes` string values; run `tools/check_canonical_source_registry.py` in Phase 2.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: rewrite ADR-017 and governance_05 history statements | In Progress | — | — | `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` |
| 2 | Phase 2: delete/rewrite history comments in the three config files | In Progress | — | — | `config/agent.toml`; `config/rag_pipeline_mcp_server.toml`; `config/documentation_canonical_sources.toml` |
| 3 | Phase 3: full validation gates and deploy hand-off | Pending | — | — | All five Implementation Target Files |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261120-202848_01_docs_10_adr_adr_02_03_017_mcp-authentication.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261120-202848_02_docs_00_governance_governance_05_change-impact-and-dependency-graphs.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261120-202848_03_config_agent.toml.md | 2 | Procedure | Pending | — | — |
| implementations/20261120-202848_04_config_rag_pipeline_mcp_server.toml.md | 2 | Procedure | Pending | — | — |
| implementations/20261120-202848_05_config_documentation_canonical_sources.toml.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123022_adrchk022_history-comment-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-201816
- **Related target files**: `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; `config/agent.toml`; `config/rag_pipeline_mcp_server.toml`; `config/documentation_canonical_sources.toml`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem + Required Changes; lines 56 and 97 commit references (checked in Step 2) | docs/10_adr/adr_02_03_017_mcp-authentication.md | Phase 1 | AC-1, AC-2 | check_docs_quality.py; check_adr_preservation.py; check_adr_structure.py | Confirmed by repository evidence |
| REQ-002 | Problem + Required Changes; governance_05 line 138 removal note (checked in Step 2) | docs/00_governance/governance_05_change-impact-and-dependency-graphs.md | Phase 1 | AC-1 | check_docs_quality.py; check_docs_structure.py; check_dependency_graph_cycles.py | Confirmed by repository evidence |
| REQ-003 | Problem + Required Changes; agent.toml lines 28-30, 42-49, 51-56, 371-377 (checked in Step 2) | config/agent.toml | Phase 2 | AC-1, AC-3, AC-5 | generate_reference_table.py --check; tests/agent/test_removed_config_keys_rejected.py; tests/agent/test_config_builders.py | Confirmed by repository evidence |
| REQ-004 | Problem + Required Changes; rag_pipeline_mcp_server.toml lines 24-30 NOTE block (checked in Step 2) | config/rag_pipeline_mcp_server.toml | Phase 2 | AC-1, AC-5 | tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py; tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py | Confirmed by repository evidence |
| REQ-005 | Problem; canonical registry lines 22 and 29 "candidate replacement" notes (checked in Step 3) | config/documentation_canonical_sources.toml | Phase 2 | AC-1, AC-4 | check_canonical_source_registry.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-202848 -->