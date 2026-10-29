# Create a machine-readable ADR authority, dependency, and architecture-assumption model

## Priority
Medium

## Summary
Record, in one machine-readable model, which ADR is the single primary authority for each decision target, which relationship edges are normative versus informational, and which shared architecture assumptions apply to which ADRs, then generate the ADR dependency diagram and index sections from that model and check it in CI.

## Background
Source: `memo-issue.md` item H-05 (original tasks H-06, L-02, and L-05), re-verified against current source on 2026-10-29. The memo rates it High; the priority here is Medium for the reason under Reason for Change.
- The ADR dependency graph is a hand-maintained text block: `docs/10_adr/adr_01_index.md` (section "ADR Dependency Graph", lines 62-80) lists `A → B` edges meaning "A lists B under Related ADRs and refers to it in its body", and a separate prose list of six intentional circular references (lines 82-95); the index has no auto-generated block (`rg -c AUTO-GENERATED` returns 0) (`Explicit in code`/docs).
- The only edge meaning is "related and referenced"; there is no edge type that says which ADR is normative for a decision target. Authority is stated in prose, for example "ADR-003 remains the authority for RuntimeToolRegistry, Tool ownership, and Routing" (`adr_01_index.md:90`).
- A registry with a "decision target" and "claim type" concept already exists for documentation sources: `config/documentation_canonical_sources.toml` with `tools/check_canonical_source_registry.py` (entries such as `eventbus.persistence-schema.bootstrap-ddl`). It records canonical source paths per decision target, not primary ADRs.
- A cycle checker exists only for the software runtime area graph (`tools/check_dependency_graph_cycles.py`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`); the index states that rule does not apply to the ADR reference graph (`adr_01_index.md:95-97`).
- Shared single-host, loopback, local-SQLite, and single-Agent assumptions are stated in several ADRs: a search for those terms in `docs/10_adr/` matches 7 files (`Explicit in code`/docs; the search counts files, not distinct statements). ADR numbering has a gap: ADR-011 is unassigned (`adr_01_index.md:60`).
- ADR invariant evidence checking is covered separately and partly done: `issues/done/20261027-155848_adrgate005_enforce-adr-evidence-checks.md`.

## Problem
Implementers infer ADR precedence from prose; the diagram, the index, and the actual precedence rules can drift because the diagram is hand-edited; and a shared assumption that changes (for example single-host) has no list of affected ADRs. The existing docs registry cannot answer "which ADR is the primary authority for target X".

## Reason for Change
Priority is Medium (maintainability and unclear ownership), not the memo's High: no incorrect behavior or data loss is tied to the current prose-based precedence, and the ADR set is currently consistent (the index documents its circular references). The gap becomes costly as more ADR-governed contracts are added by the other issues in this batch. It is not time-sensitive.

## Implementation Intent
Create one authoritative model (format and home to be chosen with the owner) holding: a decision-target authority matrix with exactly one primary ADR per target plus supplemental ADRs and the limits of their authority; typed relationship edges (`Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`); and an architecture-assumption registry with ID, current value, applicable ADRs, validation method, owner, and review triggers. Generate the dependency diagram and the relevant index sections from the model, with separate reference and authority graphs (cycles allowed only in the informational reference graph). Extend the existing registry tooling rather than adding a parallel mechanism, and keep ADR bodies as the normative text.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md` and ADR front matter under `docs/10_adr/`
- `config/documentation_canonical_sources.toml`, `tools/check_canonical_source_registry.py`
- `tools/check_adr_structure.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`
- A new model file, its schema, a generator script, and an assumption validator (locations to be decided)

## Required Changes
- Create the decision-target authority matrix covering workflow control, component responsibility, routing, LLM visibility, dynamic health, approval, transport, MCP technical safety, EventBus persistence, EventBus authorization, DB recovery, RAG canonical data, fallback, and reference generation, with exactly one primary ADR per target.
- Record supplemental ADRs and the limits of their authority.
- Create the architecture-assumption registry and define the relationship edge types.
- Generate separate reference and authority graphs, the ADR dependency diagram, and the relevant ADR index sections.
- Add CI checks for multiple primary authorities, dangling ADR IDs, invalid authority cycles, and unacknowledged assumption changes.

## Constraints
- ADR bodies remain the normative decisions; the model must not become a second source of truth for decision content.
- Do not weaken any Accepted ADR invariant; do not change unrelated ADR decisions without a separate approval record.
- Generated blocks must carry the existing generated-content markers and cannot be hand-edited (ADR-015 pattern).
- Keep the intentional circular references representable (informational graph only).

## Acceptance Criteria
- Every governed decision target resolves to exactly one primary ADR; conflicting normative ownership fails CI.
- Every shared assumption has one authoritative definition and an impact list; a configuration that violates an enforceable assumption is rejected or explicitly blocked for review.
- The ADR index and dependency diagram are reproducible from the model.
- Adding or changing an ADR cannot leave dangling or inconsistent relationships.

## Testing Expectations
- Unit tests for the model validator (duplicate primaries, dangling IDs, authority cycles, assumption drift) and for the generator (reproducibility).
- CI integration: `uv run python tools/check_canonical_source_registry.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/generate_reference_table.py --check` or its successor, plus the docs checkers in `routing.md` for docs edits.

## Documentation Impact
Yes. The ADR index and the ADR document guide must describe the authority model, the edge types, and how generated sections are maintained; document intent and boundaries, not tool internals (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Re-deciding which ADR is authoritative for any target (the matrix records current decisions; contested targets become owner questions).
- Rewriting ADR bodies beyond front matter and generated sections.
- ADR invariant evidence checks (`adrgate005`, done) and manifest generation (`issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`).

## Dependencies
- Blocks `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md` (the authority and assumption manifests it generates) and informs `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md` (authority ADR for the mandatoriness registry).
- Related, archived: `issues/done/20261027-155848_adrgate005_enforce-adr-evidence-checks.md`; re-verify this issue against it.

## Unresolved Questions
- `Needs confirmation`: the home and format of the model (a TOML or JSON file under `config/`, or ADR front matter) and who owns it.
- `Needs confirmation`: whether to extend `config/documentation_canonical_sources.toml` or create a separate ADR-authority file.
- `Needs confirmation`: the exact count and wording of repeated architecture assumptions across ADRs (the search above counts files only).
- `Needs confirmation`: whether any decision target currently has two ADRs claiming primary authority (not found by this review, which read only the index).

## AI Implementation Instruction
- Read `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_01_index.md`, and the canonical-source registry tooling before editing.
- Do not change any ADR decision text; limit ADR edits to front matter and generated sections.
- Stop and report instead of choosing when an authority is contested or the model's home is undecided.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104504
- **Related target files**: `docs/10_adr/adr_01_index.md`, `config/documentation_canonical_sources.toml`, `tools/check_canonical_source_registry.py`, `tools/check_adr_structure.py`, `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`
