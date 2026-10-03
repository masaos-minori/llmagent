# Implementation Procedure — Consolidate duplicated Part 1 / Part 2 meta sections in agent_13_reference-api.md

## Goal

Merge the two duplicate sets of meta sections in `docs/23_agent/agent_13_reference-api.md` into one, update the H1 and front matter `title` to drop "Part 1"/"Part 2", and remove the mid-file "Part 2" heading. Keep all per-module API sections from both parts intact (`REQ-001`, `REQ-002`). Result invariant: zero duplicate meta-section blocks remain; inbound links to `agent_13_reference-api.md` resolve correctly (`REQ-003`).

## Scope

Single modification to `docs/23_agent/agent_13_reference-api.md`: merge the two duplicate meta-section sets (Keywords, Related Documents, Purpose, Design Intent, Responsibility Boundary) into one block, update the H1 from "Agent Reference API — Part 1" to "Agent Reference API", update the front matter `title` field accordingly, and remove the mid-file "## Part 2" heading while keeping its per-module API sections.

## Assumptions

- The two meta-section sets differ only by minor wording differences (e.g., "Function signatures, parameter types, return values, error conditions." vs. "Method signatures, parameter types, return values, error conditions.") — these can be reconciled without loss of information.
- The mid-file "## Part 2" heading is purely structural and carries no semantic meaning beyond separating the two original parts.
- Inbound links to `agent_13_reference-api.md` from other docs use the filename without "#Part 1" or "#Part 2" anchors, so removing those headings does not break links.

## Design decisions

- Merge the two meta-section sets by taking the more complete version of each section (e.g., keep "Function signatures" over "Method signatures" where they overlap).
- Update the H1 and front matter `title` to reflect the consolidated file name.
- Remove the mid-file "## Part 2" heading but preserve all per-module API sections under it.

## Alternatives considered

- Retaining both meta-section sets: rejected — duplication violates the principle of single source of truth.
- Keeping the "Part 1"/"Part 2" naming: rejected — the consolidation task explicitly requires dropping these labels.
- Restructuring the entire file: out of scope per the Plan.

## Implementation

### Target file

`docs/23_agent/agent_13_reference-api.md`

### Procedure

Merge duplicate meta sections, update H1/title, remove "Part 2" heading.

### Method

Edit — targeted text replacement and deletion.

### Details

1. Baseline: confirm current state of the file — two meta-section sets at the top and a "## Part 2" heading around line 140.
2. Edit the H1: replace "Agent Reference API — Part 1" with "Agent Reference API".
   - Before: `# Agent Reference API — Part 1`
   - After: `# Agent Reference API`
3. Edit the front matter `title` field: replace `"Agent Reference API — Part 1"` with `"Agent Reference API"`.
4. Merge the two duplicate meta-section sets (Keywords, Related Documents, Purpose, Design Intent, Responsibility Boundary):
   - Take the more complete version of each section from the first set.
   - Where the second set adds unique content (e.g., additional related documents), incorporate it.
   - Delete the second copy of these meta sections.
5. Remove the mid-file "## Part 2" heading (keep the per-module API sections under it).
   - Before: `## Part 2`
   - After: (heading removed; per-module API sections become direct children of the main H1)
6. Run `uv run python tools/check_docs_structure.py "docs/23_agent/agent_13_reference-api.md"` and expect pass (`REQ-001`, `REQ-002`).
7. Verify no broken inbound links: search for references to `agent_13_reference-api.md` in other docs and confirm they still resolve correctly.
8. Run `uv run python tools/check_docs_quality.py` and expect pass (`REQ-001`, `REQ-002`).

## Compatibility considerations

None — documentation-only edit with no behavioral effect. However, any external link using `agent_13_reference-api.md#Part%201` or `agent_13_reference-api.md#Part%202` as an anchor will need updating.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/23_agent/agent_13_reference-api.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_13_reference-api.md` | Structural conformance | `uv run python tools/check_docs_structure.py "docs/23_agent/agent_13_reference-api.md"` | Pass |
| `docs/23_agent/agent_13_reference-api.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass (no new violations) |
| `docs/23_agent/agent_13_reference-api.md` | Duplicate-meta absence (acceptance criterion) | Manual review of diff | Only one set of Keywords/Related/Purpose/Design Intent/Responsibility Boundary remains |
| Other docs referencing `agent_13_reference-api.md` | Inbound link integrity | Manual review of grep results | No broken anchors (#Part 1/#Part 2) |

## Completion criteria

- Against the current repository, after the edit, `grep -n "## Part 2" docs/23_agent/agent_13_reference-api.md` returns no matches.
- No duplicate meta-section blocks remain in `docs/23_agent/agent_13_reference-api.md`.
- The H1 reads "Agent Reference API" (without "— Part 1").
- No new `[ERROR]`/`[WARNING]` findings introduced by the edits.

## Out of scope

- Fixing Needs Confirmation sentences themselves (issue `ncagent001`).
- Changes to `docs/23_agent/agent_14_reference-api-generated.md`.
- Editing per-module API content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Acceptance criterion passed: no ## Part 2 headings remain. Duplicate meta-sections merged. H1/title updated. |
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
- **Source issue**: issues/20261001-104507_agentref001_consolidate-duplicated-part-1-part-2-meta-sections-in-agent-reference-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-193213_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-100911
- **Related target files**: docs/23_agent/agent_13_reference-api.md