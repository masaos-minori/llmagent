# Fix Sudachi tokenizer lazy loading race condition under async concurrency

## Priority
Medium

## Summary
Add thread-safe locking to _SudachiTokenizer._ensure_loaded() to prevent multiple coroutines from simultaneously initializing the Sudachi tokenizer. Under async concurrency (e.g., multiple queries processed in parallel), this can cause duplicate tokenizer loads, wasted memory, and potential initialization conflicts.

## Background
_SudachiTokenizer (repository.py:36-68) uses lazy loading: _tkn and _mode are None until first use. The check `if self._tkn is None:` at line 46 is not atomic — between the check and the assignment, another coroutine could also see _tkn as None and start loading.

## Problem
Under concurrent query processing:
1. Coroutine A checks `self._tkn is None` → True
2. Coroutine B checks `self._tkn is None` → True
3. Both create dictionaries and tokenizers simultaneously
4. One overwrites the other's instance
5. Wasted memory (two dictionary instances) and potential initialization race

While the final state is correct (one instance survives), the intermediate state is inconsistent and wastes resources.

## Reason for Change
Add asyncio.Lock to ensure only one coroutine initializes the tokenizer. Other coroutines wait and reuse the initialized instance. This eliminates resource waste and ensures deterministic initialization order.

## Implementation Intent
1. Add `self._lock: asyncio.Lock | None = None` to _SudachiTokenizer.__init__
2. In _ensure_loaded(), acquire the lock before checking _tkn again
3. Use `asyncio.Lock()` lazily (create on first acquisition attempt)
4. After acquiring, double-check `if self._tkn is None:` (double-checked locking pattern)

## Target Files or Areas
- scripts/rag/repository.py

## Required Changes
- Add asyncio import at module level
- Add `_lock: asyncio.Lock | None = None` field to _SudachiTokenizer.__init__
- Modify _ensure_loaded() to use lock for thread-safe initialization
- Ensure lock is created lazily (not in __init__) to avoid sync/async boundary issues

## Constraints
- Must not block synchronous callers (the tokenizer is used in both sync and async contexts)
- Lock creation must be lazy to avoid sync/async context issues
- Must handle the case where lock acquisition fails gracefully

## Acceptance Criteria
- Only one _SudachiTokenizer instance is created per process regardless of concurrency
- Concurrent queries share the same tokenizer instance
- No race conditions during initialization
- Existing FTS search functionality works correctly

## Testing Expectations
- Add test verifying concurrent access does not create multiple tokenizer instances
- Verify existing FTS search tests pass
- Run: pytest tests/rag/test_rag_repository.py

## Documentation Impact
Update _SudachiTokenizer docstring to note it is safe for concurrent use.

## Out of Scope
- Making the tokenizer async-aware (it remains synchronous)
- Caching the tokenizer across processes (process-level caching is out of scope)
- Adding configuration for tokenizer warm-up

## Dependencies
N/A: none

## Unresolved Questions
Should we add a process-wide singleton instead of instance-level locking? This would prevent duplicate tokenizers even across different RagPipeline instances.

## AI Implementation Instruction
1. Read scripts/rag/repository.py
2. At top of file, add `import asyncio`
3. In _SudachiTokenizer.__init__, add: `self._lock: asyncio.Lock | None = None`
4. In _ensure_loaded(), replace:
   ```python
   if self._tkn is None:
       ...
   ```
   With:
   ```python
   if self._tkn is None:
       if self._lock is None:
           self._lock = asyncio.Lock()
       # Note: asyncio.Lock cannot be acquired synchronously; 
       # callers must use await self._ensure_loaded_async() in async context
       # For sync context, keep current behavior but add comment about race condition
   ```
5. IMPORTANT: Since asyncio.Lock requires async context, consider using threading.Lock instead for sync safety. Evaluate whether the tokenizer is called from sync or async paths.
6. If sync path exists, use `threading.Lock()` instead of asyncio.Lock()
7. Run pytest tests/rag/test_rag_repository.py to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/repository.py
