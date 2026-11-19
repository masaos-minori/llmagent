## Goal
- Pin the TTL baseline behavior that no existing test pins, before it is documented (REQ-006: characterization tests that change no behavior).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: three new tests in `tests/eventbus/test_authz_generation_ttl.py`.
- The restart baseline carrying no expiries is already pinned by `TestRestartBaselineAudit` (`test_startup_emits_one_authz_baseline_record` asserts empty expiries after a second startup); it is cited, not duplicated (Plan corrected in Step 3a).

## Assumptions
- The tests describe current behavior of `admin_route.py` and `authz_ttl.py`; the code is read-only here (Reference Files of the Plan).
- Test config comes from `eventbus_test_config`; the baseline mapping is built from the shared consumer and topic constants of `eventbus_helpers.py`, so the tests read a baseline pair from `eb_app.load_config()` instead of hard-coding it.
- A test that contradicts the draft behavior note exposes either a defect (stop and file an issue) or a wrong note (the ADR-013 note follows the test); behavior is never changed in this document.

## Design decisions
- Reuse `post_topics_authorization`, `injectable_clock`, `current_principals`, and `sweep_expired_authorizations`; no new helper.
- Put each test in the class that matches its subject, so existing structure is kept.

## Alternatives considered
- A new test module for the three tests: rejected, the existing module already holds the generation, sweep, restart, and hash classes and its fixtures.

## Implementation
### Target file
`tests/eventbus/test_authz_generation_ttl.py`

### Procedure
1. Add `test_ttl_expiries_do_not_change_baseline_hash` (new) to `TestBaselineHashInvariance`: grant a pair with `ttl_seconds`, assert the published generation has non-empty `expiries`, and assert its `baseline_hash` equals `authorization_baseline_hash` of a config with the same mapping and no expiries.
2. Add `test_carried_over_pair_keeps_expiry` (new) to `TestTTLExpirySweep`: grant pair A with `ttl_seconds`; post a second update that lists A and a new pair B without `ttl_seconds`; assert the new generation's `expiries` holds A's original entry unchanged and no entry for B.
3. Add `test_runtime_only_removal_is_restored_by_restart` (new) to `TestRestartBaselineAudit`: using the lifespan pattern of the existing restart test, remove a baseline pair by an admin update, re-grant it with `ttl_seconds`, advance the injected clock past expiry, run the sweep, and assert the pair is absent from the consumer principal's grants while the loaded baseline config still lists it; then open a second lifespan and assert the pair is back and the generation's `expiries` is empty.
4. Write each test first and run it against unchanged code; all three MUST pass.

### Method
- Use unique topic names per test so the assertions do not collide with the baseline pairs.
- For test 3, enter `TestClient` as a context manager twice on the same app with the patched `load_config`, as the existing restart test does; use the control-plane credential (`ADMIN_AUTH`) for the admin updates and the consumer token for the grant assertion.
- Keep the type annotations and the `-> None` returns used by the module; `tests/eventbus` is type-checked by mypy.

### Details
- If a test fails against unchanged code, stop: record the observed behavior, file an issue, and report the finding; do not change production code in this Plan.
- Report the verified behavior in the commit message so the ADR-013 note (seq 06) can cite it.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only; no token values are printed or asserted in logs.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py -v`.
- `uv run ruff format --check tests/eventbus/test_authz_generation_ttl.py` and `uv run ruff check tests/eventbus/test_authz_generation_ttl.py`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria
- Three new tests exist, pass against unchanged production code, and duplicate no existing test.
- The verified behavior of each scenario is recorded for the ADR-013 note.

## Out of Scope
- Any change to `admin_route.py`, `authz_ttl.py`, or `auth.py`.
- Tests for the owner-decision items (Plan Unknowns UNK-01 to UNK-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three characterization tests | Completed | 20261119-100257 | 20261119-100341 | Step 2 stale check clean; test file clean at baseline Changed: tests/eventbus/test_authz_generation_ttl.py (3 tests, +98 lines). Verified on unchanged code: (a) baseline hash ignores expiries; (b) carried-over pair keeps its expiry and ttl applies only to newly granted pairs; (c) sweep removes a re-granted baseline pair from runtime only and restart restores it with empty expiries. No defect found |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-100341 | 20261119-102738 | 12 passed (random and fixed order); ruff, mypy pass; full suite once at end of batch End of unit: full suite 12898 passed 7 skipped (not integration/production_paths_allowed/repo_scan); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass |

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
- **Requirement ID**: `REQ-006` (characterization tests for the TTL baseline behavior)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `tests/eventbus/test_authz_generation_ttl.py`