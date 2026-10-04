# StartupValidationPipeline: RAG consistency check blocks thread pool

## Background

`StartupValidationPipeline.check_services()` in `scripts/agent/startup_validation.py` runs multiple validation checks sequentially. The RAG consistency check is executed in the default executor thread pool.

## Problem

`RagMaintenanceService().consistency()` is a synchronous operation run in the default executor thread pool. If this operation is slow (e.g., scanning large RAG indices), it blocks a thread in the limited thread pool. Since the default executor uses a bounded number of threads, this can stall other async operations.

Additionally, the lambda creates a new `RagMaintenanceService` instance each time, which may have side effects (opening database connections) that aren't cleaned up if the operation fails.

## Evidence

- File: `scripts/agent/startup_validation.py`
- Lines 128-145:

```python
loop = asyncio.get_running_loop()
rag_check = await loop.run_in_executor(
    None,
    lambda: RagMaintenanceService().consistency(),
)
```

## Impact

- Startup delay proportional to RAG index size
- Thread pool exhaustion under concurrent startup scenarios
- Resource leaks if `RagMaintenanceService` holds open connections on failure

## Recommended action

1. Make `RagMaintenanceService.consistency()` async and call it directly without `run_in_executor`.
2. Pass an existing `RagMaintenanceService` instance rather than creating one per call.
3. Add a timeout parameter to prevent indefinite blocking.

```python
# Option A: Async method
rag_service = RagMaintenanceService()
rag_check = await rag_service.consistency_async(timeout=30.0)

# Option B: With explicit timeout
rag_check = await asyncio.wait_for(
    loop.run_in_executor(None, rag_service.consistency),
    timeout=30.0,
)
```

## Acceptance criteria

- [ ] RAG consistency check does not block the thread pool
- [ ] Timeout enforced on the RAG check operation
- [ ] Test verifies no thread pool starvation under concurrent startup
- [ ] Test verifies timeout behavior

## Out of scope

- Changes to `RagMaintenanceService.consistency()` internal logic
- Changes to the validation pipeline order
