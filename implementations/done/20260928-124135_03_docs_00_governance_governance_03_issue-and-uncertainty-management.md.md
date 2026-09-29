## Goal

Remove the resolved CI-014 entry from Known Issues Part 1 and update the CI batching note in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (`REQ-001` acceptance criterion).

## Scope

Two edits in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: delete the `#### CI-014` subsection and correct the batching note. No other section changes.

## Assumptions

- Row 1's test is implemented and passing before this doc edit is marked complete (dependency on Row 1).
- CI-014 currently occupies `docs/00_governance/governance_03_issue-and-uncertainty-management.md:173-191`, between `#### CI-012` and `#### CI-016`.
- The batching note sits at line 213 and lists CI-014 among the five remaining members.
- No other entry's `**Related**:` field references CI-014 (verified: CI-014 appears only in its own subsection and the batching note).

## Design decisions

- Delete the entire `#### CI-014` subsection (heading through its trailing blank line) rather than marking it "resolved" inline — it belongs in Known Issues Part 1, which is for open issues.
- Update the batching note minimally: drop CI-014 from the member list and Area enumeration, change "five" → "four", and add CI-014 to the historical removed-members parenthetical while keeping the original "nine members" count.

## Alternatives considered

- Leaving CI-014 in place with status flipped to "closed": rejected — Part 1 is for open known issues; resolved items are removed, per the plan.
- Rewriting the whole batching note: rejected — only the counts and member references change.

## Implementation
### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Delete the `#### CI-014` subsection at lines 173-191, joining `#### CI-012`'s block directly to `#### CI-016` (line 193).
2. Edit the batching note at line 213 as below.

### Method

Two in-place text edits; verify heading hierarchy (`#### CI-xxx`) and paragraph structure remain intact afterward.

### Details

- **Edit 1 — remove subsection**: delete from `#### CI-014` (line 173) through the blank line before `#### CI-016` (line 193), inclusive.
- **Edit 2 — batching note** (current line 213):
  - Member list: `CI-009, CI-010, CI-012, CI-014, CI-016` → `CI-009, CI-010, CI-012, CI-016`.
  - Count: `These five` → `These four`.
  - Removed-members parenthetical: `CI-008, CI-011, CI-013, and CI-015 were removed` → `CI-008, CI-011, CI-013, CI-014, and CI-015 were removed` (keep "originally nine members").
  - Area enumeration: `Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), RAG (CI-014), and Agent (CI-016)` → `Shared/DB (CI-009), MCP (CI-010), EventBus (CI-012), and Agent (CI-016)`.
  - Leave the final sentence about cross-cutting-role vs. per-area ownership unchanged.

## Compatibility considerations

Documentation-only. Ensure the referenced test (Row 1) actually landed before finalizing, so the note's implication that coverage exists is true.

## Security considerations

N/A.

## Rollback considerations

Re-add the CI-014 subsection and restore the original batching note wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual verification | Read file content | `#### CI-014` subsection gone; batching note lists four members and no longer mentions CI-014 |

## Completion criteria

- The `#### CI-014` subsection no longer exists.
- The batching note reflects four remaining members with no residual CI-014 reference.
- Heading hierarchy and surrounding entries are intact.

## Out of scope

Any other CI entry; Part 2 Needs Confirmation Inventory; cross-cutting ownership-model changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260929-230703 | 20260929-230703 | Applied two in-place edits per Procedure: removed #### CI-014 subsection (actual lines 113-133, not 173-191); rewrote batching note to reflect zero remaining members (user-confirmed rewrite). |
| 2 | Add or update tests per Validation plan | Completed | 20260929-230703 | 20260929-230703 | N/A: documentation-only; validation plan uses manual verification. CI-014 test confirmed present and passing from a prior cycle. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260929-230703 | 20260929-230703 | Doc-only validation: check_docs_quality/structure/content_policy passed for governance_03. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260929-230703 | 20260929-230703 | Primary deliverable; see Step 1 notes. |

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
- **Requirement ID**: `REQ-001` (CI-014 removed from Known Issues Part 1; batching note updated)
- **Source issue**: `issues/20260927-211346_ci014_add-unit-test-for-adr-009-normalized_content-llm-output-prohibition.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260928-093959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-124135
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`