## Goal
Author the new normative ADR `docs/10_adr/adr_02_07_016_adr-authority-model.md` recording the ADR authority model: one primary ADR per governed decision target, typed edge taxonomy, and the reference-graph vs authority-graph rules (REQ-001 ADR-016 decision record).

## Scope
- In scope: the ADR-016 file end-to-end (front matter + body).
- Out of scope: the model data itself (row 02), generator/validator code (rows 03–05), index generation (row 06).

## Current shape (facts)
- The ADR set ends at ADR-015; ADR-011 is unassigned and recorded as such (`docs/10_adr/adr_01_index.md` note after the ADR List table). ADR-016 is the next free number.
- ADR file idiom (verified against `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`): YAML front matter (`title`, `area`, `tags`, `related`), then `# ADR-NNN: <Title>`, `## Keywords`, `## Status`, `## Summary`, decision/context/consequences sections.
- `tools/check_adr_structure.py` and `tools/_front_matter_schema.py` enforce the front-matter field contract (`title`, `area`, `tags`, `related`, `status`-bearing conventions).

### Verified 20261030 (adversarial pass)
- Confirmed: ADR-015 is the last row of the ADR List (`adr_01_index.md:58`, Group `07 docs`); the ADR-011-unassigned note is at `:60`. New row's Group value: `07 docs`.
- Corrected: `check_adr_structure.py` `_REQUIRED_HEADINGS` (`:139-158`) fixes the exact body skeleton — Keywords, Status, Summary, Context, Assumptions, Decision, Rationale, Alternatives Considered, Consequences, Invariants, Verification, [conditional: Exceptions / Failure Policy / Data Ownership and Persistence], Implementation Notes, Known Deviations, Review Triggers, Approval, Related ADRs, Implementation References, Completion Checklist. All 17 required headings must be present in this order; "Revisit triggers" is `## Review Triggers`. `## Known Deviations` is a separate ERROR check when missing. Template-residue phrases and `INV-NNN` ids are rejected in the body.
- Confirmed: only `adr_02_*.md` front matter `related` entries pointing at `adr_02_*.md` files are cross-checked as ADR edges by the row 05 extension; `related` entries pointing at governance docs or `adr_01_index.md` are plain document links, not model edges.
- Sequencing note: DANGLING_ADR enforcement (row 04) makes the model's ADR-016 edges require this file to exist; the batch work order therefore lands this file right after row 02 (see row 02's Verified note), not literally last. The final docs-checker gate (which this file's Method relies on) runs once after all rows land, so citing tool/model names early is harmless.

## Assumptions
- Owner decision 2026-10-29 fixes the home as a new ADR in `docs/10_adr`; group `02_07` (docs governance group) matches `adr_02_07_015_...`.
- Status is `Accepted` on landing: the owner decision predates authoring; the body records the decision date 2026-10-29.
- ADR-016 is index-only governance: it must not restate any decision content owned by other ADRs; it names the model file and the two new tools.

## Design decisions
- Body decisions recorded verbatim from the Plan's Implementation Intent and Design sections: (1) one primary ADR per governed decision target, supplemental ADRs carry explicit authority limits; (2) edge types `Requires`, `Governs`, `Specializes`, `Extends`, `Exception-to` (normative) plus `Reference` (informational); (3) the authority graph (non-`Reference` edges) must be acyclic and is CI-enforced; the reference graph may contain cycles and the six intentional circular pairs are flagged `intentional`; (4) ADR bodies remain the normative source; `config/adr_authority.toml` is an index of ownership, never decision content; (5) generated index sections are maintained only via `tools/generate_adr_authority.py` (`--check` in CI) and validated by `tools/check_adr_authority.py`.
- Section skeleton follows `check_adr_structure.py`'s required heading list (see Verified note): Keywords, Status, Summary, Context, Assumptions, Decision (numbered decision clauses mirroring REQ-001), Rationale, Alternatives Considered, Consequences, Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval, Related ADRs, Implementation References, Completion Checklist — all required headings, exact order.
- Front matter `related` lists `adr_01_index.md`, `adr_02_07_015_docs-reference-document-class-disposition.md`, and the governance docs row 08 edits; every `related` entry pointing at an `adr_02_*.md` file must also exist in the model as a `Reference` edge (row 05 enforces this — the `016 → 015` edge is authored together with row 02). Non-ADR `related` entries are plain links, not model edges.

## Alternatives considered
- Folding the decision into `adr_01_index.md` prose — rejected: the index is generated/maintained content, not a decision record; REQ-001 requires a normative ADR home (owner decision).
- Superseding an existing ADR — rejected: no existing ADR claims index-authority; ADR-016 adds a new decision target, not a revision.

## Implementation
### Target file
- `docs/10_adr/adr_02_07_016_adr-authority-model.md` (new)

### Procedure
1. Create the file with front matter (`title: "ADR-016: ADR Authority Model"`, `area: governance`, tags `adr`/`governance`, `related` per Design).
2. Write Status `Accepted`, decision date 2026-10-29, source plan `plans/20261029-214650_adrauth001_adr-authority-model.md`.
3. Write Context: hand-maintained graph drift risk, prose-based precedence, registry cannot answer primary-authority questions (mirrors the Plan Problem).
4. Write Decision: the five clauses from Design decisions, naming `config/adr_authority.toml`, `tools/generate_adr_authority.py`, `tools/check_adr_authority.py`, and the marker discipline.
5. Write Consequences + Review Triggers (new ADR must register in the model; contested target ⇒ owner question; assumption changes require model update review) and the remaining required sections (Invariants: the one-primary-per-target and acyclic-authority-graph rules; Verification: the two new tools; Known Deviations: none; Approval: owner decision 2026-10-29; Related ADRs: ADR-015; Implementation References: the model file and the two tools; Completion Checklist).

### Method
Land last in the plan's `seq` order (rows 02–06 first): the ADR cites tool and model names that must exist by then. Use ADR-015 as the structural template; pass `tools/check_adr_structure.py` and the docs checkers in `routing.md`.

### Details
- ADR-016 does not list the authority matrix rows in its body; it states the rule and points to the model file. Keeping matrix data out of the body prevents a second editable copy.

## Compatibility considerations
- `tools/check_adr_invariant_matrix.py` and the invariant verification matrix are untouched: ADR-016 defines governance structure, not implementation invariants with test evidence (out-of-scope boundary with adrgate005).
- The ADR List and dependency rows for ADR-016 land via row 06's generated/edited index, not by this file editing the index.

## Security considerations
- None beyond governance integrity; the ADR must not overstate machine enforcement that row 04 does not implement.

## Rollback considerations
- Removing ADR-016 requires removing its model rows and index row in the same revert; otherwise row 04 fails with dangling-ID findings.

## Validation plan
- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_reference.py` pass with the new ADR present.
- `uv run python tools/check_adr_authority.py` reports no findings once the model carries ADR-016's edges.
- Docs checkers from `routing.md` pass.

## Completion criteria
- ADR-016 exists with Accepted status, decision date, and the five decision clauses; checkers pass.

## Out of Scope
- Model content (row 02), tools (rows 03–05), index edits (row 06), guide prose (row 07).

## Execution Status

### Execution Status
| Status | Started | Completed | Notes |
|---|---|---|---|
| Completed | 20261030-193223 | 20261030-193223 | Adversarial verification complete 20261030: skeleton corrected to `check_adr_structure.py` required-heading list; group `07 docs`; lands after row 02 per DANGLING_ADR sequencing. |

### Blocker Log
| Date | Blocker | Impact | Resolution |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Type | Status | Notes |
|---|---|---|---|
| — | — | — | — |

## Traceability
- Plan: `plans/20261029-214650_adrauth001_adr-authority-model.md` — Implementation Target Files row 01, REQ-001.
- Sequence: lands after rows 02–06 of the same plan.