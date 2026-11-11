# Complete the ADR authority model, reference edges, and ADR format

## Priority
Medium

## Summary
Register the decision targets that two ADRs both define, add the missing Related-ADR and dependency-graph edges, number every Decision list explicitly, finish ADR-012, fix format gaps in ADR-008, ADR-012, and ADR-013, and make the front-matter divergence check run in CI.

## Background
- Source: `memo-issue.md` items L-03 and L-05, re-checked against current source on 2026-11-09. Many items below were not re-read in this review and remain `Needs confirmation`.
- `Explicit in config`: `config/adr_authority.toml` contains no `fts` or `network` decision target (search found none), consistent with the memo's claim that the FTS text selection rule (ADR-005 INV-03 and ADR-009 INV-07) and the EventBus network binding (ADR-006 INV-10/15 and ADR-013) are unregistered duplicates.
- `Explicit in documentation`: the ADR index names its graph section "ADR Dependency Graph", while ADR-016 calls the generated sections "Reference Graph", "Authority Graph", and "Intentional Circular References" (section names differ; the memo's claim is confirmed).
- `Explicit in code`: `tools/check_adr_authority.py` states that the front matter/model cross-check (`FRONTMATTER_DIVERGENCE`) is not run there; `tools/check_adr_reference.py` runs it through the `adr-reference-scoped` pre-commit hook. No `.github/` workflow references the check (search found none), so it does not run in CI (`Needs confirmation` of the CI definition in `.github/workflows/ci.yml`).
- `Explicit in documentation`: ADR-012 and ADR-013 each have a "Security Reviewer" entry (ADR-012 line "Security Reviewer", ADR-013 line "Security Reviewer"); whether it names a person is `Needs confirmation`. ADR-012's invariants INV-01 to INV-04 cover only some Decision Details (the memo says only Decision #1 to #4; `Needs confirmation`).
- `Needs confirmation`: all other memo claims in this item (missing Related-ADR edges ADR-006 to 008, ADR-010 to 008, ADR-014 to 002/003/004, ADR-007 in ADR-012 front matter, ADR-016 in the index `related`; missing Agent to RAG and mcp_dedup dependency-graph edges; rag-pipeline-mcp missing from ADR-008 components; implicit Decision numbering; copied template assumptions; ADR-012 definitions of the dry-run exception, the "documented safe exception", and Stages 1 to 3; ambiguous Completion Checklist states; the ADR-013 test table Implementation column; the long ADR-008 Status cell; differing finding-code lists in the Guide and ADR-016).
- ADR-010 is withdrawn by the RAG delegation removal issue in this batch, so ADR-010 edges are handled there; avoid editing them twice.
- Verification result (2026-11-11, confirmation pass against current source):
  - `Confirmed by repository evidence`: `rag.fts-text-selection` is unregistered; ADR-005 Decision 8 (and an Implementation Note) restates the rule that ADR-009 INV-03 and INV-07 own. The section names differ: the generator writes `## ADR Dependency Graph`, `### Authority Graph`, and `### Intentional Circular References`, while ADR-016 calls the first "Reference Graph". ADR-016 lines 130 and 132 and `check_adr_authority.py` list `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE` (plus `FRONTMATTER_DIVERGENCE` in `check_adr_reference.py`), while `adr_00_document-guide.md` line 71 lists only four codes.
  - Refuted (CI): `.github/workflows/ci.yml` runs `uv run pre-commit run --all-files` in the same `lint` job, and the `adr-reference-scoped` hook (`tools.check_adr_reference`, `pass_filenames: false`) is part of it, so `FRONTMATTER_DIVERGENCE` already runs in CI; `ci.yml` and `.pre-commit-config.yaml` need no change.
  - Refuted (ARCH registry location): the ARCH-NNN registry is the `[[assumption]]` list (ARCH-001 to ARCH-003) in `config/adr_authority.toml`, defined by ADR-016 INV-05 and checked by `ASSUMPTION_DRIFT`; there is no separate `architecture_assumptions` file.
  - Refuted (numbering): the Decision Details of ADR-001, 002, 003, 004, 005, 006, 007, 008, 009, 012, 013, 014, and 016 are already numbered lists; only ADR-015's Decision is prose with no list. Whether any numeric cross-reference is stale is not shown and is left to the plan's confirmation phase. Also refuted: "static tokens" does not appear in ADR-013 Out of Scope (the only match is in Alternatives Considered).
  - Partly refuted (network binding): the loopback-binding decision and test are in ADR-006 (Decision 12 and INV-15); ADR-013 only cites loopback binding as an implemented first layer and a non-goal. A decision target `eventbus.network-binding` should therefore have ADR-006, not ADR-013, as primary (maintainer to confirm).
  - `Confirmed by repository evidence` (edges and front matter): ADR-006 has no edge to ADR-008 (the model has only ADR-008 to ADR-006) although its body cites ADR-008; ADR-014's front matter and body relate only to ADR-001 (the memo's 002/003/004 edges are not supported by its body; ADR-003 is the supplemental entry of `agent.component-responsibility`); ADR-012's front matter lists no ADR while the model has the ADR-012 to ADR-007 edge; the ADR index `related` list omits ADR-016. `governance_05` says `scripts/agent/` has no import of `scripts/rag/`, but `scripts/agent/services/rag_maintenance_service.py` imports `rag.corpus_identity` (that file is missing from the issue's target list; `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` may remove the import, so re-verify at implementation). No `mcp_dedup` entry exists in `governance_05`, but the mcp_dedup ownership plan owns that decision, so it is not repeated here. ADR-008's "Target components" line omits rag-pipeline-mcp while its recovery table names it.
  - `Confirmed by repository evidence` (ADR-012/013 format): ADR-012 has invariants INV-01 to INV-04 for Decision Details #1 to #4 only (its Verification table already cites tests for #5 to #10 by name, without test file paths); "a documented safe exception" in Decision #5 and Stages 1 to 3 (defined only in the `write_protection_pipeline.py` docstring: repo path validation, write guard, authorization) are not defined in the ADR; the memo's "dry-run exception" does not appear in ADR-012. ADR-013's Automated Tests table has no Implementation column. Both ADRs' Approval Records are task-level decisions without reviewer names (`Security Reviewer` listed as a required role), so named approvals need the maintainer.
  - Not repeated here: the long ADR-008 Status cell in the index is amendment history that the history-wording issue removes.

## Problem
- A decision defined in two ADRs without a registered primary owner will diverge on the next edit (ADR-016 requires one owner).
- Missing edges mean change-impact analysis (`governance_05`) does not notify affected ADRs and components.
- Implicit Decision numbering breaks references as soon as an item is inserted; copied template assumptions state false facts.
- Required Security Reviewer approvals may be missing for security-relevant ADRs (`Needs confirmation`).

## Reason for Change
- Without these fixes, impact analysis and authority checks run on an incomplete model. Timing: follows the index and matrix issue in this batch, so numbering and mapping fixes are not made twice.

## Implementation Intent
- Every decision has exactly one primary owner, every real dependency is an edge, and every ADR uses a format the checkers can validate. Fix the models and the ADR bodies together; the generated index sections are regenerated, not hand-edited.

## Target Files or Areas
- `config/adr_authority.toml`, `config/architecture_assumptions` registry (`Unknown`: exact file; the ARCH-NNN registry named in the memo)
- ADR-002, 005, 006, 007, 008, 009, 010, 012, 013, 014, 016 under `docs/10_adr/`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`
- `tools/check_adr_reference.py`, `tools/check_adr_authority.py`, `tools/generate_adr_authority.py` (run; modify only the CI wiring in `.github/workflows/ci.yml` and `.pre-commit-config.yaml` when required)
- `.github/workflows/ci.yml`

## Required Changes
- Register `rag.fts-text-selection` (primary ADR-009) and `eventbus.network-binding` (primary ADR-013), and change the other ADRs to references.
- Add the missing Related-ADR edges and front matter and register any new mutual pairs; align the edge definition and section names between the index and ADR-016; add ADR-016 to the index `related`.
- Add the Agent to RAG edge and the mcp_dedup database to the dependency graph, and add rag-pipeline-mcp to the ADR-008 components.
- Number every Decision list explicitly and fix all numeric references.
- Move the shared assumptions into the ARCH-NNN registry and fix the copies that contradict ADR-008.
- Complete ADR-012 (definitions, Stages 1 to 3, invariants for every decision, test file paths).
- Make Completion Checklist states explicit; add the Implementation column to the ADR-013 test table; remove static tokens from ADR-013 Out of Scope; shorten the ADR-008 Status cell.
- Add named Security Reviewer approvals to ADR-012 and ADR-013 (maintainer-supplied), and add `FRONTMATTER_DIVERGENCE` to CI, aligning the finding-code lists.

## Constraints
- ADR amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals or reviewer names.
- Run `tools/check_adr_preservation.py` for every wording change, and justify each reported decision change.
- Docs content policy applies; the generated index sections are written only by `generate_adr_authority.py`.
- Do not change checker semantics except wiring an existing check into CI.

## Acceptance Criteria
- The authority, graph, and front-matter checks pass in CI (`check_adr_authority.py`, `check_adr_reference.py`, `generate_adr_authority.py --check`).
- Every Decision reference resolves to a numbered item.
- No ADR restates a decision owned by another ADR (the two registered targets reference their primaries).
- `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `check_docs_structure.py` pass.

## Testing Expectations
- Documentation and configuration only, plus a CI wiring change; run the ADR checkers above and `uv run python tools/check_docs_consistency.py --domain overview`. Verify the CI step locally with the same command it runs.

## Documentation Impact
- ADR-002, 005, 006, 007, 008, 009, 012, 013, 014, 016, the ADR index, and the document guide change: ownership, edges, numbering, invariants, and approvals.

## Out of Scope
- Index matrix and invariant-to-test mapping fixes (index and matrix issue in this batch).
- ADR-010 changes (RAG delegation removal issue).
- New ADR content for MCP authentication (MCP security issue).

## Dependencies
- Depends on: `issues/20261109-113220_adrrev015_adr-index-matrix.md`.
- Related: `issues/20261109-113054_adrrev012_adr-approval-ledger.md` and `issues/20261109-112608_adrrev003_rag-http-delegation.md`.

## Unresolved Questions
- Confirmation pass done for the items above; still `Needs confirmation`: stale numeric Decision cross-references, copied template assumptions that contradict ADR-008 (the registry already holds ARCH-001 to ARCH-003), ambiguous Completion Checklist states, and whether ADR-014 relies on ADR-002/004 (its body mentions only ADR-001).
- Maintainer input: Security Reviewer names and approvals for ADR-012 and ADR-013 (`不明`); the primary ADR for `eventbus.network-binding` (ADR-006 by evidence).
- Resolved: the ARCH-NNN registry lives in `config/adr_authority.toml` `[[assumption]]`.

## AI Implementation Instruction
- Run a confirmation pass first and drop any item the current ADRs already satisfy.
- Do not invent reviewer names, approvals, or dates.
- Regenerate index sections with the tool; do not hand edit guarded sections.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113248
- **Related target files**: `config/adr_authority.toml`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `.github/workflows/ci.yml`
