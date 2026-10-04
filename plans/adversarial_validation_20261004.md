# Adversarial Validation Report — Plans 20261004-1*

Generated: 2026-10-04
Scope: All 13 plans matching `plans/20261004-1*_plan.md`

---

## Plan 1 (EventBus out-of-order ACK)

### CRITICAL: SQL query inconsistency
The plan mentions LEFT JOIN in one place but the SQL query at Design section uses `JOIN`. These are inconsistent — the LEFT JOIN is necessary because events with NO `consumer_delivery` record must be treated as unacked. The `JOIN` version would silently exclude such events.

**Fix**: Replace `JOIN consumer_delivery cd ON e.event_id = cd.event_id` with `LEFT JOIN consumer_delivery cd ON e.event_id = cd.event_id AND cd.consumer_id = ?` in the Design section SQL query (lines 297-302).

### MEDIUM: `since_seq` parameter not fully addressed
The existing adversarial validation finding correctly notes that `since_seq` (from Last-Event-ID header) is the primary resume position, not just the consumer offset. The fix should compute `resume_position = max(since_seq, lowest_unacked_seq)` rather than replacing the entire resume position logic.

**Fix**: Update Implementation Steps Step 3 to clarify that `get_resume_position` should accept `since_seq` as a parameter and compute `max(since_seq, lowest_unacked_seq)`.

### LOW: Index naming misleading
Index name `idx_consumer_delivery_unacked` suggests it indexes only unacked rows, but it indexes ALL rows. Better name: `idx_consumer_delivery_consumer_ack`.

---

## Plan 2 (retry_once_with_delay exception type preservation)

### MEDIUM: Secret masking context lost
The plan proposes changing `raise RuntimeError(masked_msg) from retry_err` to `raise retry_err`. But this loses the masked message context! The original code masks secrets before raising. If we just raise `retry_err`, the secret masking is lost.

**Fix**: Change to `raise retry_err from None` after logging the masked message, or keep the masking but change the exception type: `raise retry_err.__class__(masked_msg) from retry_err`.

### LOW: `TimeoutError` class hierarchy
The assumption that `TimeoutError` is a subclass of `OSError` is incorrect — `TimeoutError` is a subclass of `BaseException` in Python 3.x. The existing `except (OSError, RuntimeError)` in `startup_mcp_starter.py` would NOT catch `TimeoutError` on first attempt.

---

## Plan 3 (ShutdownCoordinator tracking data cleanup)

### MEDIUM: Contradictory step description
Step 1 says "Move `remove_process_entry()` and `cleanup_server_key()` inside the try block" but the actual proposal keeps `remove_process_entry()` outside the try block. This is contradictory.

**Fix**: Clarify Step 1: "Keep `remove_process_entry()` before the try block; move `cleanup_server_key()` inside the try block."

### LOW: Cross-plan conflict note valid
Plans 3, 6, 13 all propose creating `tests/agent/test_http_lifecycle.py`. Consolidation needed.

---

## Plan 4 (ProcessTerminator SIGKILL escalation failures)

### CORRECT: Only ProcessLookupError caught
Verified: line 161 catches only `ProcessLookupError`. Other `OSError` subclasses like `PermissionError` would propagate.

### MEDIUM: Post-SIGKILL verification removal
The plan removes the `else` clause with `wait_exited()` which was already identified as unnecessary. However, there's no post-SIGKILL verification at all — if `os.killpg()` succeeds but the process doesn't exit (e.g., due to kernel-level issues), the caller won't know.

**Fix**: Add a brief `await asyncio.sleep(0.1)` after successful SIGKILL to allow the OS to process the signal, then optionally check `proc.poll()` in the caller.

---

## Plan 5 (ResourceShutdownCoordinator selective task cancellation)

### CRITICAL: UNK-03 is NOT blocking
The plan marks UNK-03 ("Is `self._ctx.turn` an accessible attribute?") as Blocking=True. Verified: `ResourceShutdownCoordinator.__init__` receives `ctx: AgentContext`, and `AgentContext` has a `turn` attribute of type `TurnState`. So `self._ctx.turn` IS accessible.

**Fix**: Change UNK-03 Blocking from True to False.

### MEDIUM: background_tasks may be empty during shutdown
`TurnState.background_tasks` is populated by `Orchestrator` during turn execution. During shutdown, the Orchestrator may no longer be running, so `background_tasks` might be empty even though there are pending tasks. This means the fix could cancel FEWER tasks than intended.

**Fix**: Consider keeping `asyncio.all_tasks(loop)` as a fallback when `turn.background_tasks` is empty, or document this limitation.

---

## Plan 6 (HttpServerLifecycleManager getpgid failure handling)

### CORRECT: finally block always removes tracking entries
Verified: lines 340-346 show the `finally` block ALWAYS removes tracking entries regardless of whether termination succeeded.

### MEDIUM: Boolean flag approach is correct
The plan's proposed change uses a boolean flag `termination_succeeded` instead of checking `'term_err' in locals()`. This is an improvement over the original plan's approach.

### LOW: Poll result check after termination
Line 332 checks `poll_result = proc.poll()` AFTER termination attempt. However, this check only logs the exit code — it doesn't prevent tracking entry removal if termination fails silently.

---

## Plan 7 (AgentContext traceback preservation)

### CORRECT: from None suppresses traceback
Verified: line 313 shows `from None` suppressing the original traceback.

### MEDIUM: Simpler approach exists
The plan proposes changing `from None` to `from e`. But since `e` is already bound in the except clause, `from e` is equivalent to implicit chaining. The simpler approach would be to just remove `from None` entirely.

**Fix**: Replace `from None` with nothing (implicit chaining is the default in Python 3).

---

## Plan 8 (StartupValidationPipeline RAG timeout)

### MEDIUM: Resource leak assumption is INCORRECT
The plan assumes `RagMaintenanceService` holds a SQLite connection that should be closed after use. But looking at the source, `consistency()` uses a context manager (`with SQLiteHelper("rag").open()`) that automatically closes the connection. There's NO resource leak from the instance creation itself.

**Fix**: Remove the assumption about resource leaks. The main value of extracting `RagMaintenanceService()` outside the lambda is for testability, not resource management.

### MEDIUM: Instance reuse doesn't solve the real problem
Extracting `RagMaintenanceService()` outside the lambda doesn't solve any real problem since the service uses a context manager. The main value is the timeout addition.

---

## Plan 9 (SignalHandler Windows ctypes fallback)

### CORRECT: Silent failure without pywin32 verified
Verified: when pywin32 import fails, only a warning is logged and no handler is registered.

### MEDIUM: CTRL_CLOSE_EVENT constant
According to Windows API documentation, `CTRL_CLOSE_EVENT` is indeed 0. However, `CTRL_LOGOFF_EVENT` is also 0 on some systems. The more reliable approach is to define the constant explicitly.

**Fix**: Define `CTRL_CLOSE_EVENT = 0` explicitly rather than using magic number 0.

---

## Plan 10 (ApprovalRecovery pending_approval_task_id)

### CRITICAL: Function signature mismatch
The plan proposes calling `find_all_pending_approvals(store.get_connection(), task_id=ctx.turn.pending_approval_task_id)`. But the actual function signature is `find_all_pending_approvals(db: SQLiteHelper)` — it takes only ONE argument. The second keyword argument doesn't exist.

**Fix**: Implement a separate query to check if the current approval record still exists:
```python
current_exists = store.get_connection().fetchone(
    "SELECT COUNT(*) FROM approvals WHERE approval_id = ?",
    (ctx.turn.pending_approval_id,),
)
if current_exists and current_exists[0] > 0:
    # Active approval — preserve it
    ...
```

### LOW: Approval ID vs Task ID confusion
The plan uses `task_id` for the DB lookup but the current code uses `approval_id`. The lookup should be against `approval_id`, not `task_id`.

---

## Plan 11 (AppServices constructor validation)

### CORRECT: No validation of required params verified
Verified: `AppServices.__init__()` accepts all parameters without validation.

### MEDIUM: memory parameter classification
The docstring says `memory` can be None (intentionally absent), while `http`, `llm`, `tools`, `lifecycle`, `hist_mgr`, `audit_logger` are required. The plan correctly identifies these.

### LOW: health_registry, gateway, runtime_tools have defaults
These three parameters have default values of None, making them optional.

---

## Plan 12 (AppServices invariant vs null checks)

### CORRECT: Inconsistency between docstring and implementation verified
Verified: docstring claims "All required services are non-None" but defensive null checks exist in `startup_reporter.py`.

### MEDIUM: Option A depends on Plan 11
Plan 12 recommends Option A (enforce invariant + remove null checks). But this requires Plan 11 to be applied first. Without Plan 11, enforcing the invariant at construction time would require duplicating validation logic.

**Fix**: Document the dependency clearly and consider Option B as the immediate action.

---

## Plan 13 (StartupOrchestrator remediation steps)

### MEDIUM: Error message format change risk
The plan proposes iterating over `pipeline.outcomes` instead of using `fatal_messages()`. But this changes the error message format significantly (newline-separated instead of "; " separated). This could break external tooling that parses the error message.

**Fix**: Keep the "; " separator for backward compatibility, but append remediation info inline:
```python
for o in pipeline.outcomes:
    if o.status == StartupCheckStatus.FATAL:
        part = o.message
        if o.remediation:
            part += f"; Remediation: {o.remediation}"
        fatal_parts.append(part)
fatal_str = "; ".join(fatal_parts)
```

### LOW: Display format inconsistency
The plan correctly identifies the inconsistency between error message and display format.
