# Implementation Procedure: docs/05_agent_03_*_turn-processing-flow*.md

## Goal

Reduce `docs/05_agent_03_*_turn-processing-flow*.md` documents to canonical sources for turn-processing design intent by removing sequential call-detail and dataclass field dumps.

## Scope

**In-Scope**:
- Restructure all four files in `docs/05_agent_03_*_turn-processing-flow*.md` to preserve: conceptual model of a single turn, why WorkflowEngine is mandatory, meaning of plan/execute/verify, operational notes for approval-wait/background-failure/pause states, ToolLoopGuard's role and design intent, reason partial completions are separated from conversation history.
- Preserve correlation ID, approval-wait, partial completion, workflow state as intent (not field lists) — explain their operational/audit meaning.
- Remove: sequential function-call walkthroughs, private method names, dataclass field lists, guard public-method enumerations, verbatim constant-string quotes, mechanical state-transition tables (e.g., `current_turn_id`).
- Rephrase operational concepts as judgments (why), not just mechanical descriptions.
- Reformat using the template: Purpose / Design Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known Limitations / Related Docs.
- Mark unrecoverable design rationales as `Needs Confirmation`.

**Out-of-Scope**:
- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.

## Assumptions

1. The `memo-doc-agent-review.md` referenced in acceptance criteria existed during the original review but may have been moved or deleted since then.
2. `tools/check_agent_docs_consistency.py` is available and functional for post-edit verification.
3. All mechanical content being removed is indeed duplicatable via code search (no unique facts will be lost).
4. The four target files form a coherent logical unit (overview + LLM/tool loop + WorkflowEngine part1/part2).

## Design decisions

- Turn processing should answer "what does a turn do" and "how do components coordinate," not "which private method name appears where."
- Sequential function-call walkthroughs are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated sequence diagram: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_03_01_turn-processing-flow-overview.md`
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`
- `docs/05_agent_03_03_turn-processing-flow-workflow-engine-part2.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Read all four files in `docs/05_agent_03_*_turn-processing-flow*.md` in full.
3. Verify the four files form a coherent logical unit (overview + LLM/tool loop + WorkflowEngine part1/part2).
4. Identify sections containing:
   - Sequential function-call walkthroughs (step-by-step invocation chains within a turn)
   - Private method names
   - Dataclass field lists
   - Guard public-method enumerations
   - Verbatim constant-string quotes
   - Mechanical state-transition tables (e.g., `current_turn_id`)

#### Phase 2: Core Logic Implementation

5. For each identified mechanical section across all four files:
   - If the content is a sequential function-call walkthrough: replace with a high-level description of the turn lifecycle (plan → execute → verify).
   - If the content includes private method names: remove entirely; this is mechanical mapping visible in code.
   - If the content is a dataclass field list: replace with component-level responsibility descriptions.
   - If the content is a guard public-method enumeration: remove unless it carries operational meaning.
   - If the content includes verbatim constant-string quotes: remove unless the string itself carries operational meaning.
   - If the content is a mechanical state-transition table: replace with a description of the state machine's purpose and key transitions.
6. Preserve the following content across all four files:
   - Conceptual model of a single turn (high-level flow)
   - Why WorkflowEngine is mandatory (operational judgment)
   - Meaning of plan/execute/verify phases (design intent)
   - Operational notes for approval-wait/background-failure/pause states
   - ToolLoopGuard's role and design intent
   - Reason partial completions are separated from conversation history
   - Correlation ID (as operational/audit concept, not field list)
   - Approval-wait (as operational concept, not field list)
   - Partial completion (as operational concept, not field list)
   - Workflow state (as operational concept, not field list)
7. Rephrase operational concepts as judgments: instead of listing step-by-step actions, explain why the concept exists (e.g., "approval-wait prevents unverified tool results from affecting downstream state").
8. Mark any unrecoverable design rationale as `Needs Confirmation`.
9. Reformat remaining content in all four files using the standard template:
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

10. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links or removed-file references.
11. Manually verify that all four documents still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process all four files together since they form a single logical unit.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure cross-references between Part 1 and Part 2 remain valid after restructuring.
- Ensure consistency across all four files in terms of terminology and scope division.

## Compatibility considerations

N/A — documentation-only change. No API or behavior compatibility concerns.

## Security considerations

N/A — documentation-only change. No security implications.

## Rollback considerations

Rollback is straightforward: restore the original files from git history if the restructuring introduces errors or loses critical information.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Consistency check | `python tools/check_agent_docs_consistency.py` | 0 broken links, 0 removed-file references |
| Template compliance | Manual review against `memo-doc-agent-review.md` §修正後の章構成テンプレート | Structure matches template |
| Mechanical content removal | Manual review | No private-method-name list or dataclass field dump remains |
| Operational concept preservation | Manual review | Approval-wait / partial-completion / workflow-state concepts remain, framed as operational judgment |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the turn processing flow from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-095155_require.md
- Source plan: plans/20260807-102618_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-113613
- Related target files: docs/05_agent_03_01_turn-processing-flow-overview.md, docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md, docs/05_agent_03_03_turn-processing-flow-workflow-engine-part1.md, docs/05_agent_03_03_turn-processing-flow-workflow-engine-part2.md
