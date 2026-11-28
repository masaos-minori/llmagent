## Goal
- Switch the admin writer to the generation-owned config and the publish-if-current function, so a lost race returns 409 and `app.state.config` is no longer replaced (`REQ-001` conditional publication; `REQ-002` one authority; `REQ-004` uncontended behavior unchanged).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `update_topics_authorization` in `scripts/eventbus/admin_route.py` and its companion test file.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- Procedure 01 provides `publish_generation_if_current` (new); this procedure is implemented after it.
- No `scripts/` module reads `app.state.config.consumer_authorization` at request time (consumer scan in the Plan); the handler's own `get_config(request)` read is the only one.

## Design decisions
- The base config for `dataclasses.replace` and for the no-op comparison is `current_gen.config`, so the read, the build, and the publish all concern one generation snapshot.
- On a `False` return from `publish_generation_if_current` (new) the handler returns the same 409 JSON shape as the stale-generation path: `error="generation_conflict"`, the request's `expected_generation`, and a freshly read `current_generation().generation`; nothing is audited.

## Alternatives considered
- Keep `get_config(request)` as the base and only add the compare (rejected: leaves the split authority).

## Implementation
### Target file
`scripts/eventbus/admin_route.py`

### Procedure
1. Replace `config = get_config(request)` with `config = current_gen.config`; remove the `get_config` import if it becomes unused.
2. Replace the pair `request.app.state.config = new_gen.config` and `publish_generation(new_gen)` with `if not publish_generation_if_current(current_gen, new_gen):` (new import from `eventbus.auth`) and return the 409 `JSONResponse` described above; remove the unused `publish_generation` import.
3. Remove the now-stale comments that say the handler swaps `app.state.config`, and update the docstring body (not its first line) to describe the compare-and-publish.

### Method
- Keep the audit call, success response, no-op response, and every existing 422/503/409 path exactly as they are after the admin TTL-precedence procedures; do not reorder validation.
- The audit record is emitted only after a successful publish.

### Details
- `tests/eventbus/test_admin_topics_authorization.py` imports `eventbus.admin_route._build_principal_map` via `monkeypatch`/`patch` targets (`eventbus.admin_route._build_principal_map`, `eventbus.admin_route.log_authorization_change`); keep both names importable in the module.

### Companion test files
- `tests/eventbus/test_admin_topics_authorization.py`
  - Procedure: change the assertion in `TestPublishOrder::test_effective_update_publishes_config_and_map` from `eb_app.app.state.config is not config_before` to `is config_before`, and add a forced-interleave test: monkeypatch `eventbus.admin_route._build_principal_map` with a wrapper that publishes a competing generation (`dataclasses.replace(gen, generation=gen.generation + 100)` through `eventbus.auth.publish_generation`) before returning the real map; assert the request returns 409 `generation_conflict`, `current_generation()` is the competing object, `log_authorization_change` is not called, and `app.state.config` is unchanged.
  - Validation: `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q`.

## Compatibility considerations
- Single, uncontended requests are unchanged (same response, audit, and generation numbers). The only behavior change is the 409 on a lost race, which was previously impossible to observe.

## Security considerations
- The privileged route can no longer publish over a newer generation; authentication and role checks are untouched.

## Rollback considerations
- Revert the commit; no persisted state is involved.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/admin_route.py` and companion | Integration | `uv run pytest tests/eventbus -q` | Pass |
| `scripts/eventbus/admin_route.py` | Static | `uv run ruff format scripts/eventbus/admin_route.py`, `uv run ruff check scripts/eventbus/admin_route.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -c pyproject.toml scripts/eventbus/admin_route.py` | Clean |

## Completion criteria
- The admin writer reads its base from `current_gen.config`, publishes only through `publish_generation_if_current` (new), and no longer assigns `app.state.config`; a lost race returns 409 with no audit record; existing tests pass except the one changed assertion.

## Out of Scope
- Request validation order and the metadata-only rejection (adrr001); the sweep (procedure 03); `route_helpers.py` (not changed, `get_config` stays for other routes).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch the writer to `current_gen.config` and `publish_generation_if_current` (new) in `scripts/eventbus/admin_route.py` | Pending | — | — | |
| 2 | Update and add the companion tests in `tests/eventbus/test_admin_topics_authorization.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (admin loses a race with 409), `REQ-002` (no `app.state.config` replacement), `REQ-004` (uncontended behavior unchanged)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`
