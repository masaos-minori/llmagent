# Implementation Procedure: docs/05_agent_04_*_state-and-persistence*.md

## Goal

Reduce `docs/05_agent_04_*_state-and-persistence*.md` documents to canonical sources for state/persistence boundaries by removing full field lists and CRUD/DB-operation enumerations.

## Scope

**In-Scope**:
- Restructure all four files in `docs/05_agent_04_*_state-and-persistence*.md` to preserve: session-scope / turn-scope / persistent-scope distinction, relationship between `ctx.conv.history` and `session.sqlite`, why `session_diagnostics` is separated from `messages`, why `workflow.sqlite` is the source of truth for workflow state, RAG-DB vs. memory-DB responsibility boundary, `/undo` caveats after compression, policy against crossing DB boundaries with direct operations.
- Remove: full field lists for `AgentContext`/`ConversationState`/`TurnState`/`RuntimeStats`, CRUD method lists, DB operation function lists, mechanical table-column enumerations, mechanical save/fetch/update descriptions.
- Replace duplicative content with pointers to `05_agent_09_data-layer`.
- Rephrase operational concepts as judgments (why), not just mechanical descriptions.
- Reformat using the template: Purpose / Design Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known Limitations / Related Docs.
- Mark unrecoverable design rationales as `Needs Confirmation`.

**Out-of-Scope**:
- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.

## Assumptions

1. The `memo-doc-agent-review.md` referenced in acceptance criteria existed during the original review but may have been moved or deleted since then.
2. `tools/check_agent_docs_consistency.py` is available and functional for post-edit verification (includes DB-schema-drift check vs. `schema_sql.py`).
3. All mechanical content being removed is indeed duplicatable via code search (no unique facts will be lost).
4. The four target files form a coherent logical unit (state model part1/part2 + history compression + platform databases).

## Design decisions

- State/persistence should answer "what does each component own" and "how do scopes interact," not "which field appears where."
- Full field lists and CRUD enumerations are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated schema diagram: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_04_01_state-and-persistence-state-model-part1.md`
- `docs/05_agent_04_01_state-and-persistence-state-model-part2.md`
- `docs/05_agent_04_02_state-and-persistence-history-compression.md`
- `docs/05_agent_04_03_state-and-persistence-platform-databases.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Read all four files in `docs/05_agent_04_*_state-and-persistence*.md` in full.
3. Verify the four files form a coherent logical unit (state model part1/part2 + history compression + platform databases).
4. Confirm `05_agent_09_data-layer` exists for cross-references.
5. Identify sections containing:
   - Full field lists for `AgentContext`/`ConversationState`/`TurnState`/`RuntimeStats`
   - CRUD method lists
   - DB operation function lists
   - Mechanical table-column enumerations
   - Mechanical save/fetch/update descriptions

#### Phase 2: Core Logic Implementation

6. For each identified mechanical section across all four files:
   - If the content includes full field lists for `AgentContext`/`ConversationState`/`TurnState`/`RuntimeStats`: replace with high-level scope descriptions (session/turn/persistent).
   - If the content is a CRUD method list: remove entirely; this is mechanical mapping visible in code.
   - If the content is a DB operation function list: remove unless it carries operational meaning.
   - If the content is a mechanical table-column enumeration: replace with a pointer to `05_agent_09_data-layer`.
   - If the content is a mechanical save/fetch/update description: replace with a description of the persistence lifecycle's purpose.
7. Preserve the following content across all four files:
   - Session-scope / turn-scope / persistent-scope distinction (operational judgment)
   - Relationship between `ctx.conv.history` and `session.sqlite` (design intent)
   - Why `session_diagnostics` is separated from `messages` (operational judgment)
   - Why `workflow.sqlite` is the source of truth for workflow state (operational judgment)
   - RAG-DB vs. memory-DB responsibility boundary (design intent)
   - `/undo` caveats after compression (operational caution)
   - Policy against crossing DB boundaries with direct operations (key constraint)
8. Replace duplicative content with pointers to `05_agent_09_data-layer` where appropriate.
9. Rephrase operational concepts as judgments: instead of listing step-by-step actions, explain why the concept exists (e.g., "/undo after compression can only restore to the last checkpoint").
10. Explicitly state DB-boundary-crossing prohibition and `/undo`-after-compression caveat as operational rules.
11. Mark any unrecoverable design rationale as `Needs Confirmation`.
12. Reformat remaining content in all four files using the standard template:
    ```
    ## Purpose
    ## Design Intent
    ## Responsibility Boundary
    ## Key Constraints
    ## Operational Notes
    ## Known Limitations
    ## Related Docs
    ```

#### Phase 3: Deployment & Verification

13. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links, removed-file references, or DB-schema drift.
14. Manually verify that all four documents still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process all four files together since they form a single logical unit.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure cross-references between Part 1 and Part 2 remain valid after restructuring.
- Ensure consistency across all four files in terms of terminology and scope division.
- Cross-reference `05_agent_09_data-layer` for DB-related content to avoid duplication.

## Compatibility considerations

N/A — documentation-only change. No API or behavior compatibility concerns.

## Security considerations

N/A — documentation-only change. No security implications.

## Rollback considerations

Rollback is straightforward: restore the original files from git history if the restructuring introduces errors or loses critical information.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Consistency check | `python tools/check_agent_docs_consistency.py` | 0 broken links, 0 removed-file references, 0 DB-schema drift |
| Template compliance | Manual review against `memo-doc-agent-review.md` §修正後の章構成テンプレート | Structure matches template |
| Mechanical content removal | Manual review | No full dataclass field list or CRUD/DB-function enumeration remains |
| Operational rule preservation | Manual review | DB-boundary-crossing prohibition and `/undo`-after-compression caveat stated explicitly |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the state/persistence flow from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-095302_require.md
- Source plan: plans/20260807-102817_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-113802
- Related target files: docs/05_agent_04_01_state-and-persistence-state-model-part1.md, docs/05_agent_04_01_state-and-persistence-state-model-part2.md, docs/05_agent_04_02_state-and-persistence-history-compression.md, docs/05_agent_04_03_state-and-persistence-platform-databases.md
