# Neutralize persisted memory text before it enters the system prompt at startup

## Priority
Medium

## Summary
`PromptSetup.setup_prompt` appends stored memory snippets to the initial system prompt as plain text. Those memories are extracted automatically from earlier user and assistant turns, and the only transformation applied between storage and the system role is PII redaction and truncation. Add a trust-boundary step so persisted text cannot act as system-level instructions in a later session, or record the accepted risk explicitly.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`. This issue is one finding of that review.
- Evidence (Explicit in code): `PromptSetup.setup_prompt` builds a memory block headed by a fixed marker line and concatenates each snippet text onto `initial_prompt`; `AgentContext.conv.replace_history` then stores it as the single `system` message.
- Evidence (Explicit in code): `MemoryIngestionService.on_session_stop` calls `extract_memories`, which reads `assistant` and `user` messages of the session history; `MemoryInjectionService._build_snippets` applies `filter_pii` and `truncate_snippet` only.
- Evidence (Strongly implied by code): assistant text can echo content that came from tool output (web pages, repository files, MCP results), so attacker-controlled text can be memorized in one session and promoted to the system role in the next. No neutralization step was found in `scripts/agent/memory`.
- Related, already closed and not overlapping: `issues/done/20261012-124838_start004_startup-prompt-setup-swallows-all-memory-injection-errors-as-a-generic-disabled-flag.md` (error classification only).

## Problem
The system role carries the highest instruction authority. Memory text enters it unmarked and unescaped. A memory whose text imitates the marker line or contains imperative instructions is indistinguishable from operator-authored system prompt content once injected. The existing `ROLE_KEY_WHITELIST` and source-trust handling in `agent.context` protect message structure, not message content.

## Reason for Change
Persistent prompt injection survives across sessions, so one poisoned turn affects every later session until the memory is pruned. Nothing makes this urgent today: exploitability depends on how memories are extracted (see Unresolved Questions), so the change is a hardening step, not a hotfix.

## Implementation Intent
Treat memory snippets as untrusted data at the point where they cross into the system prompt. Keep the memory feature and its content, but make the boundary explicit: delimit the block unambiguously, neutralize text that imitates the delimiter or role markers, and state in the surrounding prompt text that the block is recalled data and not instructions. Prefer one shared helper so the per-turn injection path (`on_user_prompt`) can use the same rule. Do not change extraction, scoring, retrieval, or PII filtering.

## Target Files or Areas
- scripts/agent/startup_prompt_setup.py (`PromptSetup.setup_prompt`)
- scripts/agent/memory/injection.py (`MemoryInjectionService`, snippet building)
- scripts/agent/memory/snippet_filter.py (home for a neutralization helper)
- tests/agent/test_startup_prompt_setup.py

## Required Changes
- Decide the neutralization rule for snippet text (delimiter collisions, role-marker look-alikes, control characters) and implement it in one helper beside the existing snippet filters.
- Apply the helper to the startup block built by `PromptSetup.setup_prompt`.
- Frame the block in the prompt as recalled data and not instructions.
- Add tests: a snippet imitating the block marker, a snippet containing role-style instructions, and unchanged output for ordinary snippets.

## Constraints
- Memory retrieval ordering, count limits, and PII redaction MUST keep their current behavior.
- The helper MUST NOT drop legitimate snippets silently; a changed snippet is logged without logging its full text.
- Comments and log messages are English only.

## Acceptance Criteria
- A snippet containing the block marker text cannot terminate or forge the memory block in the resulting system prompt.
- A snippet containing role-style instructions appears only inside the delimited, data-framed block.
- Ordinary snippets are injected with unchanged wording.
- `uv run pytest tests/agent/test_startup_prompt_setup.py` passes with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit tests for the helper and for `setup_prompt` output; no integration test is required. Run the startup prompt tests and the memory injection tests.

## Documentation Impact
Update the agent memory design document to state the trust boundary: memory content is untrusted data, and what the system prompt does with it. Do not add file lists or concrete limits.

## Out of Scope
- Changing how memories are extracted, scored, deduplicated, or stored.
- The per-turn `on_user_prompt` path beyond reusing the same helper.
- Removing or redesigning the memory feature.

## Dependencies
N/A: none

## Unresolved Questions
- Is the memory store reachable by content that did not come from the local operator (tool output echoed by the assistant, web content)? The exploitability of this finding depends on it. (Needs confirmation)
- Should the per-turn injection path share the same rule in this issue or a follow-up? (Assumption: follow-up.)

## AI Implementation Instruction
Keep the change minimal and confined to the listed areas. Do not alter extraction, retrieval, or scoring. If the exploitability question changes the decision (for example, the store is operator-only), stop and report instead of implementing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214901
- **Related target files**: scripts/agent/startup_prompt_setup.py, scripts/agent/memory/injection.py, scripts/agent/memory/snippet_filter.py, tests/agent/test_startup_prompt_setup.py
