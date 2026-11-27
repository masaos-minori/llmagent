# Implement final-payload context budgeting and unified diagnostics

## Priority
High

## Summary
Define and implement final-payload token budgeting, fail-closed overflow handling, and unified `/stats`, `/context`, and `/debug verbose` diagnostics for Repository Context and Episodic Memory.

## Background
Source: bundle item H-07. Verified against master on 2026-11-27:
- `Explicit in code`: `context_budget_exceeded` has no match in the repository; the typed error is new.
- `Explicit in code`: `LlmTurnExecutor` (`scripts/agent/llm_turn_executor.py`) and `LLMTurnRunner` (`scripts/agent/llm_turn_runner.py`) exist; `scripts/agent/turn_result.py`, `scripts/agent/context.py`, and `scripts/agent/history.py` exist; `scripts/agent/history/` does not.
- `Documentation only`: Known Issue `SHARED-007` tracks the undefined overflow contract.
- `Needs confirmation`: the tokenizer implementation and the position of the `llm.stream()` call were not read in this verification.

## Problem
History limits and character truncation do not guarantee that the final request fits the model context after instructions, tool schemas, Repository Context, Episodic Memory, current input, tool results, response reserve, and safety margin are added. The failure contract for irreducible mandatory payload is undefined.

## Reason for Change
Budgeting and diagnostics share category accounting, selection outcomes, exclusion reasons, and safety constraints; one issue avoids duplicated accounting and inconsistent operator views. It integrates issues/20261127-085930_amem002_repository-context-implementation.md and issues/20261127-085931_amem003_episodic-core-recovery.md and replaces the diagnostics that `/memory` provided.

## Implementation Intent
Reduce optional information deterministically and enforce the token limit immediately before `llm.stream()`. Never silently remove mandatory content; return `context_budget_exceeded` with safe aggregate metadata when it cannot fit. `LlmTurnExecutor` owns the contract and `LLMTurnRunner` is the enforcement point.

## Target Files or Areas
- `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/context.py`, `scripts/agent/turn_result.py`
- `scripts/agent/history.py`, `scripts/agent/history_selection_policy.py`
- the LLM client and tokenizer implementation (`Unknown`), `scripts/agent/commands/`, `config/agent.toml`
- Agent context, history, turn, and diagnostics tests; Agent turn-processing, LLM, CLI, and context documents

## Required Changes
- Budget contract: define all budget categories; adopt the reduction order (low-ranked Episodic Memory, low-ranked Repository Context, old conversation history, non-required tool result details); protect System and Developer instructions, current user input, required tool schemas, mandatory canonical context, response reserve, and safety margin; define fail-closed conditions for irreducible overflow, tokenizer failure, model-limit failure, and inconsistent calculation; define `context_budget_exceeded` as the typed error with safe diagnostic fields and prohibited content; require recalculation on retry.
- Configuration: add response-reserve and safety-margin settings with explicit automatic-value semantics instead of overloading an existing zero value; recommended defaults are a response reserve of 20% of the model context capped at 8,192 tokens and a safety margin of 5% with a 512-token minimum; resolve values at startup or model selection.
- Runtime: implement a final-payload assembler and token calculator using the actual model tokenizer across every category; apply the reduction order and recalculate after each compression or truncation; enforce the limit directly before the LLM request; map overflow to `context_budget_exceeded` in `LlmTurnExecutor`; do not use model switching as an automatic fallback.
- Diagnostics: `/stats` reports Repository Context state and Episodic count, extraction, prune, search mode, retention, and consistency; `/context` reports tokens and percentages per category, reserve, and margin; `/debug verbose` reports safe selection, exclusion, scope, duplicate, fallback, and budget reasons; record FTS-only degraded mode; never display Episodic contents or IDs.

## Constraints
- Do not silently remove mandatory content.
- Do not expose repository text, Episodic contents, secrets, personal data, or raw tool results in errors or diagnostics (`skills/DESIGN.md` No secrets in output).
- Do not close `SHARED-007` until the contract, implementation, and tests are complete.

## Acceptance Criteria
- No oversized final payload reaches the LLM client.
- Mandatory content is never silently removed.
- `context_budget_exceeded` carries safe metadata only.
- Operators can inspect aggregate Memory and context state without `/memory`.
- `SHARED-007` can be removed with complete evidence.

## Testing Expectations
Each reduction stage; mandatory overflow; tokenizer and model-limit failure; retry recalculation; tool schema and tool result accounting; a test proving no oversized request reaches the LLM client; secret-safe errors and diagnostics; `/stats`, `/context`, and `/debug verbose`. Run `rules/toolchain.md`.

## Documentation Impact
Budget categories, reduction order, fail-closed behavior, and diagnostics in the Agent turn-processing, LLM, CLI, and context documents; no concrete default values in prose. Handled in issues/20261127-085937_amem009_docs-manifests-sync.md.

## Out of Scope
- Repository Context and Episodic implementation (issues/20261127-085930_amem002_repository-context-implementation.md, issues/20261127-085931_amem003_episodic-core-recovery.md) and model-switching fallback.

## Dependencies
- Depends on issues/20261127-085930_amem002_repository-context-implementation.md and issues/20261127-085931_amem003_episodic-core-recovery.md.
- Blocks issues/20261127-085936_amem008_legacy-memory-removal.md and issues/20261127-085937_amem009_docs-manifests-sync.md.

## Unresolved Questions
- `不明`: the model tokenizer source and the model context-window lookup used at selection time.
- `不明`: the exact budget categories and the maintainer's confirmation of the recommended defaults.

## AI Implementation Instruction
Enforce the limit at the single point immediately before `llm.stream()`. Do not add new fallback behavior. Stop and report if the tokenizer for a configured model cannot be identified.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085935
- **Related target files**: `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/context.py`, `scripts/agent/turn_result.py`, `scripts/agent/history.py`, `scripts/agent/commands/`, `config/agent.toml`
