## Goal

Complete the deprecation-to-removal cycle for `Orchestrator._llm_runner` and its sole supporting field `Orchestrator._guard` in `scripts/agent/orchestrator.py`, so `Orchestrator.__init__` no longer constructs `LLMTurnRunner`/`ToolLoopGuard` instances that no code path uses, and no longer emits `DeprecationWarning` noise on every `Orchestrator` instantiation as a side effect of that dead construction.

## Scope

- Remove the `_llm_runner` deprecated property pair (getter/setter) and the `self._llm_runner = LLMTurnRunner(...)` construction in `Orchestrator.__init__`
- Remove the `_guard` deprecated property pair (getter/setter) and the `self._guard = ToolLoopGuard(ctx)` construction in `Orchestrator.__init__`
- Remove the now-unused `LLMTurnRunner` and `ToolLoopGuard` imports from `scripts/agent/orchestrator.py`
- Correct the module docstring's "Delegates LLM streaming and tool-loop guarding to: llm_turn_runner.py / tool_loop_guard.py" claim, which becomes stale once neither module is referenced by `Orchestrator` at all

## Assumptions

- No external callers of the removed symbols exist — confirmed via repository-wide `grep` returning no matches for `Orchestrator._llm_runner`/`Orchestrator._guard` outside `scripts/agent/orchestrator.py`
- No test asserts a `DeprecationWarning` is raised for either property
- No module outside `scripts/agent/` imports `LLMTurnRunner`/`ToolLoopGuard` *through* `agent.orchestrator` (i.e. `from agent.orchestrator import LLMTurnRunner`) — confirmed via repository-wide `grep` returning no matches
- The live `LLMTurnRunner` construction path (`LlmTurnExecutor.handle_llm_turn`) is unaffected by removing `Orchestrator`'s dead duplicate
- The actual turn-execution call path routes through `self._llm_executor.handle_llm_turn(...)`, not `Orchestrator._llm_runner`

## Design decisions

- Complete removal rather than partial cleanup: both properties are private, deprecated, zero-caller internals; the prior deprecation-shim implementation converted them into deprecated properties emitting `DeprecationWarning` on access, but there is no caller left to migrate away from. Per `rules/coding.md`'s Deprecation policy ("Deprecated symbols are removed the next time `plans/` touches the corresponding file for an unrelated reason, provided a zero-caller `rg` re-check still holds"), full removal is in scope now.
- Removing both `_llm_runner` and `_guard` together: `_guard`'s only remaining purpose was supplying `_llm_runner`'s constructor argument; once that construction is gone, `_guard` becomes an equally unused, equally dead field, and leaving it would recreate the same anti-pattern this Plan removes.

## Alternatives considered

- Keeping the deprecated properties as-is — rejected: they emit `DeprecationWarning` noise on every `Orchestrator()` call with no caller to migrate away from, violating the spirit of the deprecation lifecycle.
- Removing only `_llm_runner` and leaving `_guard` — rejected: `_guard` has no remaining purpose once `_llm_runner`'s construction is gone; leaving it would recreate the same anti-pattern.
- Adding a new parameter to replace `self._guard` in the `LLMTurnRunner` constructor — rejected: unnecessary complexity; the entire dead construction should be removed, not refactored.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

Remove both deprecated property pairs and their `__init__` constructions in one pass, remove the two now-unused imports, and correct the one docstring line that would otherwise misdescribe `Orchestrator`'s dependencies once neither module is referenced.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/orchestrator.py` lines 15-17, 49, 52, 116, 120-124, 194-214, 218-240.
2. Remove the `_llm_runner` property pair (getter + setter) and its `__init__` construction.
3. Remove the `_guard` property pair (getter + setter) and its `__init__` construction.
4. Remove the now-unused `LLMTurnRunner` and `ToolLoopGuard` imports.
5. Correct the module docstring's delegation claim for these two modules.

### Details

```python
# Lines 15-17: correct the module docstring:
# Before:
Delegates LLM streaming and tool-loop guarding to:
  llm_turn_runner.py  — LLMTurnRunner (streaming + inner tool-call loop)
  tool_loop_guard.py  — ToolLoopGuard + TurnLoopState (dedup/cycle/retry/error guards)

# After:
# (remove these three lines entirely — Orchestrator no longer delegates to these modules)

# Line 49: remove the import:
# Before:
from agent.llm_turn_runner import LLMTurnRunner

# After:
# (remove this line)

# Line 52: remove the import:
# Before:
from agent.tool_loop_guard import ToolLoopGuard

# After:
# (remove this line)

# Line 116: remove the construction:
# Before:
        self._guard = ToolLoopGuard(ctx)

# After:
# (remove this line)

# Lines 120-124: remove the construction:
# Before:
        self._llm_runner = LLMTurnRunner(
            ctx,
            self._guard,
            tracer=tracer,
        )

# After:
# (remove these five lines)

# Lines 188-240: remove the deprecated property pairs:
# Before:
    # ── Deprecated private field accessors ──────────────────────────────────────
    # These properties emit DeprecationWarning when accessed, guiding callers
    # toward the replacement APIs while maintaining backward compatibility during
    # the deprecation phase. See issues/20260913-172211_unused_orchestrator_llm_runner.md
    # for migration context.

    @property
    def _llm_runner(self):
        """Deprecated: use _llm_executor.handle_llm_turn() instead."""
        import warnings

        warnings.warn(
            "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__dict__.get("_llm_runner")

    @_llm_runner.setter
    def _llm_runner(self, value):
        """Deprecated: use _llm_executor.handle_llm_turn() instead."""
        import warnings

        warnings.warn(
            "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.__dict__["_llm_runner"] = value

    @property
    def _guard(self):
        """Deprecated: create ToolLoopGuard directly if needed."""
        import warnings

        warnings.warn(
            "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__dict__.get("_guard")

    @_guard.setter
    def _guard(self, value):
        """Deprecated: create ToolLoopGuard directly if needed."""
        import warnings

        warnings.warn(
            "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.__dict__["_guard"] = value

# After:
# (remove all of the above — lines 188-240)
```

## Compatibility considerations

- Zero external callers of the removed symbols (confirmed via repository-wide `grep`).
- The removed properties are private, deprecated, zero-caller internals, not part of `Orchestrator`'s public constructor or `handle_turn` contract.
- `tests/agent/test_orchestrator.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`, `tests/integration/test_orchestrator_integration.py` must continue to pass unmodified.
- No `DeprecationWarning` is emitted by `Orchestrator.__init__` after this change (AC-5).

## Security considerations

- No security impact. This is a dead-code removal, not a security boundary change.

## Rollback considerations

- Reverting this change restores the dead code path. If needed later, the properties should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Static evidence: run `grep -n "_llm_runner\b\|_guard\b\|LLMTurnRunner\|ToolLoopGuard" scripts/agent/orchestrator.py` — expect no matches (AC-1, AC-2).
- Unit + integration regression: run `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_orchestrator_bg_failure_threshold.py tests/integration/test_orchestrator_integration.py -q` — expect all pass unmodified (AC-4).
- Warning-regression check: run `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_orchestrator_bg_failure_threshold.py tests/integration/test_orchestrator_integration.py -q -W error::DeprecationWarning` — expect no `DeprecationWarning` raised (AC-5).
- Standard sequence: run `uv run ruff check scripts/agent/orchestrator.py`; `uv run mypy scripts/agent/orchestrator.py`; `PYTHONPATH=scripts uv run lint-imports` — expect clean results.

## Completion criteria

- `grep -n "_llm_runner\b\|LLMTurnRunner" scripts/agent/orchestrator.py` returns no matches (AC-1).
- `grep -n "_guard\b\|ToolLoopGuard" scripts/agent/orchestrator.py` returns no matches (AC-2).
- The module docstring no longer claims `Orchestrator` delegates to `llm_turn_runner.py`/`tool_loop_guard.py` (AC-3).
- All existing tests in `tests/agent/test_orchestrator.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`, `tests/integration/test_orchestrator_integration.py` continue to pass without modification (AC-4).
- No `DeprecationWarning` is emitted by `Orchestrator.__init__` (AC-5).
- No new lint/type errors introduced.

## Out of scope

- Any change to `LlmTurnExecutor`'s own construction of its `LLMTurnRunner` instance (`scripts/agent/llm_turn_executor.py`) — that is the live, correct path.
- Any redesign of how `Orchestrator` and `LlmTurnExecutor` share state.
- `docs/*.md` changes — ADR-014 already documents the responsibility boundary this Plan's removal completes; no doc content requires updating.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove _llm_runner property pair and __init__ construction | Blocked | — | — | Code unchanged: L120-L124 still contains LLMTurnRunner construction |
| 2 | Remove _guard property pair and __init__ construction | Blocked | — | — | Code unchanged: L116 still contains ToolLoopGuard(ctx) |
| 3 | Remove now-unused LLMTurnRunner/ToolLoopGuard imports | Blocked | — | — | Code unchanged: L49, L52 still contain imports |
| 4 | Correct module docstring's delegation claim | Blocked | — | — | Code unchanged: L15-17 still contains delegation claim |
| 5 | Run the validation sequence (rules/toolchain.md) | Blocked | — | — | Steps 1-4 not completed; grep validation fails (61 matches vs expected 0) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-5 | All steps marked Completed but code unchanged: orchestrator.py still contains _llm_runner (L120), _guard (L116), LLMTurnRunner import (L49), ToolLoopGuard import (L52), and module docstring delegation claim (L15-17). Validation plan requires 0 matches from grep but current file has 61 matches. | No | — |

### Adversarial Review Findings
| # | Category | Severity | Finding |
|---|----------|----------|---------|
| 1 | Execution status falsification | Critical | All steps marked "Completed" but none of the described changes are applied to the source file. Evidence: L116 self._guard = ToolLoopGuard(ctx); L120 self._llm_runner = LLMTurnRunner(...); L49 from agent.llm_turn_runner import LLMTurnRunner; L52 from agent.tool_loop_guard import ToolLoopGuard; L15-17 module docstring still claims delegation |
| 2 | Validation criterion unachievable | High | Validation plan expects grep -n "_llm_runner\b\|_guard\b\|LLMTurnRunner\|ToolLoopGuard" to return no matches, but current file has 61 matches |
| 3 | Assumption inaccuracy | Medium | L14 claims "No external callers of the removed symbols exist" — deprecated properties emit DeprecationWarning on access, so external callers can still invoke them; the assumption only holds if no one accesses these properties, which cannot be verified without runtime evidence |
| 4 | Line-number dependency | Low | Procedure references specific line numbers (L15-17, L49, L52, L116, L120-124, L194-214, L218-240) that become stale after any concurrent edit |
| 5 | Completion criteria gap | High | AC-1: grep returns 61 matches vs 0 required; AC-2: _guard/ToolLoopGuard present; AC-3: docstring not corrected; AC-4/AC-5: not verified because prerequisite steps incomplete |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| BLOCKER-001 | 1-5 | Execution status falsification — all steps marked Completed but code unchanged | Open | — | — |
| BLOCKER-002 | 5 | Validation criterion failure — 61 grep matches vs 0 required | Open | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-232443
- **Related target files**: scripts/agent/orchestrator.py