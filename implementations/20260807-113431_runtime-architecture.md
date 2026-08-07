# Implementation Procedure: docs/05_agent_02_runtime-architecture-part{1,2}.md

## Goal

Reduce `docs/05_agent_02_runtime-architecture-part1.md` and `docs/05_agent_02_runtime-architecture-part2.md` to canonical sources for runtime responsibility boundaries by removing fine-grained implementation detail.

## Scope

**In-Scope**:
- Restructure both parts of `docs/05_agent_02_runtime-architecture-part{1,2}.md` to preserve: AgentREPL-as-thin-coordinator judgment, reason StartupOrchestrator was split out, AgentContext/AppServices responsibility boundary, Orchestrator/LLMTurnRunner/ToolExecutor/HistoryManager role split, shared-vs-agent dependency direction, startup-validation fail-fast/rollback policy.
- Remove: fine-grained private class names in dependency graphs, mixin counts, MRO detail, internal implementation class names, method-level responsibility tables, `Explicit in code`-labeled implementation-confirmation notes.
- Rephrase fail-fast/rollback policy as a judgment (why), not just a mechanical description of steps.
- Reformat using the template: Purpose / Design Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known Limitations / Related Docs.
- Mark unrecoverable design rationales as `Needs Confirmation`.

**Out-of-Scope**:
- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.

## Assumptions

1. The `memo-doc-agent-review.md` referenced in acceptance criteria exists and contains a valid chapter structure template.
2. `tools/check_agent_docs_consistency.py` is available and functional for post-edit verification.
3. All mechanical content being removed is indeed duplicatable via code search (no unique facts will be lost).
4. The architectural boundary rule enforced by `lint-imports` is already configured for shared-vs-agent dependency direction.

## Design decisions

- Runtime architecture should answer "what responsibility does each component own" and "how do components interact," not "which private class name appears where."
- Private implementation details (class names, mixin counts, MRO order) are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated dependency graph: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_02_runtime-architecture-part1.md`
- `docs/05_agent_02_runtime-architecture-part2.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` exists and locate it (search repo root and subdirectories).
2. Read both parts of `docs/05_agent_02_runtime-architecture-part{1,2}.md` in full.
3. Verify `lint-imports` configuration for shared-vs-agent dependency direction (check `.importlinter` or pyproject.toml).
4. Identify sections containing:
   - Fine-grained private class names in dependency graphs
   - Mixin counts and MRO (Method Resolution Order) detail
   - Internal implementation class names
   - Method-level responsibility tables
   - `Explicit in code`-labeled implementation-confirmation notes

#### Phase 2: Core Logic Implementation

5. For each identified mechanical section across both files:
   - If the content lists private class names in dependency graphs: replace with high-level component names only.
   - If the content includes mixin counts or MRO detail: remove entirely; this is mechanical mapping visible in code.
   - If the content includes internal implementation class names: remove unless they carry operational meaning.
   - If the content is a method-level responsibility table: replace with component-level responsibility descriptions.
   - If the content includes `Explicit in code`-labeled notes: remove; these are implementation-confirmation markers, not design rationale.
6. Preserve the following content across both files:
   - AgentREPL-as-thin-coordinator judgment (why REPL delegates rather than orchestrates)
   - Reason StartupOrchestrator was split out (operational judgment)
   - AgentContext/AppServices responsibility boundary
   - Orchestrator/LLMTurnRunner/ToolExecutor/HistoryManager role split (component-level, not method-level)
   - Shared-vs-agent dependency direction (verify against lint-imports config)
   - Startup-validation fail-fast/rollback policy (rephrase as judgment, not mechanical steps)
7. Rephrase the fail-fast/rollback policy: instead of listing step-by-step actions, explain why the policy exists (e.g., "fail fast prevents cascading failures during startup").
8. Mark any unrecoverable design rationale as `Needs Confirmation`.
9. Reformat remaining content in both files using the standard template:
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
11. Manually verify that both documents still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process both files together since they form a single logical unit.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Cross-reference `.importlinter` or pyproject.toml for shared-vs-agent dependency direction before stating it as a constraint.
- Ensure Part 1 and Part 2 have consistent scope division after restructuring (Part 1 = core runtime, Part 2 = extension points/lifecycle).

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
| Mechanical content removal | Manual review | No mixin/MRO enumeration or method-level responsibility tables remain |
| Fail-fast/rollback rephrasing | Manual review | Policy stated as judgment (why), not mechanical steps |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the runtime architecture from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-095052_require.md
- Source plan: plans/20260807-102438_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-113431
- Related target files: docs/05_agent_02_runtime-architecture-part1.md, docs/05_agent_02_runtime-architecture-part2.md
