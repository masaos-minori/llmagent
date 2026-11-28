## Goal
- Add the publish-if-current unit tests, the admin-versus-sweep race tests, the mixed-generation test, and the service-config stability test (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tests/eventbus/test_authz_generation_ttl.py`. This file is named in the `Related Tests` of three code rows, so it keeps its own procedure instead of being a companion.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 23 unchanged, 0 changed).
- Sequencing (Step 2 overlap judgment): the admin TTL-precedence Plan (adrr001) is archived but its procedures are not yet executed; they edit `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`, and the ADR-013 Decision Detail 12. `plan_dependency_order.py` reports this Plan ready because adrr001 left `plans/`, but its procedures MUST be implemented first; re-read the target before editing. Line numbers are deliberately not cited.
- Procedures 01 to 03 are implemented first. The restart-baseline behavior is already covered by `TestRestartBaselineAudit::test_runtime_only_removal_is_restored_by_restart`; it is cited, not duplicated.
- The interleave is forced by monkeypatching the principal-map builder of each writer (`eventbus.admin_route._build_principal_map`, `eventbus.authz_ttl._build_principal_map`), as the existing abort test does; no async barrier is needed.

## Design decisions
- Reuse the module's fixtures and helpers (`gen_client`, `_require_generation`, `post_topics_authorization`, `injectable_clock`, `ADMIN_AUTH`, `CONSUMER_TOKEN`).
- Add new test classes rather than editing existing ones.

## Alternatives considered
N/A: follows the existing test style.

## Implementation
### Target file
`tests/eventbus/test_authz_generation_ttl.py`

### Procedure
1. Add a unit test class for `publish_generation_if_current` (new): with the current generation as `expected`, a built next generation is published and the function returns `True`; with a stale `expected`, nothing is published and it returns `False`.
2. Add an admin-versus-sweep race class with two tests: (a) a sweep whose builder hook performs an admin update through `post_topics_authorization` publishes nothing, writes no audit record (`eventbus.authz_ttl.log_authorization_change` patched), and the admin update stays in force; (b) an admin update whose `eventbus.admin_route._build_principal_map` hook runs `sweep_expired_authorizations` (an expiry registered and the clock advanced) returns 409 and the sweep's removal generation stays in force. Assert in both that generation numbers strictly increase without duplicates.
3. Add a mixed-generation test: after several updates and a sweep, for the in-force generation assert `principals` equals `eventbus.auth._build_principal_map(generation.config)` grants, and that this holds for the generation captured after each step.
4. Add a service-config stability test: after updates and a sweep, `eb_app.app.state.config` is the same object as before and unrelated fields (for example `port`, `db_path`, `authz_sweep_interval_seconds`) are unchanged, while `current_generation().config.consumer_authorization` reflects the update.

### Method
- Patch targets by dotted string with `monkeypatch.setattr`/`unittest.mock.patch` as in `test_sweep_aborts_on_concurrent_generation_bump`; keep `# noqa` use as in neighbouring tests only where fixtures require it.

### Details
- Use `dataclasses.replace(gen, generation=gen.generation + 100)` for a competing generation where a hook must publish one directly.

## Compatibility considerations
- Test-only addition; no production behavior depends on it.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_authz_generation_ttl.py` | Integration | `uv run pytest tests/eventbus/test_authz_generation_ttl.py -q -p no:randomly` and again with random order | New and existing tests pass |
| `tests/eventbus/test_authz_generation_ttl.py` | Static | `uv run ruff format tests/eventbus/test_authz_generation_ttl.py`, `uv run ruff check tests/eventbus/test_authz_generation_ttl.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |

## Completion criteria
- The four test groups above exist and pass; the race tests fail if either writer is switched back to an unconditional publish.

## Out of Scope
- Production code (procedures 01 to 03); the admin interleave test (procedure 02 companion); a new restart test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the unit, race, mixed-generation, and service-config stability tests in `tests/eventbus/test_authz_generation_ttl.py` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (race and unit tests), `REQ-002` (stability test), `REQ-003` (mixed-generation and race coverage)
- **Source issue**: issues/20261125-103308_adrr002_authz-publication-invariant.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172526_adrr002_authz-publication-invariant.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173946
- **Related target files**: `tests/eventbus/test_authz_generation_ttl.py`
