> **PAUSED** — superseded by adrrev009 (20261111-193537). Implementation halted until adrrev009 lands; its overlapping ADR-008 scope is now owned by adrrev009.

## Goal
Complete the ADR authority model and ADR format where the confirmation pass found real gaps: register the decision targets that two ADRs both define, add the edges and front-matter entries the ADR bodies and the model support, align the section names and finding-code lists between the index, ADR-016, and the guide, complete ADR-012 and ADR-013's format, and correct the one `governance_05` statement that the code contradicts, without changing checker semantics.

## Priority
Medium

## Scope
- **In-Scope**: `config/adr_authority.toml` (two decision targets, edges, intentional pair); front matter and Related ADRs sections of ADR-006, ADR-012, ADR-014; ADR-005's restated FTS rule; ADR-008's target-components line; ADR-012 invariants, Stage and exception definitions, and test file paths; ADR-013's test table Implementation column; ADR-016's section-name and pair-count wording; the ADR index `related` list and regenerated guarded sections; the guide's finding-code list; `governance_05`'s Agent to RAG statement; pending approval records for decision-text edits.
- **Out-of-Scope**: `.github/workflows/ci.yml` and `.pre-commit-config.yaml` (verified: `FRONTMATTER_DIVERGENCE` already runs in CI through `pre-commit run --all-files`); a separate architecture-assumption registry (the `[[assumption]]` list in `config/adr_authority.toml` is the registry); renumbering Decision lists (verified already numbered, except ADR-015's prose Decision, which is a single decision and stays as is); ADR-010 edges (RAG delegation removal issue); the ADR-008 index Status-cell shortening (amendment history removed by the history-wording issue); the mcp_dedup database decision (mcp_dedup ownership plan); the ADR index matrix and invariant-to-test fixes (adrrev015); changing checker semantics; naming Security Reviewers or writing approvals (maintainer).
- **Dependencies**: Depends on the index and matrix Plan because both edit `docs/10_adr/adr_01_index.md` and the generated sections, and numbering and mapping fixes must not be made twice.
  - **Depends on**: plans/20261111-104147_adrrev015_adr-index-matrix.md | phase all | edits the same index rows and ADR bodies (ADR-006, ADR-014); land first so this Plan regenerates the guarded sections once.
  - Related, no ordering edge: the approval-ledger Plan (adrrev012) tracks the pending approvals created here.

## Background
`config/adr_authority.toml` holds the authority matrix (13 decision targets), typed ADR edges, and the `[[assumption]]` registry (ARCH-001 to ARCH-003); ADR-016 defines the model and `tools/check_adr_authority.py` (CI) validates it, while `tools/check_adr_reference.py` runs the front-matter cross-check through the `adr-reference-scoped` pre-commit hook, which CI executes with `pre-commit run --all-files`. Verification (2026-11-11) found: no `rag.fts-text-selection` target although ADR-005 Decision 8 restates ADR-009 INV-03/INV-07; the EventBus loopback-binding decision and test are in ADR-006 (INV-15) with ADR-013 only citing it; ADR-006 has no edge to ADR-008 (the model has only ADR-008 to ADR-006); ADR-012's front matter lists no ADR although the model has ADR-012 to ADR-007; the ADR index `related` omits ADR-016; ADR-016 calls the index section "Reference Graph" while the generator writes "ADR Dependency Graph"; the guide lists four finding codes while the tools and ADR-016 list five (plus `FRONTMATTER_DIVERGENCE`); ADR-012 has invariants for Decision Details #1 to #4 only and leaves "a documented safe exception" and Stages 1 to 3 undefined (the stages are defined only in a code docstring); ADR-013's test table has no Implementation column; `governance_05` says `scripts/agent/` imports nothing from `scripts/rag/`, but `rag_maintenance_service.py` imports `rag.corpus_identity`. Memo claims refuted: no CI gap, no missing ARCH registry file, Decision lists already numbered, no "static tokens" in ADR-013 Out of Scope, no "dry-run exception" in ADR-012.

## Problem
- A decision restated in two ADRs without a registered primary will diverge on the next edit (ADR-016 requires one owner), and the EventBus loopback decision has no registered owner.
- Missing edges and front-matter entries mean impact analysis and `FRONTMATTER_DIVERGENCE` run on an incomplete model, and mismatched section names and finding-code lists make the documents disagree about the checkers.
- ADR-012 and ADR-013 use formats the checkers and readers cannot fully validate, and `governance_05` states a false dependency fact.

## Reason for Change
Without these fixes, authority and impact checks run on an incomplete model; the index and matrix Plan lands first so rows and numbering are not edited twice.

## Implementation Intent
Every decision has one registered primary, every edge the bodies support is in the model and the front matter together, and ADR-012 and ADR-013 follow the format of the other ADRs. Edit the model and the ADR bodies together, regenerate the index sections with the tool, and drop any memo item the current ADRs already satisfy.

## Requirements
- `REQ-001`: Register `rag.fts-text-selection` (primary ADR-009, supplemental ADR-005 limited to FTS synchronization and rebuild operations) and `eventbus.network-binding` (primary ADR-006 by the evidence that INV-15 and its test live there, supplemental ADR-013 limited to authentication layered on top; maintainer to confirm, UNK-01), and change ADR-005 Decision 8 and the matching Implementation Note to reference ADR-009 instead of restating the rule.
- `REQ-002`: Add the ADR-006 to ADR-008 edge as a registered intentional `Reference` pair (with an ownership-split note) and in ADR-006's front matter and Related ADRs; add ADR-007 to ADR-012's front matter and Related ADRs; add ADR-003 to ADR-014's front matter, Related ADRs, and the model (the supplemental entry of `agent.component-responsibility`), and ADR-002/ADR-004 only if the confirmation phase shows ADR-014's body relies on them (UNK-02); add ADR-016 to the ADR index `related`; update ADR-016's pair-count wording.
- `REQ-003`: Align section names and finding-code lists: ADR-016 names the generated sections as the generator writes them; the guide lists the same finding codes as `tools/check_adr_authority.py` plus `FRONTMATTER_DIVERGENCE` and states where each runs.
- `REQ-004`: Complete ADR-012: invariants for Decision Details #5 to #10 drawn from the existing Decision text and the tests its Verification table already cites, the definition of "a documented safe exception" and of Stages 1 to 3 from the code that implements them, and test file paths in the Verification table.
- `REQ-005`: ADR-013's Automated Tests table gains an Implementation column holding the cited test file paths, without changing any verified claim.
- `REQ-006`: ADR-008's Target components include rag-pipeline-mcp, which its recovery table already names.
- `REQ-007`: `governance_05` states the Agent to RAG relationship as the code has it (the Agent imports `rag.corpus_identity`), or keeps the "no edge" statement only if the import is gone when this Plan is implemented.
- `REQ-008`: Each decision-text edit (ADR-005, ADR-006, ADR-008, ADR-012, ADR-014, ADR-016) carries a clearly marked pending approval record, and the Security Reviewer approvals of ADR-012 and ADR-013 are reported as pending maintainer statements with no reviewer name or date invented.
- `REQ-009`: The authority, graph, and front-matter checks pass (`check_adr_authority.py`, `check_adr_reference.py`, `generate_adr_authority.py --check`) and the index guarded sections are regenerated only by the tool.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `config/adr_authority.toml` | Modify | Add two `[[authority]]` targets, the ADR-006/ADR-008 intentional pair, the ADR-012 to ADR-007 front-matter consistency, and the ADR-014 to ADR-003 edge | REQ-001, REQ-002, REQ-009 / AC-1, AC-2, AC-9 | 13 targets at lines 13-91; no `fts` or `network` target; edges end at line 259; `ADR-008 -> ADR-006` Reference edge at lines 212-214 and no reverse edge; `ADR-012 -> ADR-007` at lines 237-239 (checked in Step 3) | `tools/check_adr_authority.py`, `tests/tools/test_adr_authority.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | Add `adr_02_07_016_adr-authority-model.md` to front matter `related`; regenerate the guarded graph sections | REQ-002, REQ-009 / AC-2, AC-9 | Front matter `related` lists ADR-001 to ADR-015 and no ADR-016; the generator writes `## ADR Dependency Graph`, `### Authority Graph`, `### Intentional Circular References` (checked in Step 2) | `tools/generate_adr_authority.py --check`, `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Align the finding-code list (line 71 omits `ASSUMPTION_DRIFT` and `EDGE_UNKNOWN_TYPE`) and where each check runs | REQ-003 / AC-3 | Line 71 lists four codes; `check_adr_authority.py` docstring lists five and `check_adr_reference.py` the front-matter code (checked in Step 2) | `tools/check_docs_structure.py`, `tools/check_docs_quality.py` | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Decision 8 (line 74) and the Implementation Note (line 245) reference ADR-009 for the FTS text-selection rule | REQ-001, REQ-008 / AC-1 | Line 74 "Normal FTS5 synchronization and manual rebuilds use the same generation rule (`COALESCE(normalized_content, content)`)" duplicates ADR-009 INV-03/INV-07 (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Front matter `related` and Related ADRs add ADR-008; state ownership of INV-15 (loopback binding) | REQ-001, REQ-002, REQ-008 / AC-1, AC-2 | Related ADRs lists ADR-002, 004, 013 only; INV-15 at line 188; body cites ADR-008 at line 276 (checked in Step 2) | `tools/check_adr_reference.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Add rag-pipeline-mcp to Target components (line 142) | REQ-006, REQ-008 / AC-6 | Line 142 lists `DbConfig`, `SQLiteHelper`, `create_schema()`, `db/recovery.py`, `db/maintenance.py`; lines 95 and 105 name rag-pipeline-mcp in the recovery table (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Front matter and Related ADRs add ADR-007; invariants for Decision Details #5 to #10; define "documented safe exception" and Stages 1 to 3; test file paths in the Verification table | REQ-002, REQ-004, REQ-008 / AC-2, AC-4 | Front matter lists no ADR; INV-01 to INV-04 only (lines 129-132); Decision #5 "documented safe exception", #9 stage ordering; stages defined only in `write_protection_pipeline.py` docstring; Verification cites test names without file paths (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Add an Implementation column with test file paths to the Automated Tests table (lines 242-) | REQ-005, REQ-008 / AC-5 | Table header `\| Test \| Verifies \| Type \| Blocking \|` has no Implementation column; other ADRs have one (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Front matter `related` and Related ADRs add ADR-003 | REQ-002, REQ-008 / AC-2 | Related ADRs lists ADR-001 only; the model's `agent.component-responsibility` target names ADR-003 as supplemental (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Name the generated sections as the generator writes them (lines 64 and 140) and update the "six intentional pairs" wording | REQ-002, REQ-003, REQ-008 / AC-2, AC-3 | Lines 31, 47, 64, 140 use "Reference Graph" and "six" (checked in Step 2) | `tools/check_adr_authority.py`, `tools/check_adr_structure.py` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Correct the "Agent ↔ RAG: `scripts/agent/` contains no import of `scripts/rag/`" statement (line 124) | REQ-007 / AC-7 | `scripts/agent/services/rag_maintenance_service.py:16` imports `rag.corpus_identity` (checked in Step 3; missing from the issue's target list) | `tools/check_docs_consistency.py --domain overview` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_adr_authority.py` | Finding codes and checks that gate the model | REQ-003, REQ-009 |
| `tools/check_adr_reference.py` | `FRONTMATTER_DIVERGENCE` cross-check; confirms the hook is the CI path | REQ-002, REQ-009 |
| `tools/generate_adr_authority.py` | Writes the three guarded sections; never hand-edit them | REQ-009 |
| `tools/_adr_authority_core.py` | Model validation rules (single primary, edge types, intentional pairs) | REQ-001, REQ-002 |
| `tests/tools/test_adr_authority.py` | Existing model tests; check they stay green with the added targets and edges | REQ-001, REQ-002 |
| `.github/workflows/ci.yml` | Confirms `pre-commit run --all-files` runs the front-matter check; no change | REQ-003 |
| `.pre-commit-config.yaml` | `adr-reference-scoped` hook definition; no change | REQ-003 |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Owner of INV-03 and INV-07 (the FTS text-selection rule) | REQ-001 |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | The ADR-012 to ADR-007 edge target | REQ-002 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | The ADR-014 to ADR-003 edge target | REQ-002 |
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Defines Stages 1 to 9 and the ordering that ADR-012 must state | REQ-004 |
| `scripts/agent/services/rag_maintenance_service.py` | The Agent import of `rag.corpus_identity` | REQ-007 |
| `.importlinter` | Declares the permitted Agent to RAG dependency | REQ-007 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR process, approval evidence standard | REQ-008 |

## Acceptance Criteria
- AC-1: `config/adr_authority.toml` registers `rag.fts-text-selection` and `eventbus.network-binding` each with exactly one primary, and ADR-005 references ADR-009 instead of restating the FTS rule (`REQ-001`).
- AC-2: Every new front-matter `related` ADR entry has a matching model edge, the ADR-006/ADR-008 pair is registered as intentional with a note, and ADR-016 appears in the index `related` list (`REQ-002`).
- AC-3: ADR-016, the index, the guide, and the tools use the same section names and finding-code lists (`REQ-003`).
- AC-4: ADR-012 has an invariant for each Decision Detail, defines the safe exception and Stages 1 to 3, and cites test file paths (`REQ-004`).
- AC-5: ADR-013's test table has an Implementation column with file paths (`REQ-005`).
- AC-6: ADR-008's Target components include rag-pipeline-mcp (`REQ-006`).
- AC-7: `governance_05` agrees with the code's Agent to RAG import (`REQ-007`).
- AC-8: Each decision-text edit has a marked pending approval record; the Security Reviewer approvals are reported as pending, with no invented name or date (`REQ-008`).
- AC-9: `check_adr_authority.py`, `check_adr_reference.py`, `generate_adr_authority.py --check`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `check_docs_structure.py` pass; `check_adr_preservation.py` reports only intended, explained changes (`REQ-009`).

## Tests
- `tests/tools/test_adr_authority.py` and the checker commands are the gate for the model change; no new Python test is planned unless the added targets or edges break an existing fixture, in which case the failing test is updated through a plan amendment (`tools/amend_plan.py`, fallout class).
- Documentation requirements are verified by the checkers in the Validation plan.

## Documentation Impact
ADR-005, 006, 008, 012, 013, 014, 016, the ADR index, the guide, and `governance_05`, located through `docs/00_index.md` "Document References by Task" (governance and overview areas): ownership, edges, invariants, and approvals. State intent and failure behavior only; the index guarded sections are written by `tools/generate_adr_authority.py`. Write in English.

## Assumptions
- `eventbus.network-binding` has primary ADR-006 because the decision (INV-15) and its test are there and ADR-013 only cites it; the issue named ADR-013 and the maintainer confirms the choice (UNK-01).
- The ADR-006/ADR-008 pair is registered as one more intentional `Reference` pair with an ownership-split note (ADR-008 owns the database separation; ADR-006 owns the event store use), consistent with ADR-016 INV-02's one-typed-plus-one-intentional rule.
- Overlap judgment (`tools/check_plan_target_overlaps.py`), all compatible: `config/adr_authority.toml`, `docs/10_adr/adr_00_document-guide.md`, and `docs/10_adr/adr_01_index.md` are also targeted by the MCP audit and authentication Plan (adrrev011 adds its authentication target, ADR-017 edge and rows; this Plan adds different targets, edges, and a finding-code list) and the index Plan (adrrev015, different rows); ADR-006 by the EventBus specification Plan (adrrev014, Scope and Data Ownership) and adrrev015 (INV-13 and test rows), while this Plan edits only front matter, Related ADRs, and INV-15 ownership; ADR-013 by the EventBus authorization Plan (adrrev010), which re-maps three Verification rows in the same test table that this Plan gives an Implementation column, so adrrev010 must land first; ADR-005 by the RAG consistency Plan (adrrev013, Decision 10, 11, and the startup paragraph, not Decision 8); ADR-008 by the recovery, ledger, and EventBus Plans (different lines from the Target components line); ADR-014 by adrrev015 (INV-02 and Decision wording, not front matter); ADR-016 by the ledger Plan (its acceptance sentence, not the section names).
- `.github/workflows/ci.yml` and `.pre-commit-config.yaml` are unchanged because `pre-commit run --all-files` already runs the `adr-reference-scoped` hook in the `lint` job.
- Invariants added to ADR-012 restate behavior its Decision Details and cited tests already define (no new behavior), and stay Blocking only where a cited automated test exists; any without a test is recorded Non-Blocking in the ADR table.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Primary ADR for `eventbus.network-binding` (ADR-006 by evidence; the issue says ADR-013) | Maintainer decision | Confirm at approval; swapping primary and supplemental changes only the toml entry and one ADR note | False |
| UNK-02 | Whether ADR-014's body relies on ADR-002 and ADR-004 (the memo's edges) | The body mentions only ADR-001 | Confirmation in Phase 1: add the edges only where the body states the dependency | False |
| UNK-03 | Stale numeric Decision cross-references, copied template assumptions that contradict ADR-008, and ambiguous Completion Checklist states | Not shown in the confirmation pass | Phase 1 scans ADR text for each; fix only what is shown wrong and record any further item as a fallout row via `tools/amend_plan.py` | False |
| UNK-04 | Whether the Agent import of `rag.corpus_identity` still exists when this Plan is implemented | `plans`/issues for corpus identity may remove it | Re-run `rg "rag\." scripts/agent` at implementation; keep the `governance_05` statement only if no import remains | False |
| UNK-05 | Maintainer approvals: decision-text edits (ADR-005, 006, 008, 012, 014, 016) and named Security Reviewer approvals for ADR-012 and ADR-013 | Approver, date, and scope are `不明`; reviewer names may not be invented | Write marked pending records and report them; the ledger Plan tracks them | False |
| UNK-06 | Whether the index regenerated sections reorder or break after the index Plan lands | Depends on the other Plan's merged state | Land the index Plan first; regenerate with the tool and run `--check` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `config/adr_authority.toml` | Modify | High (read by `check_adr_authority.py`, `generate_adr_authority.py`, CI lint, and tests) | 2 | N/A | not applicable (not deployed to `/opt/llm`) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (generated sections; high churn) | 29 | N/A | not applicable (docs) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 8 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Medium | 2 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium | 8 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Medium | 4 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify | Medium | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Modify | Low | 3 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Medium | 4 | N/A | not applicable (docs) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Modify | Medium (impact analysis input) | 8 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files; the model file feeds CI checks). Findings from the inspection:
- Architecture: the model file is read by `tools/_adr_authority_core.py`; all changes are data and prose, and no Python module changes. Import contracts are unaffected.
- Dependency graph: front matter `related` entries and model edges must move together (`FRONTMATTER_DIVERGENCE` fails when a front-matter ADR has no edge), so each ADR file edit pairs with a toml edit in the same phase.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: none (no process or port). Persisted schema: not applicable. Consumer scan: no persisted schema, public API, or shared constant changes; `not affected: the CI lint job commands are unchanged`.
- Design decisions recorded: (1) rely on the existing pre-commit hook in CI rather than add a second CI step (alternative rejected: a duplicate step adds no coverage and creates a drift risk); (2) keep ARCH assumptions in `config/adr_authority.toml` rather than a separate file (ADR-016 INV-05 already defines it); (3) primary of `eventbus.network-binding` follows where the invariant and test live; (4) a new bidirectional pair is registered as intentional with a note instead of avoiding the edge, because ADR-006's body does cite ADR-008.
- Ordering: ADR bodies and toml in the same phase, then the index `related` list, then `generate_adr_authority.py`, then the checkers.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirmation pass** (all target files; documentation only)
   - [ ] Run `uv run python tools/check_adr_authority.py`, `check_adr_reference.py`, and `generate_adr_authority.py --check` for a baseline.
   - [ ] Scan ADR text for stale numeric Decision references, copied assumptions contradicting ADR-008, and ambiguous Completion Checklist states (UNK-03); confirm whether ADR-014 relies on ADR-002/ADR-004 (UNK-02); drop any item the ADRs already satisfy.
2. **Phase 2: Decision targets and ownership** (REQ-001, REQ-008; `config/adr_authority.toml`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Add the two `[[authority]]` targets; change ADR-005 Decision 8 and the Implementation Note to reference ADR-009; state INV-15's ownership in ADR-006; add pending approval records.
3. **Phase 3: Edges and front matter** (REQ-002, REQ-008; `config/adr_authority.toml`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`)
   - [ ] Add the ADR-006/ADR-008 intentional pair, the ADR-014 to ADR-003 edge (and ADR-002/004 only if UNK-02 supports), and the matching front matter and Related ADRs; add ADR-016 to the index `related`; update ADR-016's pair count.
4. **Phase 4: Section names, finding codes, and format** (REQ-003, REQ-004, REQ-005, REQ-006; `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
   - [ ] Align ADR-016 and the guide with the generator's section names and the tools' finding codes.
   - [ ] Add ADR-012 invariants, the safe-exception and Stage definitions, and test file paths; add ADR-013's Implementation column; add rag-pipeline-mcp to ADR-008's Target components.
5. **Phase 5: governance_05 and regeneration** (REQ-007, REQ-009; `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/10_adr/adr_01_index.md`)
   - [ ] Re-check the Agent import (UNK-04) and correct the statement.
   - [ ] Run `uv run python tools/generate_adr_authority.py`, then `--check`; never hand-edit guarded sections.
6. **Phase 6: Verification** (all target files)
   - [ ] Run the Validation plan commands; run `check_adr_preservation.py` and explain every reported decision change; report the pending approvals (approver, date, scope as `不明`; Security Reviewer names unsupplied) and write none.
   - [ ] No deploy step: no `scripts/` file changes and the CI configuration is unchanged.

### Release units
**Unit**: authority-model | **Phases**: 2, 3 | **Reason**: a front-matter `related` entry without its model edge (or the reverse) fails `FRONTMATTER_DIVERGENCE`/`DANGLING_ADR`, so the ADR edits and the toml edits of Phases 2 and 3 cannot be validated one without the other.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/adr_authority.toml` | Authority model unit tests | `uv run pytest tests/tools/test_adr_authority.py -v` | Pass |
| `config/adr_authority.toml`, ADR files | Model validity (single primary, edges, cycles, assumptions) | `uv run python tools/check_adr_authority.py` | Pass |
| ADR front matter | Front-matter versus model cross-check | `uv run python tools/check_adr_reference.py` | Pass |
| `docs/10_adr/adr_01_index.md` | Guarded sections drift | `uv run python tools/generate_adr_authority.py --check` | No drift |
| ADR files | Structure and invariant matrix | `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py` | Pass |
| ADR files | Decision-change guard | `uv run python tools/check_adr_preservation.py` | Only intended, explained changes (an Approval-text change is reported, never suppressed) |
| ADR, governance docs | Structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| `governance_05` | Claims against code | `uv run python tools/check_docs_consistency.py --domain overview` | Pass |
| ADR files | Deviation and Needs Confirmation inventories | `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` | Pass |

Validation quality baseline: `N/A: no Python target` (documentation and configuration only).

## Risks
- **Risk**: Registering `eventbus.network-binding` with ADR-006 as primary contradicts the issue's ADR-013 and the maintainer's intent. → **Mitigation**: The choice follows the evidence and is recorded as UNK-01; swapping primary and supplemental is a two-line toml change.
- **Risk**: A new front-matter entry without its model edge (or the reverse) fails CI. → **Mitigation**: Phases 2 and 3 are one release unit and `check_adr_reference.py` runs before the Phase closes.
- **Risk**: A new intentional pair breaks ADR-016's "six pairs" statements or INV-02. → **Mitigation**: Update the count wording in the same phase and run `check_adr_authority.py` and `tests/tools/test_adr_authority.py`.
- **Risk**: ADR-012 invariants added for Decisions #5 to #10 change meaning or become untested Blocking gates. → **Mitigation**: Derive each from existing Decision text and cited tests only; mark Non-Blocking where no automated test exists; `check_adr_preservation.py` output is explained.
- **Risk**: Adding the ADR-013 Implementation column drops or alters a verified claim. → **Mitigation**: Copy the existing test references into the new column and leave every other cell unchanged; the matrix checker verifies cited nodes.
- **Risk**: `governance_05` is corrected from code that another issue then changes. → **Mitigation**: Re-verify at implementation time (UNK-04) and word the statement from the code then.
- **Risk**: Decision-text edits and named reviewer approvals are mistaken for approval. → **Mitigation**: Marked pending records only; no reviewer name or date is written (UNK-05).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirmation pass | Pending | — | — | |
| 2 | Decision targets and ownership (REQ-001, REQ-008) | Pending | — | — | |
| 3 | Edges and front matter (REQ-002, REQ-008) | Pending | — | — | |
| 4 | Section names, finding codes, and format (REQ-003 to REQ-006) | Pending | — | — | |
| 5 | governance_05 and regeneration (REQ-007, REQ-009) | Pending | — | — | |
| 6 | Verification | Pending | — | — | |

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
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-104605
- **Related target files**: `config/adr_authority.toml`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: register `rag.fts-text-selection` and `eventbus.network-binding` | `config/adr_authority.toml` | Step 2 | AC-1 | `check_adr_authority.py`, `tests/tools/test_adr_authority.py` | Confirmed by repository evidence |
| REQ-001 | Same; ADR-005 Decision 8 restates ADR-009 INV-03/INV-07 | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Step 2 | AC-1 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-001 | Same; INV-15 and its test live in ADR-006 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 2 | AC-1 | `check_adr_structure.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes: add the missing edges, front matter, and mutual pairs | `config/adr_authority.toml` | Step 3 | AC-2 | `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-002 | Same; ADR-006 to ADR-008 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 3 | AC-2 | `check_adr_reference.py` | Confirmed by repository evidence |
| REQ-002 | Same; ADR-007 in ADR-012 front matter | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Step 3 | AC-2 | `check_adr_reference.py` | Confirmed by repository evidence |
| REQ-002 | Same; ADR-014 edges (only ADR-003 supported by the model) | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Step 3 | AC-2 | `check_adr_reference.py` | Needs confirmation |
| REQ-002 | Same; ADR-016 in the index `related` | `docs/10_adr/adr_01_index.md` | Step 3 | AC-2 | `generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-002 | Same; the pair-count wording | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Step 3 | AC-2 | `check_adr_authority.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes: align section names and finding-code lists | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Step 4 | AC-3 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Same; the guide lists four codes | `docs/10_adr/adr_00_document-guide.md` | Step 4 | AC-3 | `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: complete ADR-012 | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Step 4 | AC-4 | `check_adr_invariant_matrix.py`, `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: ADR-013 Implementation column | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 4 | AC-5 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes: add rag-pipeline-mcp to ADR-008 components | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Step 4 | AC-6 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes: Agent to RAG edge in the dependency graph | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Step 5 | AC-7 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-008 | Constraints: approvals are maintainer statements; no invented reviewers | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Step 6 | AC-8 | `check_adr_preservation.py` | Explicit in issue |
| REQ-009 | Acceptance Criteria: authority, graph, and front-matter checks pass; guarded sections via the tool | `docs/10_adr/adr_01_index.md` | Step 5 | AC-9 | `generate_adr_authority.py --check` | Explicit in issue |
