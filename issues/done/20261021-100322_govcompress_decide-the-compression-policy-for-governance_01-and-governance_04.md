# Decide the compression policy for governance_01 and governance_04

## Priority
Low

## Summary
Decide whether and how to compress machine-derivable content in `docs/00_governance/governance_01_documentation-policy.md` and `docs/00_governance/governance_04_documentation-checks.md`, which are also governance gate contracts, and record which parts must stay.

## Background
Both documents are about 23 KB (22533 B and 23555 B). The docs cleanup applied the "design intent over transcription" prompt to all of `docs/` but left these two without a compression decision. They contain machine-derivable text, such as per-check "Scanned directories" lists, tool behavior descriptions, and the ADR section header standardization section. They are also the gate contract: the `governance_04` Verification Matrix (GV-001 to GV-023) is to be kept. `docs/10_adr/adr_01_index.md` is an invariant map and dependency graph that is itself an automated check target, so it has little room for compression and is out of scope here.

## Problem
It is unknown which parts of the two documents are gate contract and which are derivable from tools and config. Compressing without that boundary risks dropping a gate rule; not compressing leaves duplicated, drift-prone content.

## Reason for Change
Duplicated tool behavior and scanned-directory lists can drift from the tools and config that already define them, while the governance contract text must not be weakened.

## Implementation Intent
First classify content, then decide. For each section of the two documents, apply the prompt's judgment order: currently valid, design value, mechanically re-derivable, change-time value, canonical source. Sections that define gate, blocking status, timing, or rule meaning stay. Sections that restate tool behavior or scanned directories are candidates for replacement with a source reference. Output is a decision list; edits follow only for sections the owner approves.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`
- `docs/00_governance/governance_04_documentation-checks.md`

## Required Changes
- Produce a per-section Keep / Compress / Reference / Needs Confirmation list for both documents, with the reason for each.
- Obtain the owner's approval of the list.
- Apply approved edits only; keep the Verification Matrix (GV-001 to GV-023) and all gate semantics.
- Replace derivable content with a reference to the canonical source (tool or config), and avoid creating a second normative source.

## Constraints
- Accepted ADR Decisions and gate semantics must not change.
- The registry claim-type and authority rules in `governance_01` are normative; do not compress them without owner approval.
- No history wording; current specification only.

## Acceptance Criteria
- A reviewed per-section decision list exists and is approved by the owner.
- Approved edits are applied without changing any gate, blocking status, or timing.
- No dangling link, anchor, or rule ID remains.
- `check_canonical_source_registry.py` and the docs checkers pass.

## Testing Expectations
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_canonical_source_registry.py`, `check_adr_preservation.py`.
- `uv run python tools/check_docs_consistency.py --domain overview`.
- Manual review that every gate rule in the matrix still has its rule text and gate.

## Documentation Impact
Yes. Both governance documents. Information kept or moved: gate contract, canonical source rules, tool-versus-document ownership of derivable detail.

## Out of Scope
- `docs/10_adr/adr_01_index.md`.
- Changing or adding verification rules.
- Editing any tool or config.
- Follow-up work decisions and GV-016 wiring (separate issues).

## Dependencies
N/A: none (sibling-issue check: no open issue overlaps). Other issues in the same batch edit `governance_04`; do this one after them or coordinate to avoid conflicting edits.

## Unresolved Questions
- Is compression of these two documents wanted at all, given they are also the gate contract?
- Which sections does the owner consider normative and therefore fixed?

## AI Implementation Instruction
Do not edit before the owner approves the decision list. Produce the list first and stop. Do not change gate semantics, rule IDs, or the matrix. Use references to canonical sources instead of copying content.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-100322
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_04_documentation-checks.md`
