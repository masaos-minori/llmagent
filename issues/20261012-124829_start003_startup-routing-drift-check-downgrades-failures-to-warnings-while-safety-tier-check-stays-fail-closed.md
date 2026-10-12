# Startup routing-drift check downgrades non-RuntimeError failures to warnings while the safety-tier check stays fail-closed

## Priority
Medium

## Summary
In `StartupValidationPipeline.check_services()`, the routing-drift block (`# 5`) catches
`RuntimeError` and routes it to `pipeline.add_fatal()`, but its trailing `except Exception`
downgrades every *other* exception type to `pipeline.add_warning()`. A crash in the drift
check that is not a `RuntimeError` is therefore treated as a non-blocking warning instead of a
fail-closed fatal. The adjacent safety-tier block (`# 5b`) correctly routes all exceptions to
`add_fatal()`. Make the drift block's fail-open/fail-closed policy explicit and consistent with
the safety-tier block rather than silently open for non-`RuntimeError` exceptions.

## Background
`startup_validation.py` implements the startup validation pipeline. Each check wraps itself in
a try/except and classifies outcomes as OK/FATAL/WARNING/SKIPPED. The routing-drift check was
written with two handlers: `except RuntimeError` → fatal, `except Exception` → warning. The
safety-tier check uses a single `except Exception` → fatal (Fail-Closed per INV-07).

## Problem
`check_routing_drift()` may raise exceptions other than `RuntimeError` (e.g. `ValueError`,
`KeyError`, `AttributeError`, or a custom domain error from a malformed config). For those, the
`except Exception` clause fires and records a **warning**, so startup proceeds even though the
drift check never produced a result. Routing drift is security-relevant: an unchecked drift
means tools can route to servers that were removed or renamed. The fail-open window covers
exactly the non-`RuntimeError` exception types.

## Reason for Change
The two adjacent checks (`# 5` drift vs `# 5b` safety tiers) disagree on how a failed check is
treated: drift is fail-open for most exceptions, safety tiers are fail-closed. Inconsistent
fail-open/fail-closed policy across security-relevant startup checks makes the pipeline's
safety posture hard to reason about and lets a broken drift check pass silently.

## Implementation Intent
Decide the intended policy for a drift-check crash and encode it explicitly:
- If a crash means "unknown result," route it to `add_fatal()` (fail-closed) to match the
  safety-tier block, unless there is a documented reason drift must stay fail-open.
- If drift must remain fail-open by design, replace the catch-all with the specific exception
  types that are safe to downgrade, and add a comment stating the fail-open decision and why
  it differs from the safety-tier block.
Do not change the `RuntimeError` → fatal mapping or the behavior for the drift's own
`RuntimeError` findings.

## Target Files or Areas
- `scripts/agent/startup_validation.py` (`check_services()`, blocks `# 5` and `# 5b`)
- `scripts/agent/services/routing_drift.py` — read only, to enumerate the exception types
  `check_routing_drift()` can raise

## Required Changes
- Narrow or reclassify the `except Exception` in the routing-drift block so a non-`RuntimeError`
  crash is not silently downgraded to a warning without an explicit documented decision.
- Add a comment stating the fail-open/fail-closed policy and its rationale.
- Keep the safety-tier block's fail-closed behavior unchanged.

## Constraints
- Do not weaken the `RuntimeError` → fatal mapping.
- Preserve the `# noqa: BLE001` intent (unexpected failures must be captured, not crash
  startup) — the question is whether "captured" means fatal or warning.
- Keep the strict/non-strict drift semantics intact.

## Acceptance Criteria
- A non-`RuntimeError` raised inside `check_routing_drift()` no longer silently becomes a
  non-blocking warning without an explicit, documented policy choice.
- The safety-tier block remains fail-closed (any exception → fatal).
- Existing startup-validation tests still pass; add a test asserting the chosen policy for a
  non-`RuntimeError` crash.

## Testing Expectations
- Add a test that patches `check_routing_drift` to raise a non-`RuntimeError` and asserts the
  pipeline outcome matches the chosen policy (fatal if fail-closed, warning if documented
  fail-open).
- Re-run `tests/agent/test_startup_validation.py` and related startup tests.
- `ruff check`, `mypy`, full suite green.

## Documentation Impact
If `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` documents the
fail-open/fail-closed policy per check, update it to reflect the drift block's final policy.

## Out of Scope
- Any change to `check_routing_drift()` internals or its findings.
- Changes to the RAG-consistency or readiness blocks.

## Dependencies
N/A: none

## Unresolved Questions
- Whether drift must remain fail-open by design (documented decision needed) or whether
  fail-closed is intended to match the safety-tier block.
- Which specific exception types `check_routing_drift()` can actually raise (confirm before
  narrowing the catch).

## AI Implementation Instruction
First confirm the exception types `check_routing_drift()` raises, then either narrow the
`except Exception` to those types or route them to `add_fatal()` to match the safety-tier
block. Add a comment stating the policy. Do not touch the `RuntimeError` mapping or the
safety-tier block.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `N/A: not filed from a Plan`
- **Source implementation procedure**: `N/A: not filed from an implementation procedure`
- **Generated at**: 20261012-124829
- **Related target files**: `scripts/agent/startup_validation.py`
