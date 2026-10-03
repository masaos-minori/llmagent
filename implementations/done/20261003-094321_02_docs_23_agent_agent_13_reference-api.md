# Implementation Procedure — Replace NC rule-statements and remove stale flag claims in agent_13_reference-api.md

## Goal

Replace two rule-restating mentions of "Needs Confirmation" in `agent_13_reference-api.md` (`REQ-001`) with pointers to the canonical governance document, phrased WITHOUT the literal "Needs Confirmation" phrase so no new untracked-marker warning is introduced. Correct two stale factual claims about a non-existent "Needs Confirmation flags" mechanism (`REQ-002`). Result invariant: zero inline "needs confirmation" markers and no false statements about such flags in `docs/23_agent/` (`REQ-003`).

## Scope

Single modification to `docs/23_agent/agent_13_reference-api.md`: replace two rule-restating mentions in Key Constraints (Part 1 and Part 2) with pointers to `governance_03_issue-and-uncertainty-management.md`, and remove two false claims in Known Limitations (Part 1 and Part 2) that assert legacy-vs-code differences are "explicitly marked with Needs Confirmation flags".

## Assumptions

- The replacement references `governance_03_issue-and-uncertainty-management.md` by name, never by the phrase "Needs Confirmation", avoiding self-created warnings from the marker regex.
- No file under `docs/23_agent/` carries a "needs confirmation" marker beyond the six found (confirmed by `grep`).
- The two removed false-claim bullets carry no unique factual content beyond the false claim; their sibling bullet about indirect callees is retained, so each Known Limitations section keeps at least one substantive entry.

## Design decisions

- Pointer by title/filename, not by concept. Naming the doc by its title ("Issue and Uncertainty Management") / filename conveys the pointer while avoiding a self-created warning.
- Removal, not correction-with-equivalent-statement, for the false claims. The two Known Limitations bullets assert a flag mechanism that does not exist anywhere in `docs/23_agent/`. There is no true statement to substitute, so deletion is the correct action.
- Only the six identified markers are touched. The pre-existing repeated Key Constraints / Known Limitations blocks in `agent_13_reference-api.md` are left intact; deduplicating them is unrelated work excluded per the project's no-unrelated-refactoring policy.

## Alternatives considered

- Replacing with a prose description of the NC-handling process: rejected because it would itself contain the trigger phrase or risk duplicating the canonical source.
- Replacing false claims with an accurate cross-reference (e.g., "discrepancies are resolved via issue tracking"): optional enhancement; removal satisfies the issue and leaves no false statement.
- Adding an NC inventory item for these Agent-doc markers: rejected — none is a genuine unresolved item (they restate how NC handling works or assert a non-existent mechanism).

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api.md`

### Procedure

Replace two rule-restating mentions and remove two false claims across Part 1 and Part 2 sections.

### Method

Edit — targeted text replacement and deletion.

### Details

1. Baseline: run `grep -rin "needs confirmation" docs/23_agent/` and confirm the current 6-match count across the two target files before editing.
2. Edit line 39 (Key Constraints, Part 1): replace "...must be explicitly marked with a `Needs Confirmation` flag." with "...tracked per `governance_03_issue-and-uncertainty-management.md`".
   - Before: `Incomplete implementation changes must be explicitly marked with a \`Needs Confirmation\` flag.`
   - After: `Incomplete implementation changes must be tracked per [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).`
3. Edit line 50 (Known Limitations, Part 1): REMOVE the bullet asserting "...are explicitly marked with `Needs Confirmation` flags."
   - Before: `- Differences between legacy documentation and current code are explicitly marked with \`Needs Confirmation\` flags.`
   - After: (line removed entirely; sibling bullet about indirect callees remains)
4. Edit line 159 (Key Constraints, Part 2): replace "...must be explicitly marked with a `Needs Confirmation` flag." with "...tracked per `governance_03_issue-and-uncertainty-management.md`".
   - Before: `Incomplete implementation changes must be explicitly marked with a \`Needs Confirmation\` flag.`
   - After: `Incomplete implementation changes must be tracked per [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).`
5. Edit line 170 (Known Limitations, Part 2): REMOVE the bullet asserting "...are explicitly marked with `Needs Confirmation` flags."
   - Before: `- Differences between legacy documentation and current code are explicitly marked with \`Needs Confirmation\` flags.`
   - After: (line removed entirely; sibling bullet about indirect dependencies remains)
6. Run `uv run python tools/check_needs_confirmation_inventory.py` and confirm zero warnings reference either edited file.
7. Run `grep -rin "needs confirmation" docs/23_agent/` and confirm zero matches.
8. Run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py docs/23_agent/*.md` and confirm clean.

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/23_agent/agent_13_reference-api.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_13_reference-api.md` | Marker-inventory sync (primary acceptance) | `uv run python tools/check_needs_confirmation_inventory.py` | Zero warnings reference this file |
| `docs/23_agent/agent_13_reference-api.md` | Phrase absence (defense-in-depth) | `grep -rin "needs confirmation" docs/23_agent/` | Zero matches |
| `docs/23_agent/agent_13_reference-api.md` | No false flag claims remain | Manual review of diff | No sentence asserts "marked with Needs Confirmation flags" |
| `docs/23_agent/agent_13_reference-api.md` | Structural/formatting conformance | `uv run python tools/check_docs_quality.py` | Pass (no new violations) |
| `docs/23_agent/agent_13_reference-api.md` | Internal structure / front matter / links | `uv run python tools/check_docs_structure.py docs/23_agent/*.md` | Pass |

## Completion criteria

- `AC-1`: After the edit, `uv run python tools/check_needs_confirmation_inventory.py` reports zero warnings referencing this file.
- `AC-2`: This file contains no case-insensitive phrase "needs confirmation" anywhere.
- `AC-3`: No sentence in this file asserts that legacy-vs-code differences are "marked with Needs Confirmation flags" or any equivalent non-existent mechanism.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Validators passed: grep zero matches in docs/23_agent/, marker checker zero warnings referencing edited files, no false flag claims remain |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261001-104142_ncagent001_resolve-agent-docs-needs-confirmation-rule-statements-and-stale-flag-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-163108_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-094321
- **Related target files**: docs/23_agent/agent_13_reference-api.md