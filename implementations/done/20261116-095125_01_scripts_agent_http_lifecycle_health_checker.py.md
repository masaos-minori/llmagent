## Goal

Make `HealthChecker.is_degraded_but_live` a single typed predicate that returns false, without raising, for any `/health` body that is not a JSON object carrying the boolean `true` (`REQ-001`: typed predicate; `REQ-003`: a non-object 503 keeps being polled; `REQ-004`: object body with `liveness` true stays ready-but-degraded; `REQ-005`: predicate and poll-loop tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `HealthChecker.is_degraded_but_live` in `scripts/agent/http_lifecycle_health_checker.py` (defensive parse, object check, strict boolean test, corrected docstring) and its companion test file `tests/agent/test_http_lifecycle_health_check.py`.
- Out of scope: the 503 and `liveness` protocol itself, server-side `/health` output, the polling loop's other exception handling, and `McpServerStarter.verify_health` (document `02`).

## Assumptions

- Only the boolean `true` counts as live: the only emitter in the repository writes the boolean `True` (`scripts/mcp_servers/health_response.py`) and the eventbus health route builds `liveness` from a boolean expression (re-checked with `rg`; no other `/health` producer found).
- `import json` is used only by the `except (json.JSONDecodeError, httpx.DecodingError)` clause of this predicate (re-checked with `rg`), so the import must be removed in the same change or ruff reports F401.
- Plan overlap judgment: no other Frozen Plan targets this file. `HealthChecker` is also touched by Plan `startrev006`/`startrev003` only as a reference file, not as a target.
- Test file `tests/agent/test_http_lifecycle_health_check.py` is a companion: it is a Plan row under `tests/`, only the `http_lifecycle_health_checker.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Return true only when the parsed body is a `dict` and `body.get("liveness") is True`; any other shape, including `"false"`, `"0"`, `0` and `null`, returns false.
- Catch `ValueError` (covers `json.JSONDecodeError` and `UnicodeDecodeError`) together with `httpx.DecodingError` around `resp.json()`; the predicate never raises for body shape.

## Alternatives considered

- Keeping truthiness: rejected, `"false"` and `"0"` would count as live.
- Also accepting the strings `"true"`/`"1"`: rejected as speculative; no emitter sends them.

## Implementation
### Target file
`scripts/agent/http_lifecycle_health_checker.py`

### Procedure
1. In `is_degraded_but_live`, change the parse guard to `except (ValueError, httpx.DecodingError)` returning false.
2. After the parse, return false unless `isinstance(body, dict)`; then return `body.get("liveness") is True`.
3. Correct the docstring: replace the reference to `McpServerStartupStarter.verify_health` (a class that does not exist) with `McpServerStarter.verify_health` and `McpServerStarter._verify_single_health`, state that this predicate is the only implementation of the rule, and state the strict boolean rule.
4. Remove `import json` from the module imports now that nothing else uses it.

### Method
- Keep the status check (`HTTPStatus(503)`) and the `content-type` check ahead of the parse exactly as they are.
- Keep the return annotation `bool`; do not change the call in `poll_until_ready`.

### Details
- The poll loop wraps the call in `except (httpx.HTTPError, OSError)`; after the change a non-object 503 body returns false, so the loop keeps polling until the startup timeout and ends in the existing `HttpStartupError` (`REQ-003`).

### Companion test files
- `tests/agent/test_http_lifecycle_health_check.py`
  - Procedure: write these first and confirm the non-object and `"false"` cases fail on the current code: (a) extend `test_is_degraded_but_live_branches` (or add a parametrized test) with real `httpx.Response` objects for array, string, number, `null`, malformed JSON and empty 503 bodies, all returning false without raising, and for `liveness` values `"false"`, `"0"`, `0` and `null`, all false; the object body with `liveness` true stays true; (b) in `TestHealthPollDegradedTolerance`, a poll with a non-object 503 followed by 200 ends ready; (c) a permanent non-object 503 ends in the existing timeout `HttpStartupError`, not `AttributeError`, using the file's `respx` and `HEALTH_POLL_INTERVAL_SEC` patch pattern.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q`.

## Compatibility considerations

- A server that sends a non-boolean truthy `liveness` stops counting as degraded-but-live; none exists in the repository.
- The signature and the callers (`poll_until_ready`, `McpServerStarter._verify_single_health`) are unchanged; object bodies behave as before.

## Security considerations

- The predicate parses an untrusted network response; it now treats every unexpected shape as "not live" and never raises, so a hostile or broken `/health` body cannot abort startup through an unhandled exception.

## Rollback considerations

- Revert the commit; the change is local to the predicate and its tests.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q`; the new non-object and `"false"` cases fail on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`.

## Completion criteria

- `is_degraded_but_live` returns false without raising for array, string, number, `null`, malformed and empty 503 bodies and for non-boolean `liveness`, and returns true only for a 503 JSON object with `liveness` true (`REQ-001`, AC-1).
- A poll with a non-object 503 then 200 ends ready and a permanent one ends in the timeout `HttpStartupError` (`REQ-003`, AC-3); object bodies behave as before (`REQ-004`, AC-4).
- The new tests exist and fail on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- The inline copy in `McpServerStarter.verify_health`, documentation text, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the predicate and poll-loop tests first and confirm the non-object and `"false"` cases fail (companion `tests/agent/test_http_lifecycle_health_check.py`) | Completed | 20261116-133655 | 20261116-133830 | Step 3a adversarial verification: all claims confirmed, no correction needed. Tests written first; 8 new cases fail on pre-change code (AttributeError on non-object bodies; truthy string liveness) |
| 2 | Rewrite `is_degraded_but_live`, correct its docstring and remove the unused `json` import | Completed | 20261116-133900 | 20261116-133930 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-133940 | 20261116-134330 | ruff/lint-imports/mypy/bandit(no high-med)/check_module_size/generate_reference_table/check_mock_patch_targets pass; ast-grep Not available (not installed locally); targeted 636 + full 12369 tests pass; diff-cover 100% |

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
- **Requirement ID**: `REQ-001` (typed predicate), `REQ-003` (non-object 503 keeps polling), `REQ-004` (object body stays live), `REQ-005` (tests)
- **Source issue**: issues/20261115-214907_startrev007_degraded-live-nondict-body.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220700_startrev007_degraded-live-nondict-body.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095125
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`, `tests/agent/test_http_lifecycle_health_check.py`