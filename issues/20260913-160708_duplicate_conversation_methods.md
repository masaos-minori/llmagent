# Duplicate conversation state methods between TurnCoordinator and ConversationStateManager

## Priority
Medium

## Summary
Resolve duplication of `clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, and `append_user_message` between TurnCoordinator and ConversationStateManager.

## Background
Both classes implement near-identical logic for three core operations: ephemeral message cleanup, system prompt sync, and user message appending. This duplication arose during the extraction/refactoring that split orchestrator.py into these modules.

## Problem
Callers may invoke either class for the same operation, leading to inconsistent behavior depending on which path is taken. Both classes iterate over EPHEMERAL_KEYS, sync the system prompt, append user messages, and manage first-turn background tasks — but with subtle differences in how they handle validation and error reporting.

## Reason for Change
Duplication makes maintenance harder and increases the risk of divergent behavior between the two implementations.

## Implementation Intent
Consolidate all three operations into ConversationStateManager (the more feature-complete class) and delegate from TurnCoordinator. Or merge both classes if TurnCoordinator's role reduces to audit event emission only.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/conversation_state_manager.py`
- `/home/sugimoto/llmagent/scripts/agent/turnd_coordinator.py`

## Required Changes
- Move `clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, and `append_user_message` implementations into ConversationStateManager
- Make TurnCoordinator delegate to ConversationStateManager for these operations
- Ensure both classes share the same EPHEMERAL_KEYS constant (already done via import)
- Align error handling: TurnCoordinator uses Logger, ConversationStateManager uses logging.getLogger — standardize

## Constraints
- Must not change the external API of either class
- TurnCoordinator must remain callable from the same entry points
- Backward-compatible imports must still work

## Acceptance Criteria
- Only one source of truth for each of the three operations
- All callers produce identical results regardless of which class they invoke
- No regression in ephemeral message filtering, system prompt sync, or user message append

## Testing Expectations
- Unit tests for ephemeral message filtering covering all ephemeral key variants
- Unit tests for system prompt sync with history[0] present vs absent
- Unit tests for user message append with first-turn background task spawning
- Regression tests for both TurnCoordinator and ConversationStateManager public APIs

## Documentation Impact
Update class docstrings to clarify delegation relationship between the two classes.

## Out of Scope
- Merging the two classes into one (too large a change for this issue)
- Changing the EPHEMERAL_KEYS constant itself
- Modifying the first-turn background task callback mechanism

## Dependencies
N/A: none

## Unresolved Questions
- Why did the original author create two separate classes instead of consolidating?
- Are there callers that intentionally use both classes for different purposes?

## AI Implementation Instruction
Start by comparing the two implementations line-by-line to identify all behavioral differences before merging. Document those differences in a comment during the refactor.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-160708
- **Related target files**: scripts/agent/conversation_state_manager.py, scripts/agent/turnd_coordinator.py
