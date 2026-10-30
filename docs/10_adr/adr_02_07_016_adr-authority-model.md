---
title: "ADR-016: ADR Authority Model"
area: governance
tags:
  - documentation
  - governance
  - adr-authority
related:
  - adr_01_index.md
  - adr_02_07_015_docs-reference-document-class-disposition.md
  - governance_04_documentation-checks.md
---

# ADR-016: ADR Authority Model

## Keywords

- adr authority
- decision target
- primary adr
- edge type
- authority graph
- reference graph

## Status

Accepted

## Summary

ADR precedence across the ADR set is today prose-based: the ADR index lists dependencies and six intentional circular pairs, but nothing machine-checkable states which ADR is primary for a governed decision target. This ADR adopts a machine-readable authority model: `config/adr_authority.toml` records exactly one primary ADR per governed decision target (with explicitly limited supplemental ADRs), typed dependency edges, and a shared architecture-assumption registry. The informational ADR reference graph keeps allowing the six intentional cycles; the authority graph (typed edges only) must be acyclic. Index graph sections become generated artifacts under the ADR-015 generated-content discipline. ADR bodies remain the normative decisions; the model is an index of who owns what and never a second source of decision content.

## Context

### Problem

Plans and checkers increasingly depend on ADR-governed contracts (DB migration workflow under ADR-008, RAG fallback under ADR-010, reference generation under ADR-015). With precedence recorded only as prose in `docs/10_adr/adr_01_index.md`:

- a second ADR claiming primacy over a target is invisible until two documents contradict each other;
- the dependency graph and intentional-cycle list are hand-maintained and can drift from ADR front matter `related` lists;
- architecture assumptions (single host, loopback-only, local SQLite, single Agent process) recur across ADR Context sections with no registry, so an assumption change has no detection path.

### Constraints

- ADR bodies remain normative; the model must not restate or re-decide their content (it is index-only).
- Invariant evidence stays in the ADR Invariant Verification Matrix (`tools/check_adr_invariant_matrix.py`); canonical source paths stay in `config/documentation_canonical_sources.toml`. Neither registry is merged into the model.
- The reference graph today contains six bidirectional pairs that are documented as intentional ownership splits, so a blanket "no cycles" rule cannot apply to it.

## Assumptions

- No governed decision target is contested at adoption; the model transcribes the current prose authorities as-is. A validator finding of a duplicate primary is escalated to the repository owner, not silently resolved.
- The model file lives in `config/` (separate from `documentation_canonical_sources.toml`), consistent with the existing TOML registry idiom; this placement is owner-revisable.
- Model ownership is the repository owner, consistent with the governance rows in `docs/10_adr/adr_01_index.md`.

## Decision

### Decision Details

1. **Primary authority**: every governed decision target (recorded in `config/adr_authority.toml` `[[authority]]` entries) has exactly one `primary_adr`. A second primary claim for the same target is a `DUP_PRIMARY` finding and fails CI.
2. **Supplemental limits**: an ADR with partial authority over a target appears as a supplemental entry carrying an explicit `limit` stating what it does and does not decide. Supplemental entries never outrank the primary.
3. **Closed edge taxonomy**: dependency edges are typed in the closed set `Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to`, `Reference`. `Reference` is the informational edge reproducing today's `A → B` meaning; the other five are normative edges.
4. **Graph split**: the reference graph (all edges) may contain bidirectional pairs only when the `Reference` direction carries `intentional = true` and an ownership-split `note`. The authority graph (non-`Reference` edges only) must be acyclic; a cycle there is an `AUTHORITY_CYCLE` finding and fails CI. In each intentional bidirectional pair, exactly one direction carries a non-`Reference` type.
5. **Assumption registry**: shared architecture assumptions are registered as `[[assumption]]` entries (ID `ARCH-NNN`, name, current value, applicable ADRs, validation method `config-check` or `manual-review`, owner, review triggers). A `config-check` assumption whose recorded value no longer matches live configuration is an `ASSUMPTION_DRIFT` finding and fails CI.
6. **Generated index sections**: the ADR index Reference Graph, Authority Graph, and Intentional Circular References sections are generated artifacts produced only by `tools/generate_adr_authority.py` between guard comments, following the ADR-015 INV-01 discipline; hand edits inside the guards are prohibited and drift is detected by `--check` (exit 1).
7. **Front matter/model consistency**: every ADR front matter `related` entry naming another ADR file must exist in the model as an edge; every non-`Reference` model edge must appear in the owning ADR's front matter. A model-only `Reference` edge is permitted (the model is the superset the generated graph renders). Divergence in either direction is a `FRONTMATTER_DIVERGENCE` finding detected by `tools/check_adr_reference.py`.
8. **Registration duty**: adding an ADR, changing its front matter `related`, or changing a governed target's authority requires a matching `config/adr_authority.toml` change in the same change set; dangling ADR IDs are a `DANGLING_ADR` finding and fail CI.

### Scope

Applies to the governance relationship between ADRs, the ADR index graph sections, and the assumption registry. It records who owns which decision target.

### Out of Scope

The decision content of each ADR body; invariant evidence (ADR Invariant Verification Matrix); canonical source-path claims (`config/documentation_canonical_sources.toml`); the software area dependency graph (`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`), whose cycle prohibition stays limited to area nodes.

## Rationale

### 1. Ownership clarity — Maintainability

One primary per target makes "which ADR wins" a lookup instead of a prose interpretation, which matters as more automated contracts register under specific ADRs.

### 2. Precedence becomes machine-checked — Correctness

Duplicate primaries, authority cycles, dangling IDs, front-matter divergence, and config-check assumption drift each get a finding code that fails CI at the commit that introduces the conflict, rather than a later documentation bug hunt.

### 3. Reuses working repository idioms — Consistency

TOML registry (like `documentation_canonical_sources.toml`), guarded generated blocks with `--check` (like `generate_reference_table.py` and ADR-015), and underscore shared cores (like `_front_matter_schema.py`) already exist; no parallel mechanism is invented.

## Alternatives Considered

### Alternative A: Extend `config/documentation_canonical_sources.toml` with ADR fields

- **Reason for Rejection:** that registry maps targets to canonical source paths; folding ADR authority into it would mix two claim types (where content lives vs who decides) in one file.

### Alternative B: Front matter `related` lists as the only machine-readable graph

- **Reason for Rejection:** front matter carries no room for edge types, supplemental limits, or the assumption registry, and cross-ADR validation logic would have to live in several tools instead of one shared core.

### Alternative C: Keep the hand-maintained index and rely on review

- **Reason for Rejection:** prose precedence has held so far, but nothing prevents a stale primary or an accidental authority cycle, and the batch of concurrent plans amending ADRs makes silent divergence the expected failure mode.

## Consequences

### Positive Consequences

- A conflicting ADR claim fails CI when it lands (`DUP_PRIMARY`, `AUTHORITY_CYCLE`), not after documents contradict each other.
- The index graph sections and the intentional-cycle list stop drifting from ADR front matter (`FRONTMATTER_DIVERGENCE`, generated sections).
- Shared architecture assumptions gain one authoritative value, an applicable-ADR list, and a drift-detection path.

### Negative Consequences

- Every ADR addition or `related` change now requires a paired `config/adr_authority.toml` edit in the same change set.
- The generated index sections cannot be hand-edited; changes flow through the model file.
- Two additional tools and one config file join the CI gate surface.

## Invariants

- INV-01: Every governed decision target in the model has exactly one `primary_adr`; supplemental entries carry a `limit`.
- INV-02: The authority graph (non-`Reference` edges) contains no cycle; each bidirectional reference pair is exactly one typed edge plus one `intentional = true` `Reference` edge with a `note`.
- INV-03: The ADR index graph sections between guard comments are produced only by `tools/generate_adr_authority.py` — they are never hand-edited.
- INV-04: ADR front matter `related` ADR edges and model `adr_edge` rows are consistent in both directions defined in Decision 7.
- INV-05: Every registered assumption is validated per its `validation_method`; a `config-check` value that no longer matches live configuration fails CI.

## Verification

- **Test**: `uv run python tools/check_adr_authority.py` validates the model against INV-01, INV-02, and INV-05 (finding codes `DUP_PRIMARY`, `DANGLING_ADR`, `AUTHORITY_CYCLE`, `ASSUMPTION_DRIFT`, `EDGE_UNKNOWN_TYPE`) and runs in the CI `lint` job. — **Verifies**: INV-01, INV-02, INV-05 — **Type**: Static Check — **Blocking**: Yes
- **Test**: `uv run python tools/generate_adr_authority.py --check` regenerates the guarded graph sections in memory and exits 1 when a section is missing or differs from the generator output, so a hand edit or an unregenerated model change is detected. It runs in the CI `lint` job. — **Verifies**: INV-03 — **Type**: Static Check — **Blocking**: Yes
- **Test**: `uv run python tools/check_adr_reference.py` cross-checks ADR front matter `related` edges against the model (`FRONTMATTER_DIVERGENCE`) and runs as the `adr-reference-scoped` pre-commit hook. — **Verifies**: INV-04 — **Type**: Static Check — **Blocking**: Yes

## Implementation Notes

- Model file: `config/adr_authority.toml` (authority matrix, typed edges, assumption registry; `version = "1"`).
- Shared validator core: `tools/_adr_authority_core.py`, imported by `tools/check_adr_authority.py` (standalone CI validator) and `tools/check_adr_reference.py` (front matter cross-check).
- Generator: `tools/generate_adr_authority.py` writes three guarded sections into `docs/10_adr/adr_01_index.md`: Reference Graph (`adr-reference-graph`), Authority Graph (`adr-authority-graph`), Intentional Circular References (`adr-intentional-cycles`).
- The `governance_05` area-graph cycle prohibition remains limited to area nodes; the acyclicity rule of INV-02 is this ADR's own rule over the ADR authority graph.

## Known Deviations

Not applicable

## Review Triggers

- A new ADR is added, or an ADR's front matter `related` list changes.
- A governed decision target is contested (two ADRs claiming primary authority) — escalate to the repository owner.
- A registered assumption changes (deployment topology, transport exposure, storage technology, Agent process count).
- A new edge type is proposed, or the closed taxonomy in Decision 3 is otherwise to be extended.

## Approval

### Required Reviewers
- Documentation Governance Owner

### Approval Record

- **Approved By**: repository owner
- **Approval Date**: 2026-10-29
- **Approval Reference**: Reviewed and approved by the repository owner; the model design was reviewed during the issue-to-plan phase and the owner decision of 2026-10-29 (model home: a new ADR in `docs/10_adr`) was recorded before implementation began.
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text; individual reviewer names are not recorded.

This ADR reached `Accepted` via a Task-level approval decision per the ADR Acceptance Evidence Standard (`docs/00_governance/governance_01_documentation-policy.md`).

## Related ADRs

- ADR-015: this ADR extends the generated-content discipline (ADR-015 INV-01) to the ADR index graph sections.

## Implementation References

- `config/adr_authority.toml` — authority matrix, typed edges, assumption registry
- `tools/_adr_authority_core.py` — shared loader and validators (finding codes)
- `tools/check_adr_authority.py` — standalone model validator (CI `lint` job)
- `tools/generate_adr_authority.py` — generated index sections, `--check` drift gate
- `tools/check_adr_reference.py` — front matter/model cross-check

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated (Not applicable — this ADR records governance metadata only and does not affect code or runtime)
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated (Not applicable — same as above)
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Discrepancies with the current implementation are registered as Known Issues (none applicable; see Known Deviations)
- [x] The Owner and required Reviewers are defined (see Approval Record)
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
