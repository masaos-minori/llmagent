# Adversarial Review — `scripts/agent` REPL runtime processing (turn execution + tool-execution loop)

Reviewed head: `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9` (working tree matched HEAD, no uncommitted edits).

## Review Scope

- Reviewed (turn execution): `orchestrator.py`, `workflow_engine_adapter.py`, `llm_turn_executor.py`, `llm_turn_runner.py`.
- Reviewed (tool-execution loop): `tool_runner.py`, `tool_scheduler.py`, `tool_loop_guard.py`, `tool_policy.py`, `tool_approval.py`, `tool_preparation.py`, `tool_run_recorder.py`, `tool_round_completion.py`.
- Reviewed (persistence/boundary): `turn_persistence.py`, `session.py`, `session_message_repo.py`.
- Reviewed (state/config/runtime): `context.py`, `conversation_state_manager.py`, `bg_task_monitor.py`, `diagnostic_store.py`, `history.py`, `repl_input_loop.py`.
- Reviewed (workflow store coupling): `workflow/workflow_engine.py`, `workflow/tool_call_state_ops.py`, `workflow/state_store.py`.
- Not reviewed: non-Python assets, shell/TOML, MCP transport/dispatcher side (`scripts/mcp_servers`), RAG, tests (no new test-run phase), other top-level modules.

Working tree vs reviewed head: matched at `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | `scripts/agent/` | All checks passed (from prior phase) |
| `mypy` | 17 runtime files | No issues (from prior phase) |
| `lint-imports` | import contracts | 6 contracts kept (from prior phase) |
| `generate_reference_table.py --check` | reference table | No drift (from prior phase) |
| `bandit -ll` | 7 runtime modules | Only intentional guard assertion `llm_turn_runner.py:152` (`# noqa: B101`) |

## Overall assessment

The REPL runtime is defensively structured and well-bounded. Every cross-process
and failure boundary has an explicit containment strategy:

- Per-call tool execution converts only `Exception` into an error row so siblings
  complete; `BaseException` (e.g. `asyncio.CancelledError`) propagates unchanged
  (AC-5), leaving the `tool_call_state` row pending for stale cleanup.
- Turn persistence is all-or-nothing with compensation (`rollback_partial_turn`);
  a `ConversationPersistenceError` restores history to the turn-start snapshot.
- The tool-loop guard enforces duplicate/cycle/error-limit detection with best-effort
  drain of guard hints before every return.
- The REPL shutdown race is handled with an explicit `asyncio.wait` arbitration
  between the dispatch task and the shutdown event.
- `diagnostic_store` fails closed on redaction and enforces Fernet encryption by policy.

No fail-open security gap, no unhandled exception escape from the turn path, and no
import-contract regression were found. The findings below are quality/perf observations,
all Low.

One candidate was evaluated and rejected: "partial completions are persisted but never
resumed." `issues/done/20261031-180511_partialcount001_partial-completion-counter-dead.md`
lists "how partial text is stored, shown, or retried" explicitly under Out of Scope, so
non-recovery is by design; the partial text is surfaced inline and exported via
`session_persister`, so there is no missing consumer. Not a finding.

## Findings

### F-001 — History fallback truncation is O(N·M) worst case

- Title: `_apply_unit_drops` rebuilds the history list per dropped message.
- Severity: Low
- Confidence: High
- Evidence label: Observed
- Evidence: `history.py::_apply_unit_drops` iterates `drop_candidates` and, for each
  message in each unit, rebuilds `new_history = [x for x in new_history if x is not m]`.
- Current behavior: Dropping U units of k messages each from a history of N messages
  is O(U·k·N); when most of the history must be dropped this approaches O(N²).
- Impact: Correctness is fine and this is a fallback path (only runs when LLM-based
  compression fails). Practical risk is unconfirmed (不明) and depends on history
  size; a streaming drop (`set` of protected ids, or in-place partition) would avoid
  the repeated full-list scans. Note this is distinct from
  `issues/done/20261026-224931_history001_token-overflow-compression-fallback.md`,
  which addresses token-path fallback gating, not truncation cost.
- Recommended action: None required unless profiling shows fallback truncation on a
  hot path. Optionally replace the identity-scan rebuild with a single pass over
  protected-id membership.

### F-002 — `is_partial` audit metric conflates partial-text with compensation

- Title: `is_partial` mixes two distinct conditions.
- Severity: Low
- Confidence: High
- Evidence label: Observed
- Evidence: `orchestrator.py:196` computes
  `is_partial = bool(getattr(exc, "partial_text", "")) or compensated`.
- Current behavior: `is_partial` is True either when the exception carried partial
  text OR when the turn's partial DB rows were rolled back. These are unrelated
  conditions joined by `or`.
- Impact: The value feeds only the `partial_completion` audit metric
  (`audit_event_emitter.py`); it does not drive recovery. The conflation can report
  `partial_completion=true` for a rollback that had no partial text, slightly
  degrading the accuracy of the metric.
- Recommended action: Split the two signals (e.g. track `had_partial_text` and
  `was_compensated` separately) if the metric is used for anything beyond a count,
  otherwise leave as-is.

### F-003 — `finish()` performs async round-completion inside the BaseException/cancellation handler

- Title: Round completion runs during cancellation in `execute_all_tool_calls`.
- Severity: Low
- Confidence: High
- Evidence label: Observed
- Evidence: `tool_runner.py::execute_all_tool_calls` wraps the DAG execution in
  `except BaseException:` and calls `await finish(ROUND_NOT_COMPLETED)`
  (`complete_round`), which appends tool results and persists them, before re-raising.
- Current behavior: On a `CancelledError`, the round is still completed with async
  DB/history writes before the exception propagates.
- Impact: Extends the cancellation/shutdown window by the duration of round
  completion (best-effort persistence of what already ran — arguably desirable). A
  secondary `BaseException` raised inside `finish()` would propagate out of the
  `except Exception` guard and replace the original exception in the chain; both are
  cancellation-related so the observable outcome (turn aborted) is unchanged.
- Recommended action: None required. If a hard shutdown deadline matters, gate
  `finish()` on `not asyncio.current_task().cancelled()`.

## End-of-report

Findings sorted by severity. No Critical/High/Medium security or correctness defects
were found. All three findings are Low-quality/perf observations on non-hot paths; none
requires immediate remediation.
