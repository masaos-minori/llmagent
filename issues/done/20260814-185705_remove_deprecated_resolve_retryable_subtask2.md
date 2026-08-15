# Remove deprecated LlmTransportErrorHandler.resolve_retryable (sub-task 2: cross-file consolidation)

## Background

Phase 1 of `plans/20260813-190710_plan.md` (adding DeprecationWarning) has been implemented.
This sub-task removes the deprecated method once the grace period expires.

## Sign-off channel

A maintainer must approve this sub-task via a comment on `plans/20260813-190710_plan.md` before implementation begins.

## Extraction design

A shared three-branch helper with counter-threading signature, called from `LlmReconnectHandler._evaluate_stream_error` in place of today's `LlmReconnectHandler.resolve_retryable`.

## References

- Original plan: `plans/20260813-190710_plan.md`
- Follow-up plan: `plans/20260814-154757_plan.md`
