# Implementation Procedure: docs/05_agent_06_*_tool-execution-and-approval*.md

## Goal

Reduce `docs/05_agent_06_*_tool-execution-and-approval*.md` documents to canonical sources for tool-execution/approval/safety design intent by removing field lists and call-order detail, while preserving all safety-relevant judgment.

## Scope

**In-Scope**:
- Restructure all four files in `docs/05_agent_06_*_tool-execution-and-approval*.md` to preserve: `ToolExecutor` responsibility boundary, `RuntimeToolRegistry` as routing source of truth (and that `tool_names`/`ToolRegistry` are not), why DAG scheduling is used, the meaning of `serial_tool_calls`, why side-effecting tools are serialized, the Tool-level vs. Workflow-level approval boundary, why `RepositoryGateway` is an enforced boundary, fail-closed design, plan-mode design intent, why caching is limited to successful results only, in-flight de-duplication intent.
- Remove: `ToolCallResult` field lists, detailed internal call order inside `execute()`, duplicated approve/reject argument explanations, full GitHub-tool-name enumeration, preview-format tables, full audit-log field enumeration, method/helper-function detail.
- **CRITICAL**: Never drop safety-relevant rationale during trimming. After trimming, explicitly re-verify: every safety-relevant judgment (fail-closed, approval boundary, DAG scheduling, cache-success-only, in-flight de-dup) still states its reasoning and operational caveat, not just the resulting behavior.
- When in doubt about whether a detail is safety-relevant, keep it and mark for human review rather than deleting.
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
4. The four target files form a coherent logical unit (execution + approval + concurrency-safety + canonical).

## Design decisions

- Tool execution should answer "what safety guarantees does this layer provide" and "how do components coordinate," not "which constructor parameters exist."
- Field lists and call-order enumerations are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.
- Safety-relevant rationale must never be silently dropped — when in doubt, keep and mark for human review.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated API reference: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_06_01_tool-execution-and-approval-execution.md`
- `docs/05_agent_06_02_tool-execution-and-approval-approval.md`
- `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Read all four files in `docs/05_agent_06_*_tool-execution-and-approval*.md` in full.
3. Verify the four files form a coherent logical unit (execution + approval + concurrency-safety + canonical).
4. Identify sections containing:
   - `ToolCallResult` field lists
   - Detailed internal call order inside `execute()`
   - Duplicated approve/reject argument explanations
   - Full GitHub-tool-name enumeration
   - Preview-format tables
   - Full audit-log field enumeration
   - Method/helper-function detail
5. Classify each identified item as safety-relevant or mechanical detail.

#### Phase 2: Core Logic Implementation

6. For each identified mechanical section across all four files:
   - If the content includes `ToolCallResult` field lists: remove entirely; this is mechanical mapping visible in code.
   - If the content is a detailed internal call order inside `execute()`: replace with a high-level description of the execution lifecycle.
   - If the content is duplicated approve/reject argument explanations: keep only one authoritative explanation.
   - If the content is a full GitHub-tool-name enumeration: remove unless it carries operational meaning.
   - If the content is a preview-format table: remove unless it carries operational meaning.
   - If the content is a full audit-log field enumeration: remove unless it carries operational meaning.
   - If the content is method/helper-function detail: remove unless it carries operational meaning.
7. Preserve ALL safety-relevant judgment across all four files:
   - Fail-closed design (reasoning: preventing unauthorized actions on failure)
   - Approval boundary (Tool-level vs. Workflow-level distinction)
   - DAG scheduling (reasoning: enabling parallelism where safe)
   - Cache-success-only (reasoning: preventing stale/failure results from being reused)
   - In-flight de-duplication (reasoning: preventing duplicate work under concurrent requests)
8. Preserve the following non-safety decision-reference content:
   - `ToolExecutor` responsibility boundary
   - `RuntimeToolRegistry` as routing source of truth (and that `tool_names`/`ToolRegistry` are not)
   - Why DAG scheduling is used
   - Meaning of `serial_tool_calls`
   - Why side-effecting tools are serialized
   - Tool-level vs. Workflow-level approval boundary
   - Why `RepositoryGateway` is an enforced boundary
   - Plan-mode design intent
   - Why caching is limited to successful results only
   - In-flight de-duplication intent
9. When in doubt about whether a detail is safety-relevant: keep the item and mark for human review rather than deleting.
10. Rephrase operational concepts as judgments: instead of listing step-by-step actions, explain why the concept exists (e.g., "fail-closed prevents unauthorized actions on failure").
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

#### Phase 3: Safety Re-verification

13. Explicitly re-verify each safety-relevant judgment:
    - Fail-closed: Does the text state its reasoning and operational caveat?
    - Approval boundary: Is the Tool-level vs. Workflow-level distinction clear?
    - DAG scheduling: Does the text state its reasoning and operational caveat?
    - Cache-success-only: Does the text state its reasoning and operational caveat?
    - In-flight de-dup: Does the text state its reasoning and operational caveat?
14. Flag any safety rationale that appears weakened or incomplete for human review.

#### Phase 4: Deployment & Verification

15. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links or removed-file references.
16. Manually verify that all four documents still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process all four files together since they form a single logical unit. Critical: safety-relevant rationale must never be silently dropped.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure cross-references between all four parts remain valid after restructuring.
- Ensure consistency across all four files in terms of terminology and scope division.
- **Safety re-verification is mandatory**: after trimming, explicitly check that every safety judgment retains its reasoning and operational caveat.

## Compatibility considerations

N/A — documentation-only change. No API or behavior compatibility concerns.

## Security considerations

This is the most security-sensitive documentation change in this batch. Safety-relevant rationale must never be silently dropped. When in doubt, keep the item and mark for human review.

## Rollback considerations

Rollback is straightforward: restore the original files from git history if the restructuring introduces errors or loses critical information.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Consistency check | `python tools/check_agent_docs_consistency.py` | 0 broken links, 0 removed-file references |
| Template compliance | Manual review against `memo-doc-agent-review.md` §修正後の章構成テンプレート | Structure matches template |
| Mechanical content removal | Manual review | No `ToolCallResult` field list or full GitHub-tool-name table remains |
| Safety rationale preservation | Manual review against safety checklist | All five safety judgments (fail-closed, approval boundary, DAG scheduling, cache-success-only, in-flight de-dup) retain their reasoning and operational caveats |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the tool-execution flow from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-095519_require.md
- Source plan: plans/20260807-103207_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-114145
- Related target files: docs/05_agent_06_01_tool-execution-and-approval-execution.md, docs/05_agent_06_02_tool-execution-and-approval-approval.md, docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md, docs/05_agent_06_04_tool-execution-and-approval-canonical.md
