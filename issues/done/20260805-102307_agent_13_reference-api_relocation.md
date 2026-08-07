# Separate docs/05_agent_13_reference-api-part{1,2}.md from design-doc body content

## Priority
Low

## Summary
`memo-doc-agent-review.md` recommends considering separating this chapter out of the design-doc body entirely and treating it, at most, as an "implementation reference index" — not part of the design narrative.

## Reason for Change
API/type/method detail mixed into the design-doc body increases maintenance burden (it must track code exactly) without adding design or operational judgment. Other `05_agent_*.md` chapters should point here (or to an auto-generated reference) rather than re-explaining API detail inline.

## Implementation Intent
Per `memo-doc-agent-review.md` §「05_agent_13_reference-api」: do not place this content in the design-doc body by default. If retained at all, treat it strictly as an implementation-reference index. API/type/method detail should be delegated to code or an auto-generated reference; other chapters should say only "see Reference API for detail" rather than duplicating.

## Target Files or Areas
- `docs/05_agent_13_reference-api-part1.md`
- `docs/05_agent_13_reference-api-part2.md`
- Cross-references from other `docs/05_agent_*.md` chapters that currently duplicate API/type/method detail instead of pointing here.

## Required Changes
- Decide (with the doc owner) whether this content should: (a) remain as a clearly separate "implementation reference index" outside the main design-doc narrative, or (b) be replaced by an auto-generated reference.
- Audit other `05_agent_*.md` chapters for inline API/type/method detail that duplicates this chapter's content, and replace with a pointer to this chapter (per the canonical-source rule: API詳細 = `05_agent_13_reference-api`).
- Do not delete content without confirming it is not the sole documented source for a given API/type/method.

## Acceptance Criteria
- A decision is recorded on whether this chapter stays as a reference index or is replaced by auto-generation.
- No other `05_agent_*.md` chapter re-explains API/type/method detail that belongs here; each instead links to this chapter.
- If content is deleted, it is confirmed to be reconstructable from code (not the only record of a discontinued API's rationale).

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing to confirm no broken internal links from other chapters that now point here.

## Documentation Impact
This issue is itself a documentation-only cleanup/relocation task.

## Out of Scope
- Generating new auto-generated API reference tooling (that would be a separate, larger task if chosen as the direction).
- Other `docs/05_agent_*.md` chapters' non-API content.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_13_reference-api」. This chapter has different treatment than the others (relocation/reference-index decision, not a keep/remove edit) — do not apply the standard 修正後の章構成テンプレート here unless the decision is to keep it as a design-doc chapter. Raise the (a)/(b) decision as an open question if it cannot be resolved unilaterally; mark unclear scope as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_13_reference-api」
- Generated at: 2026-08-05
