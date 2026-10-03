# Implementation Procedure — Replace NC rule-statements in agent_00_document-guide.md

## Goal

Replace two rule-restating mentions of "Needs Confirmation" in `agent_00_document-guide.md` (`REQ-001`) with pointers to the canonical governance document, phrased WITHOUT the literal "Needs Confirmation" phrase so no new untracked-marker warning is introduced. Result invariant: zero inline "needs confirmation" markers and no false statements about such flags in `docs/23_agent/` (`REQ-003`).

## Scope

Single modification to `docs/23_agent/agent_00_document-guide.md`: replace two inline "Needs confirmation" mentions — the scope bullet enumerating "...Known Issues / Deprecated Items / Needs Confirmation entries" and Key Constraints stating unrecoverable rationales "must be explicitly marked `Needs Confirmation`". Replace each with a pointer to `governance_03_issue-and-uncertainty-management.md`, without the literal trigger phrase.

## Assumptions

- The replacement references `governance_03_issue-and-uncertainty-management.md` by name, never by the phrase "Needs Confirmation", avoiding self-created warnings from the marker regex.
- No file under `docs/23_agent/` carries a "needs confirmation" marker beyond the six found (confirmed by `grep`).

## Design decisions

- Pointer by title/filename, not by concept. Naming the doc by its title ("Issue and Uncertainty Management") / filename conveys the pointer while avoiding a self-created warning.
- Only the six identified markers are touched. The pre-existing repeated Key Constraints / Known Limitations blocks in `agent_13_reference-api.md` are left intact; deduplicating them is unrelated work excluded per the project's no-unrelated-refactoring policy.

## Alternatives considered

- Replacing with a prose description of the NC-handling process: rejected because it would itself contain the trigger phrase or risk duplicating the canonical source.
- Adding an NC inventory item for these Agent-doc markers: rejected — none is a genuine unresolved item (they restate how NC handling works or assert a non-existent mechanism).

## Implementation

### Target file

`docs/23_agent/agent_00_document-guide.md`

### Procedure

Replace two inline "Needs confirmation" mentions with pointers to the canonical governance document.

### Method

Edit — targeted text replacement.

### Details

1. Baseline: run `grep -rin "needs confirmation" docs/23_agent/` and confirm the current 6-match count across the two target files before editing.
2. Edit line 29 (Responsibility Boundary): replace the scope-bullet clause "...Known Issues / Deprecated Items / Needs Confirmation entries." with a clause that keeps Known Issues / Deprecated Items here and routes uncertainty items to `governance_03_issue-and-uncertainty-management.md`, removing the literal "Needs Confirmation" phrase.
   - Before: `Chapter structure overview, question-to-chapter navigation mapping, Canonical Source Rule definition, handling of Known Issues / Deprecated Items / Needs Confirmation entries.`
   - After: `Chapter structure overview, question-to-chapter navigation mapping, Canonical Source Rule definition, handling of Known Issues / Deprecated Items here; uncertainty items tracked per [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).`
3. Edit line 35 (Key Constraints): replace the bullet "...must be explicitly marked `Needs Confirmation` rather than silently dropped." with a bullet stating unrecoverable design rationales must not be silently dropped and their disposition follows `governance_03_issue-and-uncertainty-management.md`.
   - Before: `Unrecoverable design rationales must be explicitly marked \`Needs Confirmation\` rather than silently dropped.`
   - After: `Unrecoverable design rationales must not be silently dropped; their disposition follows [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).`
4. Run `uv run python tools/check_needs_confirmation_inventory.py` and confirm zero warnings reference either edited file.
5. Run `grep -rin "needs confirmation" docs/23_agent/` and confirm zero matches.
6. Run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py docs/23_agent/*.md` and confirm clean.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/23_agent/agent_00_document-guide.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_00_document-guide.md` | Marker-inventory sync (primary acceptance) | `uv run python tools/check_needs_confirmation_inventory.py` | Zero warnings reference this file |
| `docs/23_agent/agent_00_document-guide.md` | Phrase absence (defense-in-depth) | `grep -rin "needs confirmation" docs/23_agent/` | Zero matches |
| `docs/23_agent/agent_00_document-guide.md` | Structural/formatting conformance | `uv run python tools/check_docs_quality.py` | Pass (no new violations) |
| `docs/23_agent/agent_00_document-guide.md` | Internal structure / front matter / links | `uv run python tools/check_docs_structure.py docs/23_agent/*.md` | Pass |

## Completion criteria

- `AC-1`: After the edit, `uv run python tools/check_needs_confirmation_inventory.py` reports zero warnings referencing this file.
- `AC-2`: This file contains no case-insensitive phrase "needs confirmation" anywhere.
- `AC-4`: Each replaced rule-statement bullet names `governance_03_issue-and-uncertainty-management.md` and preserves the original intent (incomplete/incomplete-impl changes and unrecoverable design rationales are tracked canonically rather than silently dropped).
- `AC-5`: `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py docs/23_agent/*.md` pass on this file.

## Out of scope

- Any change to `docs/00_governance/governance_03_issue-and-uncertainty-management.md` or its NC inventory.
- Deduplication of the pre-existing repeated Key Constraints / Known Limitations blocks in `agent_13_reference-api.md`.
- The three non-Agent untracked markers reported by the checker (`00_index.md:25`, `ADR-004-environment-failure-handling-policy.md:631`, `rag_05_5-constraints-reference.md:30`).
- Any code/config/schema change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation updates needed beyond this procedure |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261001-104142_ncagent001_resolve-agent-docs-needs-confirmation-rule-statements-and-stale-flag-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-163108_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-094321
- **Related target files**: docs/23_agent/agent_00_document-guide.md
