## Goal

Eliminate duplication of `clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, and `append_user_message` between `TurnCoordinator` and `ConversationStateManager` by consolidating these operations into `ConversationStateManager` and delegating from `TurnCoordinator`, per REQ-001 through REQ-003.

## Scope

- In-Scope: Consolidate three duplicated methods into ConversationStateManager; make TurnCoordinator delegate to ConversationStateManager for these operations; standardize logging usage across both classes
- Out-of-Scope: Merging the two classes into one; changing the EPHEMERAL_KEYS constant itself; modifying the first-turn background task callback mechanism

## Assumptions

- No existing callers invoke TurnCoordinator's duplicate methods — all callers go through ConversationStateManager directly (verified via grep)
- ConversationStateManager is the more feature-complete class and should remain the primary owner of conversation state logic
- EPHEMERAL_KEYS constant is already shared via import from conversation_state_manager module

## Design decisions

1. Consolidate the three duplicated methods into ConversationStateManager. TurnCoordinator will hold a reference to ConversationStateManager and delegate these three operations to it. This preserves TurnCoordinator's external API while eliminating duplication.
2. The delegation approach is preferred over merging because merging would require changes to the constructor signatures and dependency injection wiring.
3. Standardize logging usage across both classes — eliminate the difference between stdlib `logging.getLogger(__name__)` in ConversationStateManager and custom `Logger(__name__, "/opt/llm/logs/agent.log")` in TurnCoordinator. Choose stdlib `logging.getLogger(__name__)` as the standard since it is the Python idiomatic approach and ConversationStateManager already uses it.

Evidence grounding:
- Both classes implement near-identical logic for three core operations: ephemeral message cleanup, system prompt sync, and user message appending
- Duplication arose during the extraction/refactoring that split orchestrator.py into these modules
- Callers may invoke either class for the same operation, leading to inconsistent behavior depending on which path is taken

## Alternatives considered

- **Merge both classes into one**: Rejected because it would require changes to constructor signatures and dependency injection wiring — a larger behavioral change than the Issue describes.
- **Keep both implementations but add synchronization**: Would maintain the duplication while adding complexity to keep them in sync — defeats the purpose of consolidation.

## Implementation
### Target files
- `scripts/agent/conversation_state_manager.py`
- `scripts/agent/turnd_coordinator.py`

### Procedure
1. Verify no callers invoke TurnCoordinator's duplicate methods
2. Document behavioral differences between the two implementations
3. Move `clear_previous_turn_ephemeral_messages` implementation into ConversationStateManager; make TurnCoordinator delegate
4. Move `sync_system_prompt` implementation into ConversationStateManager; make TurnCoordinator delegate
5. Move `append_user_message` implementation into ConversationStateManager; make TurnCoordinator delegate
6. Standardize logging usage across both classes
7. Run validation sequence

### Method
Method extraction + delegation pattern implementation across both classes.

### Details
1. **Phase 1: Preparation — Confirm current state**
   a. Verify no callers invoke TurnCoordinator's duplicate methods:
      - Check `scripts/agent/orchestrator.py` for any calls to TurnCoordinator's duplicate methods
      - Check `scripts/agent/workflow_engine_adapter.py` for any calls to TurnCoordinator's duplicate methods
   
   b. Document behavioral differences between the two implementations in a comment during refactor:
      - Compare `clear_previous_turn_ephemeral_messages` implementations side-by-side
      - Compare `sync_system_prompt` implementations side-by-side
      - Compare `append_user_message` implementations side-by-side
      - Note any subtle differences in validation or error handling

2. **Phase 2: Core Logic Implementation**
   
   a. Add delegation method wrappers to `conversation_state_manager.py`:
      ```python
      # Add a new attribute to ConversationStateManager.__init__:
      self._turnd_coordinator = None  # Set by TurnCoordinator after construction
      
      # Add delegation wrapper methods:
      def clear_previous_turn_ephemeral_messages(self):
          """Delegate to TurnCoordinator's version if available, otherwise use local."""
          if self._turnd_coordinator is not None:
              return self._turnd_coordinator.clear_previous_turn_ephemeral_messages()
          # Fallback to local implementation if no delegation set
          ...
      
      def sync_system_prompt(self):
          """Delegate to TurnCoordinator's version if available, otherwise use local."""
          if self._turnd_coordinator is not None:
              return self._turnd_coordinator.sync_system_prompt()
          # Fallback to local implementation if no delegation set
          ...
      
      def append_user_message(self):
          """Delegate to TurnCoordinator's version if available, otherwise use local."""
          if self._turnd_coordinator is not None:
              return self._turnd_coordinator.append_user_message()
          # Fallback to local implementation if no delegation set
          ...
      ```
   
   b. Replace `TurnCoordinator`'s local implementations with delegation:
      ```python
      # In TurnCoordinator.__init__, add:
      self._csm = conversation_state_manager  # Import CSM instance
      
      # Replace each method body:
      def clear_previous_turn_ephemeral_messages(self):
          """Delegate to ConversationStateManager."""
          return self._csm.clear_previous_turn_ephemeral_messages()
      
      def sync_system_prompt(self):
          """Delegate to ConversationStateManager."""
          return self._csm.sync_system_prompt()
      
      def append_user_message(self):
          """Delegate to ConversationStateManager."""
          return self._csm.append_user_message()
      ```
   
   c. Standardize logging usage across both classes:
      - In `turnd_coordinator.py`, replace custom `Logger(__name__, "/opt/llm/logs/agent.log")` with stdlib `logging.getLogger(__name__)`:
        ```python
        # Before:
        from .logger import Logger
        logger = Logger(__name__, "/opt/llm/logs/agent.log")
        
        # After:
        import logging
        logger = logging.getLogger(__name__)
        ```
      - Ensure both classes use the same logging level and format

3. **Phase 3: Deployment & Verification**
   a. Run unit tests for ephemeral message filtering, system prompt sync, and user message append:
      ```bash
      uv run pytest
      ```
      Expected outcome: All tests pass; no regression
   
   b. Run regression tests for both TurnCoordinator and ConversationStateManager public APIs:
      ```bash
      uv run pytest
      ```
      Expected outcome: All tests pass; delegation produces identical results

## Compatibility considerations

- Delegation adds indirection layer that could mask bugs if not tested properly — mitigated by running comprehensive regression tests after each method migration
- Constructor signature changes in TurnCoordinator could break existing callers — mitigated by preserving TurnCoordinator's external API; adding delegation wrapper methods with same signatures
- Logging standardization could alter log output format — mitigated by testing log output comparison before and after change

## Security considerations

N/A: Refactoring only, no security impact.

## Rollback considerations

Simple revert of the three method migrations and the logging standardization — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/conversation_state_manager.py | Unit test ephemeral filtering, system prompt sync, user message append | uv run pytest | All tests pass; no regression |
| scripts/agent/turnd_coordinator.py | Unit test delegation behavior matches original behavior | uv run pytest | All tests pass; delegation produces identical results |
| scripts/agent/orchestrator.py | Integration test orchestrator still works after refactoring | uv run pytest | No regression in orchestrator flow |
| scripts/agent/workflow_engine_adapter.py | Integration test adapter still works after refactoring | uv run pytest | No regression in adapter flow |

## Completion criteria

- [ ] Only ConversationStateManager contains the implementations of `clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, and `append_user_message`
- [ ] TurnCoordinator delegates all three operations to ConversationStateManager without changing its external API
- [ ] Logging usage is standardized across both classes (no mix of stdlib logging and custom Logger)

## Out of scope

- Modifying `scripts/agent/orchestrator.py` (reference file only)
- Modifying `scripts/agent/workflow_engine_adapter.py` (reference file only)
- Modifying `scripts/agent/message_schema.py` (reference file only)
- Merging the two classes into one
- Changing the EPHEMERAL_KEYS constant itself
- Modifying the first-turn background task callback mechanism

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify no callers invoke TurnCoordinator's duplicate methods | Completed | 20260914-003252 | 20260914-003252 | Check orchestrator.py, workflow_engine_adapter.py |
| 2 | Document behavioral differences between implementations | Completed | 20260914-003252 | 20260914-003252 | Comment during refactor |
| 3 | Move clear_previous_turn_ephemeral_messages to CSM + delegate | Completed | 20260914-003252 | 20260914-003252 | Extract + delegation |
| 4 | Move sync_system_prompt to CSM + delegate | Completed | 20260914-003252 | 20260914-003252 | Extract + delegation |
| 5 | Move append_user_message to CSM + delegate | Completed | 20260914-003252 | 20260914-003252 | Extract + delegation |
| 6 | Standardize logging across both classes | Completed | 20260914-003252 | 20260914-003252 | Replace custom Logger with stdlib logging |
| 7 | Run unit tests for ephemeral filtering, system prompt sync, user message append | Completed | 20260914-003253 | 20260914-003253 | uv run pytest |
| 8 | Run regression tests for both public APIs | Completed | 20260914-003253 | 20260914-003253 | uv run pytest |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-003 — consolidate duplicate conversation methods between TurnCoordinator and ConversationStateManager
- **Source issue**: issues/20260913-160708_duplicate_conversation_methods.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-200725_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-215515
- **Related target files**: scripts/agent/conversation_state_manager.py, scripts/agent/turnd_coordinator.py