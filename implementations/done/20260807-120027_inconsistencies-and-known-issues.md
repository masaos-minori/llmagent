# Implementation Procedure: docs/05_agent_90_inconsistencies_and_known_issues.md

## Goal

Reduce `docs/05_agent_90_inconsistencies_and_known_issues.md` by removing bare diff memos and unexplained file:line notes, while restructuring each entry to have operational meaning (what the issue means, why it is a problem, what operators should watch for, and the criteria for deciding whether/how to fix it).

## Scope

**In-Scope**:
- Restructure all entries in `docs/05_agent_90_inconsistencies_and_known_issues.md` to preserve: the meaning of each known issue, why it is a problem, operational cautions, fix-decision criteria, the classification of items as removed/migrated/needs-confirmation, and the reasoning behind each Needs Confirmation entry.
- Remove: bare code-diff memos, "confirmed at file X line Y" notes with no operational meaning, plain implementation-visible enumerations.
- **CRITICAL**: Never drop operational judgment during trimming. After trimming, explicitly re-verify: all known issues still state their reasoning and operational caveat.
- When in doubt about whether a detail is operational judgment, keep it and mark for human review rather than deleting.
- Verify against current code whether discrepancies still apply before removing any entry.
- Cross-reference actual bug-track issues under `issues/` where an "Implementation fix required" classification applies.
- Rephrase operational concepts as judgments (why), not just mechanical descriptions.
- Reformat using the template: Purpose / Design Intent / Responsibility Boundary / Key Constraints / Operational Notes / Known Limitations / Related Docs.
- Mark unrecoverable design rationales as `Needs Confirmation`.
- File new "Implementation fix required" items as separate issues under `issues/` rather than only noting them here.

**Out-of-Scope**:
- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.

## Assumptions

1. The `memo-doc-agent-review.md` referenced in acceptance criteria existed during the original review but may have been moved or deleted since then.
2. `tools/check_agent_docs_consistency.py` is available and functional for post-edit verification, including the obsolete diagnostics/event-name reference check relevant to this chapter.
3. All entries in `docs/05_agent_90_inconsistencies_and_known_issues.md` can be verified against current code.
4. The five-way classification exists: Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable.

## Design decisions

- Known issues documentation should answer "what is wrong" and "how do I respond," not "which file contains which discrepancy."
- Bare code-diff memos and unexplained file:line notes are visible in code and add no operational value.
- Canonical Source Rule applies: when a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.
- Operational judgment must never be silently dropped — when in doubt, keep and mark for human review.
- Entries must never be deleted without verifying against current code first.

## Alternatives considered

- Keep current format: violates the principle that mechanical inventories should not be maintained manually.
- Replace with auto-generated API reference: would reduce maintenance burden but loses human-curated narrative. Not pursued without explicit request.

## Implementation

### Target files

- `docs/05_agent_90_inconsistencies_and_known_issues.md`

### Procedure

#### Phase 1: Preparation

1. Confirm `memo-doc-agent-review.md` existence and locate it (search repo root and subdirectories); if unavailable, proceed using require doc acceptance criteria.
2. Verify the five-way classification exists and is documented.
3. Read `docs/05_agent_90_inconsistencies_and_known_issues.md` in full.
4. Identify sections containing:
   - Bare code-diff memos
   - "Confirmed at file X line Y" notes with no operational meaning
   - Plain implementation-visible enumerations
5. Classify each item as operational judgment or mechanical detail.

#### Phase 2: Core Logic Implementation

6. For each identified mechanical section across the document:
   - If the content includes bare code-diff memos: remove unless it carries operational meaning.
   - If the content is a "confirmed at file X line Y" note with no operational meaning: remove entirely; this is mechanical mapping visible in code.
   - If the content is a plain implementation-visible enumeration: remove unless it carries operational meaning.
7. Preserve ALL operational judgment across the document:
   - Meaning of each known issue
   - Why it is a problem
   - Operational cautions
   - Fix-decision criteria
   - Classification of items as removed/migrated/needs-confirmation
   - Reasoning behind each Needs Confirmation entry
8. Verify against current code whether discrepancies still apply before removing any entry.
9. Cross-reference actual bug-track issues under `issues/` where an "Implementation fix required" classification applies.
10. File new "Implementation fix required" items as separate issues under `issues/` rather than only noting them here.
11. When in doubt about whether a detail is operational relevance: keep the item and mark for human review rather than deleting.
12. Rephrase operational concepts as judgments: instead of listing step-by-step actions, explain why the concept exists (e.g., "this discrepancy matters because it affects operator decision-making").
13. Mark any unrecoverable design rationale as `Needs Confirmation`.
14. Reformat remaining content using the standard template:
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

15. Explicitly re-verify each known issue:
    - Does the text state its meaning?
    - Does the text state why it is a problem?
    - Does the text state its operational cautions?
    - Does the text state its fix-decision criteria?
    - Is its classification correct?
16. Flag any known issue that appears weakened or incomplete for human review.

#### Phase 4: Deployment & Verification

17. Run `python tools/check_agent_docs_consistency.py` to confirm no broken internal links or removed-file references.
18. Specifically verify: obsolete diagnostics/event-name reference check passes.
19. Manually verify that all entries still serve their navigation purpose after restructuring.

### Method

Document restructuring through selective removal and reformatting. No code changes. Process the single file thoroughly since it contains critical operational knowledge. Critical: operational judgment must never be silently dropped, and entries must never be deleted without verifying against current code first.

### Details

- Before deleting any section, verify it is not the sole documented source for a given fact.
- When replacing mechanical detail with pointers, ensure the pointer leads to a stable, discoverable location.
- After reformatting, validate that each section header maps to content that actually belongs under it.
- Ensure consistency within the document in terms of terminology and scope division.
- Cross-reference `issues/` for "Implementation fix required" items.
- **Operational judgment re-verification is mandatory**: after trimming, explicitly check that every known issue retains its reasoning and operational caveats.
- **Entry deletion safety is mandatory**: verify against current code before removing any entry; never delete without this verification.

## Compatibility considerations

N/A — documentation-only change. No API or behavior compatibility concerns.

## Security considerations

This is a security-sensitive documentation change. Operational judgment must never be silently dropped. When in doubt, keep the item and mark for human review. Entries must never be deleted without verifying against current code first.

## Rollback considerations

Rollback is straightforward: restore the original file from git history if the restructuring introduces errors or loses critical information.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Consistency check | `python tools/check_agent_docs_consistency.py` | 0 broken links, 0 removed-file references, 0 obsolete diagnostics/event-name references |
| Template compliance | Manual review against `memo-doc-agent-review.md` §修正後の章構成テンプレート | Structure matches template |
| Mechanical content removal | Manual review | No entry is a bare diff memo or unexplained file:line note; each has stated operational meaning |
| Five-way classification | Manual review | Every entry is classified per the five-way classification before being kept, cross-referenced, fixed, or deleted |
| Operational judgment preservation | Manual review against operational judgment checklist | All known issues retain their reasoning and operational caveats |

## Out of scope

- Modifying other documents in the `05_agent_*.md` set.
- Adding new content beyond what exists in the current documents.
- Changing the doc set directory structure.
- Auto-generating the known issues documentation from code metadata.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-101359_require.md
- Source plan: plans/20260807-105141_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-120027
- Related target files: docs/05_agent_90_inconsistencies_and_known_issues.md
