# Implementation Procedure: tests/eventbus/test_eventbus_config.py

## Goal

Fix a broken import that currently prevents this file's tests from running at all, so
the `_REMOVED_CONFIG_KEYS` guard's regression coverage can actually be confirmed passing
(closing the source decision record honestly, not on an unverified claim).

## Scope

**In-Scope**
- Change `from scripts.eventbus.config import EventBusConfig, load_config` to
  `from eventbus.config import EventBusConfig, load_config`.

**Out-of-Scope**
- Any change to the test logic, assertions, or test names — the four existing tests
  (`test_load_config_rejects_stray_poll_interval_ms`,
  `test_load_config_rejects_stray_offset_checkpoint_interval`,
  `test_load_config_rejects_both_stray_keys`, `test_load_config_succeeds_without_stray_keys`)
  and any others in the file are otherwise correct as written — this is purely an
  import-path fix.
- `scripts/eventbus/config.py` — not touched by this procedure (see the companion
  `config.py` implementation procedure, which is verification-only).

## Assumptions

- **Critical finding**: this file currently fails at pytest collection with
  `ModuleNotFoundError: No module named 'scripts'` — confirmed by running
  `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_config.py -v` (and
  without `PYTHONPATH` too; both fail identically) during this review. The source plan
  (`plans/20260820-103959_plan.md`) originally claimed these tests "already pass" —
  that claim was false and has been corrected in the source plan.
- `from eventbus.config import ...` (no `scripts.` prefix) is the correct, working
  import form under this project's `PYTHONPATH=scripts` convention — confirmed two
  ways: (1) `PYTHONPATH=scripts python3 -c "from eventbus.config import EventBusConfig,
  load_config"` succeeds; (2) every other file in `tests/eventbus/` (e.g.
  `test_eventbus_dlq.py`) already uses this exact form successfully.
- This file and `tests/eventbus/test_eventbus_startup.py` are the only two files with
  the broken `from scripts.` import — confirmed via `grep -n "from scripts\."
  tests/eventbus/*.py`, which returns exactly these two matches.
- The likely origin of the defect is commit `073825b3a` ("refactor: mirror tests/
  directory structure onto scripts/ package layout"), which updated most but evidently
  not all `tests/eventbus/*.py` import lines when the `scripts/` package layout was
  introduced — not independently re-verified by `git blame` line-by-line in this
  review, but consistent with the commit's stated purpose and the fact that sibling
  files in the same directory already use the correct form.

## Design decisions

- Single-line import fix, no broader restructuring — the rest of the file (fixtures,
  test bodies, assertions) needs no change once the import resolves correctly.

## Alternatives considered

- Add a `scripts/__init__.py` to make `scripts.eventbus.config` importable instead of
  fixing this file's import — rejected: that would be a repo-wide packaging change
  affecting every module under `scripts/`, far outside this plan's narrow decision-
  closure scope, and would contradict the working convention every other test file in
  `tests/eventbus/` already follows (`PYTHONPATH=scripts` + unprefixed imports).

## Implementation

### Target file
`tests/eventbus/test_eventbus_config.py`

### Procedure
1. Locate the import line: `from scripts.eventbus.config import EventBusConfig,
   load_config`.
2. Change it to: `from eventbus.config import EventBusConfig, load_config`.
3. Run `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_config.py -v` and
   confirm all tests in the file now collect and pass.

### Method
Single-line text substitution; no other line in the file changes.

### Details
- No fixture or test-body change needed — the four (or more) existing tests already
  correctly exercise `load_config()`'s guard behavior; they were simply never able to
  run due to the import error.

## Compatibility considerations

N/A: test-only file; fixing a currently-broken import has no compatibility impact on
production code.

## Security considerations

N/A: test-only file, no security-relevant logic changed.

## Rollback considerations

- Trivially revertable: a single import-line change with no dependency on the sibling
  `test_eventbus_startup.py` fix (each file's import is independent), though both
  should land together since they share the same root cause and the source plan's
  acceptance criteria depend on both being fixed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_config.py | Unit (collection + execution) | `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_config.py -v` | All tests collect and pass (0 collection errors) |

## Out of scope

- `tests/eventbus/test_eventbus_startup.py` — covered by its own implementation
  procedure document (identical defect, same fix pattern).

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-103959_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-204057
- Related target files: tests/eventbus/test_eventbus_config.py
