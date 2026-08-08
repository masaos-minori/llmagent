# Implementation Procedure: docs/05_agent_05_llm-and-streaming-part{1,2}.md

## Goal

Reduce `docs/05_agent_05_llm-and-streaming-part1.md` and `docs/05_agent_05_llm-and-streaming-part2.md` to canonical sources for LLM streaming and partial-completion design intent by removing constructor signatures, DTO field lists, and mechanical enumerations.

## Scope

**In-Scope**:
- Restructure both parts of `docs/05_agent_05_llm-and-streaming-part{1,2}.md` to preserve: SSE streaming design intent, conditions under which reconnection is/is not attempted, why partial responses are kept out of history and isolated to `session_diagnostics`, operational meaning of retryable vs. fatal, statistical limitations when `usage` is absent.
- Reframe error kinds around: whether a retry is safe, why a partial response must not enter history, when the user should be warned.
- Remove: full `LLMClient` constructor signature, DTO field lists, `SSEParser` method lists, plain error-kind enumeration, fine-grained temperature/max-tokens tables.
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

## Design decisions

- LLM streaming should answer "how does the agent handle unreliable transport" and "what happens when things go wrong," not "which constructor parameters exist."
- Constructor signatures, DTO field lists, and method enumerations are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated API reference: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_05_llm-and-streaming-part1.md`
- `docs/05_agent_05_llm-and-streaming-part2.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Read both parts of `docs/05_agent_05_llm-and-streaming-part{1,2}.md` in full.
3. Identify sections containing:
   - Full `LLMClient` constructor signature
   - DTO field lists
   - `SSEParser` method lists
   - Plain error-kind enumeration
   - Fine-grained temperature/max-tokens tables

#### Phase 2: Core Logic Implementation

4. For each identified mechanical section across both files:
   - If the content includes a full `LLMClient` constructor signature: replace with a description of the client's purpose and key configuration categories (model, endpoint, auth, streaming).
   - If the content is a DTO field list: remove entirely; this is mechanical mapping visible in code.
   - If the content is an `SSEParser` method list: remove unless it carries operational meaning.
   - If the content is a plain error-kind enumeration: reframe around operational judgment (see step 5).
   - If the content is a fine-grained temperature/max-tokens table: remove unless it carries operational meaning beyond what code provides.
5. Reframe error kinds around three operational dimensions:
   - Whether a retry is safe (retryable vs. fatal)
   - Why a partial response must not enter history (data integrity)
   - When the user should be warned (operational notification)
6. Preserve the following content across both files:
   - SSE streaming design intent (why SSE, not polling or webhook)
   - Conditions under which reconnection is/is not attempted (operational judgment)
   - Why partial responses are kept out of history and isolated to `session_diagnostics` (design intent)
   - Operational meaning of retryable vs. fatal (operational judgment)
   - Statistical limitations when `usage` is absent (design constraint)
7. Mark any unrecoverable design rationale as `Needs Confirmation`.
8. Reformat remaining content in both files using the standard template:
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

9. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links or removed-file references.
10. Manually verify that both documents still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process both files together since they form a single logical unit.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure Part 1 and Part 2 have consistent scope division after restructuring (Part 1 = streaming protocol, Part 2 = error handling/partial responses).
- Cross-reference `session_diagnostics` as the isolation boundary for partial responses.

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
| Mechanical content removal | Manual review | No constructor signature or DTO field list remains |
| Error-kind reorganization | Manual review | Error-kind section organized by operational judgment (retry safety / history exclusion / user warning), not a bare list |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the LLM/streaming flow from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-095411_require.md
- Source plan: plans/20260807-103018_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-113955
- Related target files: docs/05_agent_05_llm-and-streaming-part1.md, docs/05_agent_05_llm-and-streaming-part2.md
