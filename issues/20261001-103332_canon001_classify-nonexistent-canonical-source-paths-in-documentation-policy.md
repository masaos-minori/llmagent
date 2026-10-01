# Classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides

## Priority
High

## Summary
The `## Area Canonical Maps` section of `docs/00_governance/governance_01_documentation-policy.md` lists canonical source paths that do not exist in the repository, each annotated with an inline `(Needs Confirmation — path does not exist in repository, ...)` status that is not registered in the central Needs Confirmation Inventory. Investigate every listed path, classify it with evidence, and update the Canonical Source Registry, the Policy, each area Document Guide, and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` so that they agree with the files that actually exist. The outcome is a Policy with no nonexistent path recorded as a current canonical source, no orphaned inline Needs Confirmation markers, and no hand-maintained canonical map competing with the Registry.

## Background
- `config/documentation_canonical_sources.toml` is declared the system of record for canonical-source ownership (Policy `### Canonical Source Registry` subsection), superseding the hand-maintained Primary/Secondary tables in `## Area Canonical Maps`. `Documentation only`
- The same subsection states that area guides must not maintain an independent hand-edited canonical-source mapping, and defers the migration of each area guide to "M-01-06's scope". No plan or issue for M-01-06 exists in `plans/`, `plans/done/`, or `issues/`; the identifier appears only in `plans/done/20260905-165817_plan.md` as a future dependency. `Explicit in code` (repository search)
- The inline markers cite `plans/done/20260905-185329_plan.md` as the source of the missing-path list. That plan is a historical work record, not a current-specification document.
- The originating work instruction (`memo2.md`) refers to the Policy as `docs/governance_01_documentation-policy.md`; the actual path is `docs/00_governance/governance_01_documentation-policy.md`. `Explicit in code`

## Problem
Repository investigation (2026-10-01) found the following. These are observations, not final classifications.

- Paths listed in `## Area Canonical Maps` that do not exist:
  - `docs/architecture.md` (Overview, Secondary)
  - `docs/deployment_guide.md` (Deployment, Primary)
  - `deploy.sh` (Deployment, Operational) — no file at repository root; `deploy/deploy.sh` exists and is referenced as the deploy script by `docs/90_deployment/deployment_01_deployment.md` and `skills/deploy/SKILL.md`
  - `docs/rag/specification.md`, `docs/mcp/specification.md`, `docs/agent/specification.md`, `docs/eventbus/specification.md`, `docs/shared/specification.md` (each area's Primary) — no `docs/rag/`, `docs/mcp/`, `docs/agent/`, `docs/eventbus/`, `docs/shared/` directories exist; area docs live under `docs/21_rag/`, `docs/22_mcp/`, `docs/23_agent/`, `docs/24_eventbus/`, `docs/40_shared/`, `docs/41_db/`; no file under `docs/` matches `*specification*`, although the Policy defines functional-requirement sources as `docs/{area}_*_specification.md`
  - `docs/00_governance_01_documentation-policy.md` and `docs/00_governance_04_documentation-checks.md` (Governance, marked `Active`) — actual files are `docs/00_governance/governance_01_documentation-policy.md` and `docs/00_governance/governance_04_documentation-checks.md`
  - `docs/governance_02_documentation-metadata.md` and `docs/governance_03_issue-and-uncertainty-management.md` (Governance, marked `Active`) — the files exist only under `docs/00_governance/`
- The `**Status column note:**` paragraph claims Governance entries are `Active` because the files exist, which is inconsistent with the paths written in the table.
- The Policy contains 8 inline `Needs Confirmation — path does not exist in repository` markers, while the Needs Confirmation Inventory `### Active Items` states that no active items remain open.
- The Registry has only two entries (`eventbus.core-behavior`, `eventbus.persistence-schema`). Overview, Deployment, RAG, MCP, Agent, Shared/DB, and Governance have no Registry entry, so the hand-written tables are currently the only canonical mapping for those areas, contradicting the "Registry is the system of record" rule.
- Area Document Guides diverge in how they express canonical sources: `docs/24_eventbus/eventbus_00_document-guide.md` defers to the Registry; `docs/21_rag/rag_00_document-guide.md` keeps its own `Domain | Canonical Source` table; `docs/22_mcp/mcp_00_document-guide.md` and `docs/40_shared/shared_00_document-guide.md` keep their own canonical rules; `docs/01_overview/overview_00_document-guide.md` has no canonical source section.

## Reason for Change
- Documentation/governance mismatch: the canonical source of record for most areas points at nonexistent files, so conflict resolution under the Policy's `## Conflict Resolution Rule` cannot be applied reliably.
- The central Needs Confirmation Inventory understates open uncertainty, violating the rule that unresolved items must be registered centrally.
- AI agents and developers routing through the Policy are directed to paths that do not exist.

## Implementation Intent
- Treat `config/documentation_canonical_sources.toml` as the system of record, but do not assume it is correct; classify every difference with evidence.
- For each path, decide exactly one classification from: `valid`, `renamed-or-moved`, `obsolete-reference`, `missing-canonical-source`, `registry-mismatch`, `needs-confirmation`, `canonical-source-conflict`.
- Determine replacements by checking each candidate document's Purpose, area, canonical-status declaration, and Registry entry. Do not decide by filename similarity, file mtime, or commit date, and do not treat current code behavior as the canonical source for adopted design.
- Apply the per-classification handling from the work instruction:
  - `renamed-or-moved`: update Registry, Policy, Document Guides, and related references to the current path together; do not keep old-to-new migration notes in current specification.
  - `obsolete-reference`: remove from current specification after moving any still-valid requirement, constraint, rationale, or verification rule into the proper canonical document.
  - `missing-canonical-source`: do not nominate a substitute by guesswork; record it as a design/governance gap per the Policy Routing Rules, naming the required source, Decision Target, impact, and the decision needed.
  - `registry-mismatch`: resolve against ADRs, Specifications, and Document Guides; update Registry and referencing docs in the same change, or register Needs Confirmation if not decidable.
  - `needs-confirmation`: register a full Active Item in the Needs Confirmation Inventory (path, what would confirm it, current evidence, impact, decision needed, owning area, Blocking or not).
  - `canonical-source-conflict`: register under Canonical Source Conflict; do not mark resolved until exactly one normative source is fixed and verified.
- Make the hand-written `## Area Canonical Maps` either derived from/explicitly subordinate to the Registry, or remove it; it must not remain an independent source. If full area-guide migration (M-01-06) cannot be completed in this issue, record the remaining areas as a concrete follow-up issue, not a vague TODO.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md` (`## Area Canonical Maps`, `### Canonical Source Registry`)
- `config/documentation_canonical_sources.toml`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1 Known Issues, Part 2 Needs Confirmation Inventory, Part 3 Canonical Source Conflict)
- Area Document Guides: `docs/01_overview/overview_00_document-guide.md`, `docs/21_rag/rag_00_document-guide.md`, `docs/22_mcp/mcp_00_document-guide.md`, `docs/23_agent/agent_00_document-guide.md`, `docs/24_eventbus/eventbus_00_document-guide.md`, `docs/40_shared/shared_00_document-guide.md`, `docs/90_deployment/deployment_00_document-guide.md`, `docs/00_governance/governance_00_document-guide.md`
- Candidate replacement documents to inspect (not pre-decided): `docs/90_deployment/deployment_01_deployment.md`, `deploy/deploy.sh`, `docs/01_overview/*.md`, `docs/23_agent/agent_02_runtime-architecture.md`

## Required Changes
- Investigate each path listed under `## Area Canonical Maps`, at minimum: `docs/architecture.md`, `docs/deployment_guide.md`, `deploy.sh`, `docs/rag/specification.md`, `docs/mcp/specification.md`, `docs/agent/specification.md`, `docs/eventbus/specification.md`, `docs/shared/specification.md`, `docs/00_governance_01_documentation-policy.md`, `docs/00_governance_04_documentation-checks.md`, `docs/00_governance/`, and the two `docs/governance_0[23]_*.md` rows.
- For each path record: existence, alternative candidate (with Purpose/area/canonical-declaration check), whether it was deleted from Git tracking, current references from other docs, Registry entry, and Document Guide canonical statement.
- Assign exactly one classification per path and apply the matching handling described in Implementation Intent.
- Resolve every inline `Needs Confirmation — path does not exist in repository` marker in the Policy: update to the correct path/state, register in the central Inventory, or delete if it is historical-only.
- Remove the references to `plans/done/20260905-185329_plan.md` from current specification text (Current-Specification-Only Policy); keep any still-needed rationale in a canonical location.
- Correct the `**Status column note:**` paragraph so it matches the final table (or remove it together with the table).
- Ensure no area Document Guide keeps an independent canonical-source map that duplicates or conflicts with the Registry; record any area not migrated in this issue as a concrete follow-up issue.
- Ensure no Decision Target ends up with more than one Primary canonical source.
- Produce the investigation result table in the plan/PR using the columns: Original Path, Exists, Registry Entry, Classification, Correct Path or Action, Evidence.

## Constraints
- Do not infer canonical sources from filename similarity, mtime, or commit date.
- Do not treat current code behavior as the canonical source for adopted design.
- Do not delete an Issue or Needs Confirmation entry without verification evidence.
- Do not resolve a design-vs-implementation conflict by editing documentation only.
- Do not keep historical old paths or migration records in current specification.
- `docs/` content must be written in English and follow `skills/DESIGN.md` Shared Vocabulary (no source-code line numbers, no concrete config values, no implementation counts).
- `docs/00_governance/governance_01_documentation-policy.md` already exceeds the `check_docs_structure.py` size limit; the change must not increase its size, and should preferably reduce it.

## Acceptance Criteria
- Every investigated path has exactly one classification and recorded evidence in the result table.
- Every `source_paths` value in `config/documentation_canonical_sources.toml` exists, or the gap is formally registered as Known Issue, Needs Confirmation, or Canonical Source Conflict.
- No nonexistent path is listed as a current canonical source in the Policy or any area Document Guide.
- `grep -n "path does not exist in repository" docs/00_governance/governance_01_documentation-policy.md` returns no matches, or every remaining marker has a matching Active Item in the central Inventory.
- The Needs Confirmation Inventory `### Active Items` reflects every unresolved item produced by this issue.
- The Policy, Registry, and area Document Guides contain no contradicting canonical source for the same Decision Target, and no Decision Target has more than one Primary source.
- `## Area Canonical Maps` is either removed or explicitly derived from/subordinate to the Registry.
- Any area not migrated to the Registry is recorded as a concrete follow-up issue in `issues/`.
- Resolved items have verification evidence recorded.

## Testing Expectations
Documentation-only; no runtime behavior change. Run and record results of:
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_canonical_source_registry.py`
- `uv run python tools/check_canonical_source_conflicts.py`
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_docs_japanese.py`
- A repository search confirming that removed or changed old paths no longer appear as current canonical sources.
Confirm each tool's CLI from the script itself before running; do not run commands that exist only in documentation.

## Documentation Impact
Yes. Update canonical-source ownership (Registry and Policy), area Document Guide canonical-source sections, and the Known Issues / Needs Confirmation / Canonical Source Conflict inventories. Record constraints and design/governance gaps, not implementation detail.

## Out of Scope
- Writing new area Specification documents (`docs/{area}_*_specification.md`); record missing ones as gaps only.
- Fixing the `eventbus.persistence-schema` Registry validation failure (separate issue `canon002`).
- Fixing checker defects in `tools/check_canonical_source_conflicts.py` or `tools/check_needs_confirmation_inventory.py` (separate issues `canon003`, `ncinv001`).
- Correcting wrong governance-document path references outside the Policy's `## Area Canonical Maps` section (separate issue `govpath001`).
- Registering the pre-existing untracked inline Needs Confirmation markers in `docs/23_agent/` and `docs/21_rag/` reported by `check_needs_confirmation_inventory.py`.
- Reducing `governance_01_documentation-policy.md` below the size limit beyond what this change naturally achieves (issue `docsize001`).

## Dependencies
- `canon002` (Registry validation failure): `check_canonical_source_registry.py` currently exits non-zero, so this issue's "Registry check passes" verification depends on it.
- `ncinv001`: the Needs Confirmation checker currently skips governance docs, so it cannot by itself prove that no orphaned marker remains in the Policy; until fixed, verify with a manual grep.
- `canon003`: CANONICAL-006 false positives make the conflict checker output noisy.

## Unresolved Questions
- Whether the per-area `*specification.md` documents were ever intended to exist (missing-canonical-source) or were superseded by the numbered area docs (obsolete-reference) is not decidable from filenames alone; ADRs and Document Guides must be checked.
- Whether `deploy.sh` in the map denotes `deploy/deploy.sh` (path-notation error) or a removed root-level script is unknown.
- Which document, if any, is the intended Overview architecture source replacing `docs/architecture.md` is unknown.
- Owner and scope of M-01-06 (area guide migration) are undefined.

## AI Implementation Instruction
- Do the investigation and classification table first; do not edit docs before every path has a classification and evidence.
- Do not nominate a replacement canonical source by guesswork; when evidence is insufficient, register Needs Confirmation in the central Inventory with all required fields.
- Keep changes limited to the Target Files; do not reformat unrelated sections of the Policy.
- Update Registry and referencing documents in the same change whenever a canonical mapping changes.
- Stop and report if an ADR or Specification contradicts the Registry and the correct definition cannot be determined.
- Run the listed checkers and report actual output; do not claim success for a checker that still fails because of a dependency issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261001-103332
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, config/documentation_canonical_sources.toml, docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/01_overview/overview_00_document-guide.md, docs/21_rag/rag_00_document-guide.md, docs/22_mcp/mcp_00_document-guide.md, docs/23_agent/agent_00_document-guide.md, docs/24_eventbus/eventbus_00_document-guide.md, docs/40_shared/shared_00_document-guide.md, docs/90_deployment/deployment_00_document-guide.md, docs/00_governance/governance_00_document-guide.md
