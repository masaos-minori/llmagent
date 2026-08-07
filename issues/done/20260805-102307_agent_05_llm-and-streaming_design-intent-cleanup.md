# Reduce implementation-derived detail in docs/05_agent_05_llm-and-streaming-part{1,2}.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-agent-review.md` to the LLM-and-streaming chapter (both parts): keep the SSE reconnection design intent and error-kind operational classification; remove constructor signatures, DTO field lists, and mechanical error-kind enumeration.

## Reason for Change
The chapter mixes genuine operational judgment (when to reconnect, why partial responses are isolated to `session_diagnostics`, what retryable/fatal mean operationally) with code-derivable detail (full `LLMClient` constructor signature, DTO fields, `SSEParser` method list) that will drift on refactor.

## Implementation Intent
Keep this chapter as the canonical source for LLM streaming and partial-completion design (per `memo-doc-agent-review.md` §「章間の正本ルール」: LLMストリーミングと部分完了 = `05_agent_05_llm-and-streaming`). Error kinds must be reframed as an operational classification, not a plain enumeration.

## Target Files or Areas
- `docs/05_agent_05_llm-and-streaming-part1.md`
- `docs/05_agent_05_llm-and-streaming-part2.md`

## Required Changes
- Keep: SSE streaming design intent, the conditions under which reconnection is/is not attempted, why partial responses are kept out of history and isolated to `session_diagnostics`, the operational meaning of retryable vs. fatal, statistical limitations when `usage` is absent.
- Remove or compress: full `LLMClient` constructor signature, DTO field lists, `SSEParser` method lists, plain error-kind enumeration, fine-grained temperature/max-tokens tables.
- Reframe error kinds around: whether a retry is safe, why a partial response must not enter history, when the user should be warned.

## Acceptance Criteria
- Both files follow the standard template from `memo-doc-agent-review.md` §「修正後の章構成テンプレート」.
- No constructor signature or DTO field list remains.
- Error-kind section is organized by operational judgment (retry safety / history exclusion / user warning), not a bare list.

## Testing Expectations
Not required for behavior (documentation-only). Run `python tools/check_agent_docs_consistency.py` after editing.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/05_agent_*.md` chapters.
- Code changes to the streaming client or SSE parser.

## AI Implementation Instruction
Follow `memo-doc-agent-review.md` §「05_agent_05_llm-and-streaming」 including its 注意 note on reframing error kinds around operational judgment rather than enumeration. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-agent-review.md` §「05_agent_05_llm-and-streaming」
- Generated at: 2026-08-05
