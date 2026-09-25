# Implement GV-021 Docs Content Policy Violation Detection

## Priority
Medium

## Summary
Run `check_docs_content_policy.py` against the current corpus and create follow-up issues from the violation inventory. Promote the check from opt-in to default-on once the corpus is compliant.

## Background
GV-021 tracks violations of the docs content policy — implementation details that should not appear in `docs/*.md` per `skills/DESIGN.md` Docs content policy — remove. The check currently has Partial status because it has not been run against the full corpus. The Follow-up Work Needed section states: "Run against the current corpus and scope follow-up content-migration issues from the violation inventory; promote to default-on once the corpus is compliant." An exemption exists for auto-generated content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments.

## Problem
The docs content policy prohibits implementation-detail content in documentation (full file trees, per-file descriptions embedded in a tree or table, class/function/method index tables, implementation-location mappings, literal port numbers), but the automated check has never been executed against the full corpus. Without running the check, we cannot know the scope of violations or prioritize remediation work.

## Reason for Change
GV-021's Follow-up Work Needed explicitly requires a corpus run to identify violations before the check can be promoted to default-on. This is a prerequisite for closing the gap.

## Implementation Intent
1. Run `uv run python tools/check_docs_content_policy.py` against the current corpus
2. Collect all findings into a structured inventory
3. Group findings by category (file tree, per-file description, class/index table, implementation location, literal port number)
4. Create one issue per category group (or per file if groups are too large) with concrete remediation steps
5. After all violations are resolved, update GV-021 status from "Partial" to "Existing" and promote the check to default-on

## Target Files or Areas
- `tools/check_docs_content_policy.py`
- `docs/*.md`
- `skills/DESIGN.md` (Docs content policy — remove)

## Required Changes
- Execute `check_docs_content_policy.py` against the full corpus
- Document all findings in a structured format
- Create follow-up issues for each violation category
- Update GV-021 governance matrix row after remediation

## Constraints
- Auto-generated content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments is exempt (per REQ-001 decision)
- Do not modify source code — this is a documentation cleanup initiative
- Each follow-up issue must have concrete acceptance criteria tied to specific files

## Acceptance Criteria
- All violations identified by `check_docs_content_policy.py` are documented
- One issue per violation category or per file (whichever produces reviewable scope)
- Each issue contains concrete remediation steps with file-level targets
- After remediation, GV-021 status is updated to "Existing" and the check is promoted to default-on

## Testing Expectations
- Manual verification: confirm `check_docs_content_policy.py` runs without errors against the corpus
- No unit tests required (documentation-only work)

## Documentation Impact
This issue itself documents the process for identifying and tracking violations. Follow-up issues will document the specific remediation steps for each violation category.

## Out of Scope
- Modifying `check_docs_content_policy.py` logic
- Removing auto-generated content blocks (exempt per REQ-001)
- Changing the docs content policy itself

## Dependencies
- GV-021 governance matrix row (current: Partial)
- `skills/DESIGN.md` Docs content policy — remove

## Unresolved Questions
- How many violations exist across the corpus? (requires corpus run)
- Which categories produce the most violations? (requires corpus run)
- Should any existing violations be formally excepted rather than fixed?

## AI Implementation Instruction
Run `uv run python tools/check_docs_content_policy.py` and collect all findings. Group by violation category. Create one issue per category with concrete file-level remediation steps. Do not modify the tool or the policy.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-232919
- **Related target files**: tools/check_docs_content_policy.py, docs/*.md
