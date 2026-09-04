## Goal
Remove `retry_once_with_delay()`'s `production_mode` parameter and its
`non_fatal_prefix`/`view`-driven warning branch, making the second-failure
outcome unconditionally a raised `RuntimeError`.

## Scope
- **In-Scope**: `scripts/agent/shared/retry_helper.py`'s
  `retry_once_with_delay()` function signature and body only.
- **Out-of-Scope**: `_interruptible_sleep()` and `_mask_secrets()` (helper
  functions this file also defines, confirmed by direct read to contain no
  `production_mode`/`security_profile` reference); `CLIView`'s own
  `write_warning()` method (not modified, simply no longer called from here).

## Assumptions
- Coupled to row 8 (`startup_mcp_starter.py`), the only current caller of
  `retry_once_with_delay()` (confirmed via `rg -rn "retry_once_with_delay"
  scripts/` — 2 call sites, both in that file; re-verify at execution time).

## Design decisions
- Note the existing code already `raise`s in *both* branches (production and
  non-production) — the only behavioral difference today is exception type
  (`RuntimeError` with a masked, prefixed message vs. the original
  `retry_err`) and whether a warning is logged/displayed first. Removing the
  conditional means every second-failure case now raises `RuntimeError` with
  the `fatal_prefix`-prefixed, masked message — the same exception shape the
  production path already produces, not a new one.
- Remove the `view` parameter along with `non_fatal_prefix` — `view` is used
  exclusively inside the now-deleted non-fatal branch
  (`view.write_warning(...)`); leaving an unused parameter would be a
  Pythonic-safety-constraint violation (no dead code/placeholders).

## Alternatives considered
- Keeping `view`/`non_fatal_prefix` as unused, ignored parameters for
  backward signature compatibility: rejected — this repository's own
  Constraints (REQ-009's "no silent compatibility alias" applied by analogy)
  and `skills/DESIGN.md` Pythonic safety constraints both favor removing dead
  parameters over retaining them unused; row 8 (the sole caller) is being
  edited in the same Plan execution anyway.

## Implementation
### Target file
`scripts/agent/shared/retry_helper.py`

### Procedure
1. Remove `production_mode: bool`, `non_fatal_prefix: str`, and
   `view: CLIView | None = None` from `retry_once_with_delay()`'s signature.
2. Replace the `except Exception as retry_err:` block's `if production_mode:
   ... else: ...` branching with the unconditional (former production-mode)
   behavior: always build `masked_msg` from `fatal_prefix`, log as error, and
   `raise RuntimeError(masked_msg) from retry_err`.
3. Update the docstring's "On second failure" bullet list to describe only
   the single remaining behavior.
4. Remove the now-unused `TYPE_CHECKING`/`CLIView` import if no other
   reference to `CLIView` remains in this file (re-check via `rg -n
   "CLIView" scripts/agent/shared/retry_helper.py` at execution time).

### Method
Direct `Edit`, anchored on the exact function signature and body (verified
2026-09-04, lines 20-71).

### Details
Current (verified 2026-09-04):
```python
async def retry_once_with_delay[T](
    fn: Callable[..., Awaitable[T]],
    delay: float,
    shutdown_event: asyncio.Event | None,
    interrupt_msg: str,
    *,
    production_mode: bool,
    fatal_prefix: str,
    non_fatal_prefix: str,
    view: CLIView | None = None,
) -> T:
    ...
    try:
        return await fn()
    except Exception as retry_err:
        if production_mode:
            msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
            masked_msg = _mask_secrets(msg)
            logger.error(masked_msg)
            raise RuntimeError(masked_msg) from retry_err
        logger.warning("%s %s", non_fatal_prefix, _mask_secrets(str(retry_err)))
        if view is not None:
            view.write_warning(f"{non_fatal_prefix} {_mask_secrets(str(retry_err))}")
        raise  # Re-raise so caller can decide what to do
```
After:
```python
async def retry_once_with_delay[T](
    fn: Callable[..., Awaitable[T]],
    delay: float,
    shutdown_event: asyncio.Event | None,
    interrupt_msg: str,
    *,
    fatal_prefix: str,
) -> T:
    ...
    try:
        return await fn()
    except Exception as retry_err:
        msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
        masked_msg = _mask_secrets(msg)
        logger.error(masked_msg)
        raise RuntimeError(masked_msg) from retry_err
```

## Compatibility considerations
Coupled to row 8, the sole caller — both of its call sites must drop the
`production_mode=`, `non_fatal_prefix=`, and `view=` keyword arguments in the
same overall Plan execution or they will raise `TypeError` for unexpected
keyword arguments.

## Security considerations
None directly — removes a relaxed-retry-failure path; net effect is a
security/reliability hardening (every retry failure now surfaces as a fatal
error, never silently downgraded to a warning).

## Rollback considerations
Small, localized function edit under version control; revert via `git
revert` if needed, together with row 8.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/shared/retry_helper.py` | Unit + Integration | `uv run pytest tests/agent/test_startup.py -v` | `retry_once_with_delay()` always raises `RuntimeError` with the `fatal_prefix`-prefixed message on second failure, regardless of any argument |

## Completion criteria
`retry_once_with_delay()` has no `production_mode`/`non_fatal_prefix`/`view`
parameter; its second-failure path unconditionally raises `RuntimeError`.

## Out of scope
`_interruptible_sleep()`, `_mask_secrets()`; `CLIView.write_warning()`'s own
implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Also removed the now-unused `TYPE_CHECKING`/`CLIView` import; implemented together with row 8 |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 22's own edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: confirmed via `docs/00_index.md`'s Document References by Task table during code-implementation Step 5 — the only `mcp_config.py`-matching row covers `TransportType`/`StartupMode`/`HealthcheckMode`, not `SecurityProfile`; no changed file in this cycle has a matching task-scope row |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/shared/retry_helper.py
