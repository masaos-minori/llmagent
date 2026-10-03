# Implementation Procedure — Remove leftover authoring instructions from agent_00_document-guide.md

## Goal

Remove two leftover task-instruction bullets ("Do not modify other documents...", "Do not add new content beyond...") (`REQ-001`, `REQ-002`) and reword the third bullet ("Do not change the doc set directory structure.") into a lasting constraint about directory structure changes going through the governance process (`REQ-003`). Result invariant: none of the three original bullets remain verbatim in `docs/23_agent/agent_00_document-guide.md`'s `## Key Constraints` section.

## Scope

Single modification to `docs/23_agent/agent_00_document-guide.md`: edit three bullets in `## Key Constraints` (lines 36-38) — remove two that are leftover task instructions, reword one into a lasting constraint about directory structure changes.

## Assumptions

- The three bullets are leftover instructions from the restructuring task (commit `96c0d6231`), not intended lasting constraints. This is an assumption based on wording and commit context; it needs confirmation.
- The third bullet ("Do not change the doc set directory structure.") can be reworded into a lasting constraint without changing the Agent doc set's actual behavior.
- Only these three bullets are affected; other `## Key Constraints` bullets are left as-is.

## Design decisions

- Delete the two task-instruction bullets entirely (they contradict the guide's role as the entry point that must track chapter changes).
- Reword the third bullet minimally: keep the core intent (directory structure changes require governance approval) while making it a lasting constraint rather than a one-off prohibition.
- Record the decision rationale in the generated document for traceability.

## Alternatives considered

- Retaining all three bullets unchanged: rejected — they prohibit normal maintenance and contradict the guide's own purpose.
- Rewording all three bullets: rejected — the first two are clearly task instructions, not constraints worth preserving.
- Adding a comment explaining the origin of the three bullets: rejected — comments would not prevent AI agents from obeying them.

## Implementation

### Target file

`docs/23_agent/agent_00_document-guide.md`

### Procedure

Edit three bullets in `## Key Constraints` (lines 36-38): remove two, reword one.

### Method

Edit — targeted text replacement and deletion.

### Details

1. Inspect commit `96c0d6231` to confirm the three bullets are leftover instructions (UNK-01 resolution).
   - Run `git show 96c0d6231 -- docs/23_agent/agent_00_document-guide.md` to review the diff.
2. Edit line 36: REMOVE the bullet "Do not modify other documents in the `agent_*.md` set." (`REQ-001`).
   - Before: `- Do not modify other documents in the \`agent_*.md\` set.`
   - After: (line removed entirely)
3. Edit line 37: REMOVE the bullet "Do not add new content beyond what exists in the current document." (`REQ-002`).
   - Before: `- Do not add new content beyond what exists in the current document.`
   - After: (line removed entirely)
4. Edit line 38: REWORD the bullet "Do not change the doc set directory structure." into a lasting constraint (`REQ-003`).
   - Before: `- Do not change the doc set directory structure.`
   - After: `- Changes to the doc set directory structure must go through the governance process.`
5. Verify acceptance criterion: run `grep -n -E "Do not modify other documents|Do not add new content beyond|Do not change the doc set directory" docs/23_agent/agent_00_document-guide.md` and confirm no matches.
6. Run `uv run python tools/check_docs_quality.py` and expect pass (`REQ-001`, `REQ-002`, `REQ-003`).
7. Run `uv run python tools/check_docs_structure.py "docs/23_agent/agent_00_document-guide.md"` and expect pass (`REQ-001`, `REQ-002`, `REQ-003`).

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/23_agent/agent_00_document-guide.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_00_document-guide.md` | Path resolution (acceptance criterion) | `grep -n -E "Do not modify other documents|Do not add new content beyond|Do not change the doc set directory" docs/23_agent/agent_00_document-guide.md` | No matches |
| `docs/23_agent/agent_00_document-guide.md` | Document quality | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/23_agent/agent_00_document-guide.md` | Document structure | `uv run python tools/check_docs_structure.py "docs/23_agent/agent_00_document-guide.md"` | Pass |

## Completion criteria

- Against the current repository, `grep -n -E "Do not modify other documents|Do not add new content beyond|Do not change the doc set directory" docs/23_agent/agent_00_document-guide.md` returns no matches, or each remaining bullet is reworded as a lasting constraint with a recorded justification.
- No other content in `docs/23_agent/agent_00_document-guide.md` changes.

## Out of scope

- Needs Confirmation rule sentence in the same section (tracked separately).
- Japanese text in `### Related ADRs`.
- Edits to other Agent docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Acceptance criterion passed: grep returns no matches for the three original bullets. Structure checker issues are pre-existing. |
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
- **Source issue**: issues/20261001-104506_docleft001_remove-leftover-authoring-instructions-from-agent-document-guide.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-192453_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-095037
- **Related target files**: docs/23_agent/agent_00_document-guide.md