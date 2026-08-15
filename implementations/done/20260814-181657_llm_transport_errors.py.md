# Implementation Procedure: Add Removal-Trigger Comment to llm_transport_errors.py

## Goal

Add a removal-trigger comment near the `warnings.warn` call in `LlmTransportErrorHandler.resolve_retryable()` specifying the removal trigger. This ensures the deprecation follows through to removal within a predictable timeframe.

## Scope

### In-Scope
- Add a removal-trigger comment near the `warnings.warn` call in `scripts/shared/llm_transport_errors.py`.

### Out-of-Scope
- Adding the `DeprecationWarning` itself (covered by `requires/done/20260813-172533_require.md`; **NOT yet implemented** — `plans/20260813-190710_plan.md` is pending).
- Removing `LlmTransportErrorHandler.resolve_retryable()` (follow-up work after the grace period).
- Any change to `LlmReconnectHandler.resolve_retryable()` or its callers.
- Any change to `LlmSseStreamHandler.stream_once()` or heartbeat/retry constants.
- Updating `rules/coding.md` with the deprecation policy — handled in Phase 2 of this plan.
- Creating a follow-up issue — handled in Phase 2 of this plan.

## Assumptions

- The zero-production-caller status for `LlmTransportErrorHandler.resolve_retryable` confirmed via `rg` on 2026-08-14 still holds at implementation time.
- No repo-wide policy currently defines a standard deprecation-to-removal interval (verified: `rules/coding.md` contains no such policy).
- The recommended approach — repo-wide default ("deprecated symbols are removed the next time `plans/` touches the same file for an unrelated reason, provided a zero-caller `rg` re-check still holds") — is acceptable to maintainers.

## Design decisions

- Place the removal-trigger comment immediately before the `warnings.warn` call, following the convention of documenting deprecation lifecycle alongside the deprecation warning itself.
- Use English-only comments consistent with the project's coding conventions.
- The comment text is concise and actionable, specifying exactly when the method should be removed.

## Alternatives considered

- **Separate docstring annotation**: Could add the removal trigger to the method's docstring, but the requirement explicitly specifies placing it near the `warnings.warn` call.
- **Inline comment after the warning**: Could place the comment after the `warnings.warn` call, but placing it before makes the removal trigger more visible during code review.
- **Python `@deprecated` decorator**: Could use a third-party decorator like `deprecated`, but the project uses simple `warnings.warn` calls without external dependencies.

## Implementation

### Target file

`scripts/shared/llm_transport_errors.py`

### Procedure

1. Open `scripts/shared/llm_transport_errors.py` and locate the `resolve_retryable` method (lines 61-82).
2. Find the `warnings.warn` call at lines 72-77.
3. Insert a removal-trigger comment immediately before the `warnings.warn` call (before line 72).
4. The comment should appear as:

```python
        # Remove this method the next time plans/ touches this file for an unrelated reason,
        # provided a zero-caller rg check still holds.
        warnings.warn(
            "LlmTransportErrorHandler.resolve_retryable is deprecated and unused in "
            "production; use LlmReconnectHandler.resolve_retryable instead.",
            DeprecationWarning,
            stacklevel=2,
        )
```

5. Verify the comment text is accurate by running `rg "resolve_retryable" scripts/ tests/` one final time before committing.

### Method

The removal-trigger comment serves as a human-readable reminder for future contributors who encounter this method. It specifies two conditions that must both hold before the method can be safely removed:
1. A `plans/` entry has touched this file for an unrelated reason (indicating natural maintenance opportunity).
2. A zero-caller `rg` re-check still holds (confirming no new callers have appeared since the deprecation was added).

This approach avoids arbitrary time-based deadlines and ties removal to natural maintenance opportunities, consistent with the repo's existing practice of using `plans/` entries as implementation tracking artifacts.

### Details

- The comment spans two lines to keep each line under 120 characters (consistent with the project's max line length rule).
- The comment uses lowercase "rg" (not "RG") to match the project's convention of using lowercase tool names in comments.
- The comment does not include a specific date or version number, relying on the `plans/`-based approach instead.
- The comment is placed immediately before the `warnings.warn` call, making it visually associated with the deprecation warning.

## Compatibility considerations

- The comment is a documentation-only addition. It does not modify any source code logic or signatures.
- The comment will only affect future contributors who read the source file; it does not change runtime behavior.
- If the sibling fix (`plans/20260813-190710_plan.md`) has not been implemented, the `warnings.warn` call may not exist yet, and the comment should be deferred until then.

## Security considerations

- N/A — this is a documentation-only change that adds a comment. No security-sensitive operations are introduced.

## Rollback considerations

- To rollback: remove the added comment block from `scripts/shared/llm_transport_errors.py`.
- No data loss risk — the change is purely documentary.
- If the sibling fix (`plans/20260813-190710_plan.md`) has not been implemented, rolling back the comment is necessary to avoid leaving orphaned documentation.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/llm_transport_errors.py` | Static — lint/format | `uv run ruff check scripts/shared/llm_transport_errors.py`; `uv run ruff format scripts/shared/llm_transport_errors.py` | No new lint errors; formatting applied correctly |
| Zero-caller re-check | Verification | `rg "resolve_retryable" scripts/ tests/` | Only test calls remain; no new production callers |

## Out of scope

- Updating `rules/coding.md` with the deprecation policy — handled in Phase 2 of this plan.
- Creating a follow-up issue — handled in Phase 2 of this plan.
- Adding `types-GitPython` stub package.
- Changing exception handling logic in any source file.
- Any change to runtime behavior, log messages, or the `RepoInfoResult`/`GitServiceError` contracts.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260813-190848_unknowns.md
- Source requirement: requires/done/20260814-133541_require.md
- Source plan: plans/20260814-154540_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-181657
- Related target files: scripts/shared/llm_transport_errors.py
