# Fix RagLLM callable type casting inconsistency

## Priority
Low

## Summary
Fix the RagLLM class where `Callable[..., object]` is cast to `RagLLM` via `__init_subclass__`, but the resulting instance doesn't actually implement the expected interface. Callers must cast the result back to `RagLLM` before calling `.get_embedding()` or `.chat()`.

## Background
In llm_client.py, RagLLM is defined as a Protocol:
```python
class RagLLM(Protocol):
    def get_embedding(self, text: str) -> EmbeddingResponse: ...
    def chat(self, messages: list[dict[str, str]]) -> ChatResponse: ...
```

The factory function returns `RagLLM` but the actual instance is a concrete class that inherits from both `RagLLM` and the protocol. However, the Protocol type annotation suggests it should be used as a type hint, not instantiated directly.

## Problem
1. Type confusion: The return type is `RagLLM` (Protocol), but the actual instance is a concrete class
2. Missing methods: Some concrete implementations may not implement both `get_embedding` and `chat`
3. Caller burden: Callers must know to cast the result back to the concrete class
4. No runtime verification: Protocol types don't enforce method existence at runtime

## Reason for Change
Clarify the type contract and ensure callers can reliably invoke the expected methods without additional casting. Either:
A) Make RagLLM a proper abstract base class (ABC) instead of Protocol
B) Document the expected behavior and add runtime checks
C) Return concrete types from factory functions

Option A recommended for cleaner API; Option C for minimal change.

## Target Files or Areas
- scripts/rag/llm_client.py

## Required Changes
- Evaluate whether RagLLM should be ABC vs Protocol
- Ensure factory functions return properly typed instances
- Add runtime checks if using Protocol

## Constraints
- Must not change the public API surface
- Must preserve backward compatibility
- Must not break existing tests

## Acceptance Criteria
- Factory functions return instances with guaranteed method availability
- Type annotations accurately reflect the returned type
- All existing tests pass after changes

## Testing Expectations
- Verify factory functions return instances with correct methods
- Run: pytest tests/rag/test_rag_llm_client.py

## Documentation Impact
Update RagLLM docstring to clarify its intended usage pattern.

## Out of Scope
- Changing the embedding/chat interfaces themselves
- Adding new LLM providers
- Implementing retry logic for LLM calls

## Dependencies
N/A: none

## Unresolved Questions
Should we add a factory registry pattern to make LLM instantiation more explicit?

## AI Implementation Instruction
1. Read scripts/rag/llm_client.py
2. Examine the RagLLM Protocol definition and factory functions
3. For Option A: convert Protocol to ABC with @abstractmethod decorators
4. For Option B: add runtime checks in factory functions
5. For Option C: return concrete types from factory functions
6. Start with Option C (minimal change) unless user requests Option A
7. Run pytest tests/rag/test_rag_llm_client.py to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/llm_client.py
