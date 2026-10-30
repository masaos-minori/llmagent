## Goal
- Record, in one machine-readable model, which ADR is the single primary authority per decision target, which ADR relationship edges are normative versus informational, and which shared architecture assumptions apply to which ADRs; generate the ADR index graphs from the model and enforce it in CI.

## Priority
Medium

## Scope
- **In-Scope**:
  - ADR-016 as the normative decision record for the authority model (owner decision 2026-10-29: new ADR in `docs/10_adr`).
  - Machine-readable model file (authority matrix, typed edges, architecture-assumption registry).
  - Generator for the ADR index dependency/reference graph and authority graph with generated-content markers.
  - CI validators: duplicate primaries, dangling ADR IDs, authority-graph cycles, assumption drift.
  - Extension of `tools/check_adr_reference.py` to front-matter/model consistency.
  - Tool registration and CI wiring (`TOOL_DESCRIPTIONS.md`, `routing.md`, governance checks doc, `ci.yml`).
- **Out-of-Scope**:
  - Re-deciding which ADR is authoritative for any target (contested targets become owner questions).
  - Rewriting ADR bodies beyond front matter and generated sections.
  - ADR invariant evidence checks (`adrgate005`, done) and contract manifests (`adrcov001`).
- **Dependencies**:
  - Blocks `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md` (it generates authority/assumption manifests from this model) and informs `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` (authority home for the mandatoriness registry; owner confirmed: `docs/10_adr` + `registry/` YAML).
  - Related, archived: `issues/done/20261027-155848_adrgate005_enforce-adr-evidence-checks.md` — re-verified: invariant evidence checking exists (`check_adr_invariant_matrix.py`, `.github/run_cited_adr_tests.py`, cited-test matrix in `adr_01_index.md`); this plan does not re-do it.

## Background
Verified against current source (2026-10-29): `docs/10_adr/adr_01_index.md` carries a hand-maintained "ADR Dependency Graph" text block (edge meaning: "lists under Related ADRs and refers to it") plus a prose list of six intentional circular references; authority statements are prose (e.g. index line "ADR-003 remains the authority for RuntimeToolRegistry, Tool ownership, and Routing"). `config/documentation_canonical_sources.toml` + `tools/check_canonical_source_registry.py` map decision targets to canonical source paths, not to primary ADRs. Cycle checking exists only for the software area graph (`tools/check_dependency_graph_cycles.py`, `governance_05_change-impact-and-dependency-graphs.md`), and the index states it does not apply to the ADR reference graph. Shared assumptions (single-host, loopback, local SQLite, single-Agent) recur across 7 ADR files (file-count search). ADR-011 is unassigned (index records this); highest assigned is ADR-015, so ADR-016 is the next free number. The issue's earlier claim that governance lives in `docs/09_architecture_governance.md` is stale — governance docs were reorganized under `docs/00_governance/` by ADR-015.

## Problem
Implementers infer ADR precedence from prose; the diagram, the index, and actual precedence rules can drift because the diagram is hand-edited; a shared assumption that changes has no impact list; the registry cannot answer "which ADR is the primary authority for target X".

## Reason for Change
Maintainability and ownership clarity. No incorrect behavior is currently tied to prose-based precedence (index is internally consistent), but the cost rises as the other issues in this batch add ADR-governed contracts (`dbmig001` amends ADR-008; `mcpgate001` adds a mandatoriness registry; `ragcorpus001` amends ADR-010). This plan must land before `adrcov001` and before those amendments so precedence is machine-checked when they land.

## Implementation Intent
One authoritative model file plus one normative ADR (ADR-016). ADR bodies remain the normative decisions; the model is an index of who owns what, never a second source of decision content. Extend the existing registry/generator/checker idioms (`documentation_canonical_sources.toml`, `generate_reference_table.py --check`, ADR-015 generated-content markers) instead of inventing a parallel mechanism. Separate the informational reference graph (cycles allowed, the six intentional ones representable) from the authority graph (acyclic, enforced).

## Requirements
- `REQ-001`: ADR-016 records the authority-model decision: one primary ADR per governed decision target; supplemental ADRs carry explicit authority limits; edge types `Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`; ADR bodies remain normative; model is index-only.
- `REQ-002`: Machine-readable model file holding the authority matrix (targets: workflow control, component responsibility, routing, LLM visibility, dynamic health, approval, transport, MCP technical safety, EventBus persistence, EventBus authorization, DB recovery, RAG canonical data, fallback, reference generation), typed edges, and the architecture-assumption registry (ID, current value, applicable ADRs, validation method, owner, review triggers).
- `REQ-003`: Generator produces the ADR index sections (reference graph, authority graph, intentional-cycle list) from the model, wrapped in generated-content markers, reproducible via a `--check` mode.
- `REQ-004`: CI validator rejects: a target with two primaries, dangling ADR IDs, cycles in the authority graph, and unacknowledged assumption changes (assumption value vs model drift).
- `REQ-005`: `tools/check_adr_reference.py` extended to validate ADR front matter `related` edges against the model (unknown edge targets, model/reference divergence).
- `REQ-006`: New tools registered in `tools/TOOL_DESCRIPTIONS.md`, `routing.md` tool table, and the governance auto-check inventory; wired into CI.
- `REQ-007`: ADR index and ADR document guide describe the authority model and how generated sections are maintained (intent/boundaries only, per `skills/DESIGN.md` Docs content policy).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-29: every row exists-or-is-new-with-evidence, is linked to a Plan requirement, and is `Verified`; `check_workitem_structure.py` and `check_plan_target_overlaps.py` report no findings. Re-verified 2026-10-29 against `HEAD c5a8285dd` after a tree reorganization landed during planning (`f7f7616f3 refactor: reorganize scripts/ into domain-based packages`); all existing target paths (incl. `config/documentation_canonical_sources.toml`, `docs/00_governance/`, `docs/10_adr/`, `tools/`) re-confirmed present in the tracked tree.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | New ADR: normative record of the authority model, edge types, and graph rules | Owner decision 2026-10-29: model home is a new ADR in `docs/10_adr`; highest existing is ADR-015 | REQ-001 | `adr_01_index.md` ADR List ends at ADR-015; ADR-011 gap documented | `tests/tools/test_adr_authority.py` (structure validation) | Verified |
| `config/adr_authority.toml` | New model file: authority matrix, typed edges, assumption registry | No model answering "primary ADR per target" exists; TOML matches the existing registry family | REQ-002, REQ-004 | `config/documentation_canonical_sources.toml` exists with `[[canonical_sources]]` entries lacking ADR authority | `tests/tools/test_adr_authority.py` | Verified |
| `tools/generate_adr_authority.py` | New generator + `--check`: emit index graph sections from the model with generated-content markers | Dependency graph and intentional-cycle lists are hand-maintained today | REQ-003 | `adr_01_index.md` "ADR Dependency Graph" is a hand-written `text` block; `generate_reference_table.py --check` is the precedent pattern | `tests/tools/test_generate_adr_authority.py` | Verified |
| `tools/check_adr_authority.py` | New validator: duplicate primaries, dangling IDs, authority cycles, assumption drift | No CI check enforces ADR precedence today | REQ-004 | No ADR-graph cycle check exists; `check_dependency_graph_cycles.py` covers only the software area graph | `tests/tools/test_adr_authority.py` | Verified |
| `tools/check_adr_reference.py` | Extend: cross-check ADR front matter `related` edges against the model | Front matter and model must not diverge (AC-4) | REQ-005 | Existing file checks ADR references; model is new | `tests/tools/test_adr_authority.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Replace hand-maintained graph/circular-reference sections with generated blocks; add ADR-016 row | Sections become generated; ADR-016 must appear in the list | REQ-001, REQ-003 | Hand block at "ADR Dependency Graph"; ADR List table verified | `tests/tools/test_generate_adr_authority.py` (`--check` reproducibility) | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Describe the authority model, edge types, and maintenance of generated sections | Issue Documentation Impact | REQ-007 | Guide exists and enumerates ADR-set conventions | docs checkers | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Add the new checks to the Governance Verification Matrix `Method = Auto` cells | `check_auto_check_inventory.py` cross-references documented auto-checks against real scripts | REQ-006 | `tools/check_auto_check_inventory.py` docstring names this file as the authoritative enumeration | `uv run python tools/check_auto_check_inventory.py` | Verified |
| `routing.md` | Register `check_adr_authority.py` and `generate_adr_authority.py` in the Tools table | Same auto-check inventory contract | REQ-006 | Same docstring names `routing.md` as second enumeration source | `uv run python tools/check_auto_check_inventory.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the two new tools | `routing.md` Tools → "When to run which tool" + AGENTS rule 9 (`tools/`↔`TOOL_DESCRIPTIONS.md` drift) | REQ-006 | Tool table exists; churn 73/30d shows it is the live registry | drift checker listed in `routing.md` | Verified |
| `.github/workflows/ci.yml` | Add steps: `tools/check_adr_authority.py` and `tools/generate_adr_authority.py --check` | CI must enforce the model (issue Required Changes) | REQ-004, REQ-006 | `ci.yml` already runs `generate_reference_table.py --check` at line 35 (pattern) | `tests/tools/test_generate_adr_authority.py` | Verified |
| `tests/tools/test_adr_authority.py` | New: validator unit tests (duplicate primaries, dangling IDs, authority cycles, assumption drift) | Issue Testing Expectations | REQ-004 | `tests/tools/` exists with per-tool test precedent (`tests/tools/` dir listing) | — | Verified |
| `tests/tools/test_generate_adr_authority.py` | New: generator reproducibility tests (regenerate == committed; `--check` detects drift) | Issue Testing Expectations | REQ-003 | Same | — | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_00_document-guide.md` | Issue instruction: read before editing ADR set | `docs/10_adr/adr_02_07_016_adr-authority-model.md` |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Generated-content marker pattern (ADR-015) | REQ-003 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Existing local authority for routing/LLM visibility/dynamic health/approval concepts — matrix must record, not re-decide | REQ-002 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Existing failure-classification authority and its INV-16 statement of ADR-010 primacy | REQ-002 |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Existing fallback authority | REQ-002 |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Component responsibility authority | REQ-002 |
| `config/documentation_canonical_sources.toml` | Existing registry to extend idiomatically; decision targets overlap the matrix | REQ-002 |
| `tools/check_canonical_source_registry.py` | Loader/validation idiom for TOML registries | REQ-004 |
| `tools/generate_reference_table.py` | Generator + `--check` idiom and marker format | REQ-003 |
| `tools/_front_matter_schema.py` | ADR front matter field contract (`title`, `area`, `tags`, `related`, `status`) | REQ-005 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | The area-graph cycle rule the index exempts the ADR graph from; authority graph must state its own rule | REQ-001 |
| `tools/check_adr_invariant_matrix.py` | Confirm overlap boundary: invariant evidence stays there, not in this model | Out-of-Scope |

## Acceptance Criteria
- AC-1 (REQ-002): Every governed decision target resolves to exactly one primary ADR; supplemental ADRs state authority limits.
- AC-2 (REQ-004): A second primary claim for any target fails CI (`check_adr_authority.py`).
- AC-3 (REQ-004, REQ-002): Each shared assumption has one authoritative definition and an applicable-ADR impact list; enforceable violations are rejected or explicitly flagged for review.
- AC-4 (REQ-003): Index graph sections are byte-reproducible from the model via `generate_adr_authority.py --check`.
- AC-5 (REQ-005): Adding or changing an ADR cannot leave dangling IDs or model/front-matter divergence undetected.
- AC-6 (REQ-001): ADR bodies are unchanged except front matter and generated sections; ADR-016 approval row appears in the index list.

## Tests
- Validator unit tests (REQ-004): fixture model variants — duplicate primary, dangling ID, authority cycle, assumption drift — each must fail validation; conforming model passes.
- Generator tests (REQ-003): regeneration byte-equals committed index sections; `--check` exits nonzero on drift.
- Reference-check tests (REQ-005): front matter `related` entries absent from the model, and model edges absent from front matter, are both detected.
- CI integration runs (REQ-004/REQ-006): `uv run python tools/check_canonical_source_registry.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/generate_adr_authority.py --check`, `uv run python tools/check_auto_check_inventory.py`, and the docs checkers in `routing.md`.

## Documentation Impact
Yes. `docs/10_adr/adr_01_index.md` (generated sections) and `docs/10_adr/adr_00_document-guide.md` (model description) are target rows; `docs/00_governance/governance_04_documentation-checks.md` and `routing.md` register the new auto-checks. Task mapping follows `docs/00_index.md` governance/ADR rows. Docs describe intent, boundaries, and maintenance rules, not tool internals (`skills/DESIGN.md` Docs content policy).

## Assumptions
- Model data lives in `config/adr_authority.toml` (separate from `documentation_canonical_sources.toml`, sharing its TOML/checker idioms); the normative record is ADR-016. Rationale: the existing registry maps targets to canonical source paths; folding ADR authority into it would mix two claim types. Owner confirmed the ADR home on 2026-10-29; the config-file placement follows from it and is owner-revisable.
- Model ownership: repository owner (consistent with `adr_01_index.md` governance rows naming "Owner: Repository owner").
- The authority matrix records today's prose decisions (ADR-001 workflow control; ADR-014 component responsibility; ADR-003 routing/LLM visibility/dynamic health/approval eligibility; ADR-007 transport; ADR-012 MCP technical safety; ADR-006 EventBus persistence; ADR-013 EventBus authorization; ADR-008 DB recovery/separation; ADR-005 RAG canonical data; ADR-010 fallback; ADR-015 reference generation). No target is contested today; if the validator finds a conflict it becomes an owner question, not a silent choice.
- Assumption set seed: single-host, loopback-only, local SQLite, single-Agent (the seven matching ADR files are enumerated exactly during the procedure phase — UNK-01).
- New ADR takes number 016 in group 07 docs (`adr_02_07_016_adr-authority-model.md`), consistent with `adr_02_07_015_...` file naming.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact count and wording of shared assumptions across the 7 matching ADR files | File-level search counts only | Procedure phase enumerates per-file statements and records canonical wordings in the model | False |
| UNK-02 | Whether any decision target currently has two ADRs claiming primary authority | Only the index was reviewed | First run of `check_adr_authority.py`; any finding is escalated as an owner question | False |
| UNK-03 | Which assumptions are "enforceable" (validator-checkable) vs review-only | No validation method recorded in ADRs today | Model records `validation_method` per assumption; enforceable initially: loopback-only and single-Agent (config-checkable), others review-only | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_01_index.md` | Generated blocks replace hand blocks | Referenced by every ADR-related plan/checker | 38 | High (single author) | N/A: docs only |
| `tools/generate_adr_authority.py` | New tool | CI + docs generation path | N/A (new) | N/A | `tools/` is not rsync-deployed by `deploy.sh` (scripts/config only); no deploy.sh impact |
| `tools/check_adr_authority.py` | New tool | CI gate for all future ADR changes | N/A (new) | N/A | No deploy.sh impact |
| `tools/check_adr_reference.py` | Extension | Existing ADR reference gate | 5 | High (single author) | No deploy.sh impact |
| `config/adr_authority.toml` | New config | Consumed by two tools + CI | N/A (new) | N/A | `config/` is copied by `deploy.sh` selectively per-server; a docs-only config is not in the server copy list — confirm at deploy step, no `deploy.sh` edit planned |
| `docs/00_governance/governance_04_documentation-checks.md` | Matrix rows | Governance auto-check inventory | 50 | High (single author) | N/A: docs only |
| `routing.md` | Tool table rows | Loaded by every agent session | 28 | High (single author) | N/A: repo-local |
| `tools/TOOL_DESCRIPTIONS.md` | Tool rows | Highest-churn registry file; conflict risk with parallel work | 73 | High (single author) | N/A: repo-local |
| `.github/workflows/ci.yml` | New steps | CI runtime | 11 | High (single author) | N/A: CI only |
| Other target rows (ADR-016, guide, tests) | New/edited | ADR set and tool tests | 16 (guide) / N/A | High (single author) | N/A |

## Design
- Model file `config/adr_authority.toml`, three entry families:
  - `[[authority]]`: `decision_target` (dotted, mirroring the canonical-sources naming, e.g. `agent.tool-routing`), `primary_adr = "ADR-003"`, `supplemental_adrs = [{adr = "ADR-004", limit = "failure-classification only"}]`.
  - `[[adr_edge]]`: `from`, `to`, `edge_type` in {`Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`, `Reference`}; `Reference` is the informational edge reproducing today's `A → B` meaning; the six intentional circular pairs are `Reference` edges with `intentional = true`.
  - `[[assumption]]`: `id` (e.g. `ARCH-001`), `name`, `current_value`, `applicable_adrs`, `validation_method` (`config-check` / `manual-review`), `owner`, `review_triggers`.
- Authority graph = non-`Reference` edges; validator enforces acyclicity there only. `Reference` graph may cycle; intentional cycles carry the `intentional` flag so absence is detectable.
- Generator emits three index sections wrapped in AUTO-GENERATED markers (same marker discipline as `generate_reference_table.py`/ADR-015): Reference Graph, Authority Graph, Intentional Circular References. Hand-written prose in the index outside these markers stays intact.
- Validator design: fail-closed with finding codes (`DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE`, `FRONTMATTER_DIVERGENCE`); `FRONTMATTER_DIVERGENCE` is shared with `check_adr_reference.py` (validator core lives in one module both tools import, to avoid two drift-detection logics).
- Assumption drift: for `validation_method = "config-check"`, the validator asserts model `current_value` against config values (loopback-only bind, single-agent process assumptions in `config/agent.toml`); mismatch = finding. For `manual-review`, drift means an ADR body touching the assumption is changed while the model value is untouched — flagged as review, not failure.
- Sequencing: model + tools + tests first; index sections regenerated second; ADR-016 body last (it cites the tool names and generated-section rules).

## Implementation steps
1. **Phase 1: Model and validator core**
   - [ ] Author `config/adr_authority.toml` from current prose authorities (REQ-002; `config/adr_authority.toml`)
   - [ ] Implement `tools/check_adr_authority.py` with shared core importable by `tools/check_adr_reference.py` (REQ-004, REQ-005; `tools/check_adr_authority.py`, `tools/check_adr_reference.py`)
   - [ ] Validator unit tests (REQ-004; `tests/tools/test_adr_authority.py`)
2. **Phase 2: Generator**
   - [ ] Implement `tools/generate_adr_authority.py` with `--check` (REQ-003; `tools/generate_adr_authority.py`)
   - [ ] Regenerate `adr_01_index.md` graph sections; verify byte-reproducibility (REQ-003; `docs/10_adr/adr_01_index.md`)
   - [ ] Generator tests (REQ-003; `tests/tools/test_generate_adr_authority.py`)
3. **Phase 3: CI integration & verification**
   - [ ] Wire both tools into `.github/workflows/ci.yml` and register in `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md` (REQ-006; those rows)
   - [ ] Deployment/scripts check: `config/adr_authority.toml` is repo-local (not a server config) — confirm `deploy.sh` server-config list excludes it; run full validation sequence incl. `check_auto_check_inventory.py` (REQ-006; `.github/workflows/ci.yml`)
4. **Phase 4: Normative ADR and docs**
   - [ ] Write ADR-016 body; add index row via generator/model (REQ-001; `docs/10_adr/adr_02_07_016_adr-authority-model.md`)
   - [ ] Update `docs/10_adr/adr_00_document-guide.md` (REQ-007; that row)
   - [ ] Run ADR/docs checkers from `routing.md` (`check_adr_structure.py`, `check_adr_reference.py`, `check_docs_structure.py`, `check_docs_references`-class checkers) (all REQ)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/adr_authority.toml` + `tools/check_adr_authority.py` | Unit (fixture variants) | `uv run pytest tests/tools/test_adr_authority.py` | Four finding classes detected; conforming model clean |
| `tools/generate_adr_authority.py` + `docs/10_adr/adr_01_index.md` | Integration | `uv run python tools/generate_adr_authority.py --check` | Byte-reproducible; drift exits nonzero |
| `tools/check_adr_reference.py` | Unit + integration | `uv run python tools/check_adr_reference.py` | Front-matter/model divergence detected |
| Registries | Drift/inventory | `uv run python tools/check_auto_check_inventory.py` (+ tool-drift checker from `routing.md`) | New tools registered everywhere; no warnings |
| ADR set | Structure/reference | `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py` | ADR-016 conforms; invariants untouched |
| Whole-repo | Suites | `uv run pytest`, docs checkers from `routing.md` | Green |

## Risks
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` (churn 73/30d) and `adr_01_index.md` (churn 38/30d) are edited by almost every concurrent work item. **Mitigation**: land this plan's doc rows before other batch issues touch the registries; rebase immediately before edits.
- **Risk**: Matrix records a primary that a later batch issue (e.g. ADR-008 migration amendment, ADR-010 corpus amendment) changes mid-flight. **Mitigation**: `dbmig001`/`ragcorpus001` plans must update `config/adr_authority.toml` in their doc phases; AC-2 catches stale primaries automatically.
- **Risk**: `docs/10_adr/adr_01_index.md` is a shared target with `dbmig001` (overlap flagged 2026-10-29). **Mitigation**: fix order — this Plan's index conversion lands before `dbmig001` Phase 6; the ADR List table remains hand-maintained here (only graph sections are generated), so `dbmig001`'s approval row edit stays valid; neither Plan changes the ADR-008 primary claim.
- **Risk**: Generated blocks and hand-written prose collide in `adr_01_index.md`. **Mitigation**: marker-bounded generated regions; generator refuses to write outside markers; hand text moved outside the blocks in the same commit.
- **Risk**: Assumption `config-check` validation misclassifies a config value as violating an assumption. **Mitigation**: only two assumptions start as `config-check`; misfindings escalate to `manual-review`, not silent suppression.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Model and validator core | In Progress | — | — |  |
| 2 | Phase 2: Generator | In Progress | — | — |  |
| 3 | Phase 3: CI integration & verification | In Progress | — | — |  |
| 4 | Phase 4: Normative ADR and docs | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261030-082450_01_docs_10_adr_adr_02_07_016_adr-authority-model.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261030-082450_02_config_adr_authority.toml.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-082450_03_tools_generate_adr_authority.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-082450_04_tools_check_adr_authority.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-082450_05_tools_check_adr_reference.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-082450_06_docs_10_adr_adr_01_index.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261030-082450_07_docs_10_adr_adr_00_document-guide.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261030-082450_08_docs_00_governance_governance_04_documentation-checks.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-082450_09_routing.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-082450_10_tools_TOOL_DESCRIPTIONS.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-082450_11_.github_workflows_ci.yml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-082450_12_tests_tools_test_adr_authority.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261030-082450_13_tests_tools_test_generate_adr_authority.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104504_adrauth001_adr-authority-model.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-214650
- **Related target files**: `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `config/adr_authority.toml`, `tools/generate_adr_authority.py`, `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/00_governance/governance_04_documentation-checks.md`, `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, `.github/workflows/ci.yml`, `tests/tools/test_adr_authority.py`, `tests/tools/test_generate_adr_authority.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent + owner decision 2026-10-29 | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Phase 4 | AC-6 | `check_adr_structure.py` | Explicit in issue |
| REQ-002 | Required Changes (matrix, assumption registry, edge types) | `config/adr_authority.toml` | Phase 1 | AC-1, AC-3 | `tests/tools/test_adr_authority.py` | Explicit in issue |
| REQ-003 | Required Changes (generate graphs) | `tools/generate_adr_authority.py` | Phase 2 | AC-4 | `tests/tools/test_generate_adr_authority.py` | Explicit in issue |
| REQ-003 | Required Changes | `docs/10_adr/adr_01_index.md` | Phase 2 | AC-4 | `generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-004 | Required Changes (CI checks) | `tools/check_adr_authority.py` | Phase 1 | AC-2, AC-5 | `tests/tools/test_adr_authority.py` | Explicit in issue |
| REQ-005 | Constraints + Target Areas (check_adr_reference) | `tools/check_adr_reference.py` | Phase 1 | AC-5 | `uv run python tools/check_adr_reference.py` | Confirmed by repository evidence |
| REQ-006 | Testing Expectations (CI integration) | `.github/workflows/ci.yml` | Phase 3 | AC-2 | CI run | Explicit in issue |
| REQ-006 | Required Changes | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-2 | tool-drift checker | Derived from confirmed evidence |
| REQ-006 | Required Changes | `routing.md` | Phase 3 | AC-2 | `check_auto_check_inventory.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes | `docs/00_governance/governance_04_documentation-checks.md` | Phase 3 | AC-2 | `check_auto_check_inventory.py` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact | `docs/10_adr/adr_00_document-guide.md` | Phase 4 | AC-6 | docs checkers | Explicit in issue |
| REQ-004 | Testing Expectations | `tests/tools/test_adr_authority.py` | Phase 1 | AC-2 | that file | Explicit in issue |
| REQ-003 | Testing Expectations | `tests/tools/test_generate_adr_authority.py` | Phase 2 | AC-4 | that file | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-082450 -->