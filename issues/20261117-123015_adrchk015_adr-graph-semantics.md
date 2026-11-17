# Define ADR graph semantics and fix the authority model and its checkers

## Priority
Medium

## Summary
The ADR dependency graph, the authority model, and their checkers use undefined terms; the data has gaps and reversed edges, and the checkers miss whole classes of errors.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M03`; merged from ADRCHK-M07, M08, M09, M26, M27, M28, L08 (review findings M5, M6, M21, M22, N14, N15, N16, N18, N24)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- The graph definition does not match the model: the Index defines an edge as listed in Related ADRs and referenced in the body, while ADR-016 and `tools/_adr_authority_core.py` accept reference-only edges, and references in the body is undefined.
- Related ADRs are incomplete: ADR-007 omits ADR-017, ADR-010 has no node, ADR-004 and ADR-005 mention other ADRs without listing them, and the Index front matter omits ADR-017.
- Edge types are undefined, and the decision owner direction is reversed between two pairs with the same structure.
- Decision targets are missing: Config Isolation is not registered, `agent.tool-approval` omits ADR-001, and ADR-002 and ADR-016 own no decision target.
- The checkers have gaps: `tools/check_adr_reference.py` labels a check with another checker's rule ID, an early return skips the front matter check, the assumption check verifies only part of what ARCH-002 covers, duplicate edges overwrite each other, and ADR status is never checked.
- Header rules point at each other, so no readable header list exists, and a section reference points at the wrong section number.
- ADR-016 hard-codes a count of cyclic pairs.

## Implementation Intent
- Governance and ADR-016 define reference and each edge type, including which endpoint owns the decision.
- The authority data follows these definitions, and the checkers report every violation, including duplicates, non-loopback hosts, and unknown statuses.
- The header list has one readable source, and section references use anchors instead of numbers.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md`
- `docs/10_adr/adr_02_07_016_adr-authority-model.md`
- ADR-004, ADR-005, ADR-007, and ADR-010 (Related ADRs sections)
- `config/adr_authority.toml`
- `tools/_adr_authority_core.py`
- `tools/check_adr_reference.py`
- `tools/check_adr_structure.py`
- `docs/00_governance/governance_01_documentation-policy.md`
- `docs/00_governance/governance_04_documentation-checks.md`
- `tests/tools/`

## Required Changes
- (no decision needed) Fix `check_adr_reference.py`: use the correct rule ID, run the front matter check independently, and update the docstring.
- (no decision needed) Extend `_adr_authority_core.py`: check the EventBus host and each server's bind host, report duplicate edges, and validate the status set.
- (no decision needed) Fix the Related ADRs lists and the Index `related` list; replace the hard-coded count in ADR-016 with a reference to the generated list.
- (no decision needed) Choose one source for the header list; if it is the checker, generate a readable list into governance_01 inside a guard block, and fix the section reference.
- (decision) Define reference and the edge types in ADR-016.
- (decision) Fix the reversed pair, add the missing targets, and regenerate the guarded block with `tools/generate_adr_authority.py`.

## Constraints
- Changing an edge or a target is an authority model change and needs an approval record.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- Fixtures for a non-loopback EventBus host, a duplicate edge, and an unknown status each fail.
- GV-004 and the model cross-check report no mismatch.
- `uv run python tools/check_adr_authority.py` passes, and each ADR owns or contributes to a target, or is documented as standalone.

## Testing Expectations
Fixture tests under `tests/tools/`; `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/generate_adr_authority.py --check`; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-016, the Index, Related ADRs sections, governance_01 and governance_04.

## Out of Scope
- Decision substance of any ADR other than graph and authority semantics.

## Dependencies
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the status set used by the new status check (depends on).

## Unresolved Questions
- `tools/check_adr_authority.py` and `tools/generate_adr_authority.py` were not reviewed.

## AI Implementation Instruction
- Changing an edge or a target needs an approval record; prepare a proposal and stop.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123015
- **Related target files**: `docs/10_adr/adr_01_index.md`; `docs/10_adr/adr_02_07_016_adr-authority-model.md`; ADR-004, ADR-005, ADR-007, and ADR-010 (Related ADRs sections); `config/adr_authority.toml`; `tools/_adr_authority_core.py`; `tools/check_adr_reference.py`; `tools/check_adr_structure.py`; `docs/00_governance/governance_01_documentation-policy.md`; `docs/00_governance/governance_04_documentation-checks.md`; `tests/tools/`
