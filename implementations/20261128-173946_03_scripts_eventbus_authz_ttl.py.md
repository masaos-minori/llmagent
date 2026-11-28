## Goal
- Switch the TTL sweep to the publish-if-current function and stop it replacing `app.state.config` (`REQ-001` abort-and-retry on a lost race; `REQ-002`; `REQ-004` return values and audit unchanged).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `sweep_expired_authorizations` in `scripts/eventbus/authz_ttl.py`.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- Procedure 01 provides `publish_generation_if_current` (new).
- The signature `sweep_expired_authorizations(app, clock)` stays (ten test call sites and monkeypatch targets); after the change `app` is unused inside the function, and the docstring records why.

## Design decisions
- Remove the pre-publish `current_generation() is not gen` check and the `app.state.config` assignment; publish through `publish_generation_if_current` (new) with `gen` as `expected`, and on `False` log the same abort message and return `None` before any audit record.

## Alternatives considered
- Drop the `app` parameter (rejected: breaks ten call sites and two monkeypatch targets; a separate Issue if wanted).

## Implementation
### Target file
`scripts/eventbus/authz_ttl.py`

### Procedure
1. Import `publish_generation_if_current` (new) from `eventbus.auth` and drop the `publish_generation` import if unused.
2. In `sweep_expired_authorizations`, delete the early `if current_generation() is not gen:` block; after building `new_gen`, replace `app.state.config = new_gen.config` and `publish_generation(new_gen)` with `if not publish_generation_if_current(gen, new_gen):` that logs `authz_sweep: generation bumped by a concurrent update; aborting cycle` and returns `None`.
3. Keep the counts computation, the `log_authorization_change` call, the info log, and the return value unchanged.

### Method
- Keep `authz_sweep_loop` unchanged (it still reads `authz_sweep_interval_seconds` through `app_get_config`).
- Update the docstring: compare-and-swap happens inside the publish function; `app` is kept for signature compatibility.

### Details
- `tests/eventbus/test_authz_generation_ttl.py::TestTTLExpirySweep::test_sweep_aborts_on_concurrent_generation_bump` publishes a different `AuthzGeneration` object during the build; the identity compare still aborts, so the test keeps passing unchanged.

## Compatibility considerations
- Return values, audit records, and log lines of an uncontended sweep are unchanged; the abort log line text is kept.

## Security considerations
- N/A: no credential handling; the sweep can no longer overwrite a newer generation.

## Rollback considerations
- Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/authz_ttl.py` | Integration | `uv run pytest tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_health.py -q` | Pass |
| `scripts/eventbus/authz_ttl.py` | Static and complexity | `uv run ruff check scripts/eventbus/authz_ttl.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -c pyproject.toml scripts/eventbus/authz_ttl.py`, `uv run radon cc scripts/eventbus/authz_ttl.py -s` | Clean; `sweep_expired_authorizations` at or below C (13) |

## Completion criteria
- The sweep publishes only through `publish_generation_if_current` (new), never assigns `app.state.config`, and returns `None` without an audit record when it loses a race; existing sweep tests pass unchanged.

## Out of Scope
- The admin writer (procedure 02); the sweep loop; removing the `app` parameter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch the sweep to `publish_generation_if_current` (new) in `scripts/eventbus/authz_ttl.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan (owned by procedure 05) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (sweep aborts on a lost race), `REQ-002` (no `app.state.config` replacement), `REQ-004` (sweep behavior unchanged)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `scripts/eventbus/authz_ttl.py`
