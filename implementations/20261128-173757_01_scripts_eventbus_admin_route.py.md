## Goal
- Make `POST /admin/topics/authorization` return 422 for an invalid `ttl_seconds` even when `expected_generation` is stale, reject a body without `consumer_authorization` with 422, and keep 409 only for structurally valid requests (`REQ-001` TTL precedence; `REQ-002` 409 retained; `REQ-003` metadata-only rejection; `REQ-004` rejected requests change nothing).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/eventbus/admin_route.py` (the handler `update_topics_authorization`) and its companion test file.
- Not in scope: generation publication and `app.state.config` handling (adrr002), the API reference and ADR wording (procedures 03 and 04), the 401/403 dependency `require_role`, and the audit output.

## Assumptions
- Maintainer decision recorded in the Plan (2026-11-28): a body without `consumer_authorization` MUST be rejected with 422; an explicitly present but unchanged `consumer_authorization` stays 200 with `changed=false`.
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 16 unchanged, 0 changed): the 409 return is at `scripts/eventbus/admin_route.py:125-133`, TTL validation at `:135-151`, optional `consumer_authorization` at `:101-105`.
- Overlap judgment (Step 2): `scripts/eventbus/admin_route.py` and `tests/eventbus/test_admin_topics_authorization.py` are also targets of the publication-boundary Plan (adrr002); this is a sequencing dependency, and this procedure is implemented first. Re-read the module before generating adrr002's procedures.
- The first line of the handler docstring stays unchanged so the generated reference summary does not change.

## Design decisions
- Order after the change: `require_role(Role.ADMIN)` (401/403) -> empty body 422 -> `consumer_authorization` present and valid 422 -> `expected_generation` required and plain int 422 -> no generation 503 -> `ttl_seconds` valid 422 -> generation mismatch 409 -> no-op detection and publication (unchanged).
- Extract the TTL block into a private helper so `update_topics_authorization` (radon baseline D (22)) does not grow; `consumer_authorization` becomes mandatory, which removes the `is not None` branches.

## Alternatives considered
- Validate TTL inside the existing 409 branch only (rejected: ADR-013 Decision Detail 13 requires TTL validation before the comparison is acted on).
- Keep metadata-only as a 200 no-op (rejected by the maintainer).

## Implementation
### Target file
`scripts/eventbus/admin_route.py`

### Procedure
1. Add a module-level helper `_validate_ttl_seconds` (new) that takes the raw `ttl_seconds` value and the `authz_max_ttl_seconds` bound and returns `int | float | None`, raising the same 422 `HTTPException`s with the same detail strings as today (`ttl_seconds must be a number, got <type>`; `ttl_seconds must satisfy 0 < ttl_seconds <= authz_max_ttl_seconds (<n>), got <value>`).
2. In `update_topics_authorization`, after the empty-body check, require `consumer_authorization`: if `"consumer_authorization"` is not in `body`, raise `HTTPException(status_code=422, detail="consumer_authorization is required")`; then `new_consumer_authorization = _validate_consumer_authorization(body["consumer_authorization"])`.
3. Keep the `expected_generation` required/int checks and the 503 check as they are.
4. Replace the inline TTL block with a call to `_validate_ttl_seconds` (new), passing `body.get("ttl_seconds")` and `current_gen.config.authz_max_ttl_seconds`, and move it before the generation-mismatch `JSONResponse` 409 return.
5. Because `new_consumer_authorization` is now always a dict, build `replacements = {"consumer_authorization": new_consumer_authorization}` directly and run the no-op comparison without the `is not None` guards; `changed`, `counts`, the no-op response, publication, audit record, and success response stay as they are.
6. Update the handler docstring body (not its first line) to state the new order and the metadata-only 422.

### Method
- Edit only `scripts/eventbus/admin_route.py`; do not touch `publish_generation`, `app.state.config`, or imports other than what the helper needs (no new import).
- Keep every existing detail string for existing 422 paths unchanged so current assertions on `detail` hold.

### Details
- `tests/eventbus/test_admin_topics_authorization.py` already covers `True` and `"3600"` as invalid `ttl_seconds`; the helper MUST keep rejecting booleans before the range check.
- `uv run radon cc scripts/eventbus/admin_route.py -s` MUST NOT exceed the baseline D (22) for the handler.

### Companion test files
- `tests/eventbus/test_admin_topics_authorization.py`
  - Procedure: In `TestTTLValidation`, add a parametrized test (`0`, `-1`, `86401`, `"3600"`, `True`) that posts a valid mapping with a stale `expected_generation` (`current.generation + 1`) and asserts 422, `ttl_seconds` in the detail, the same `current_generation()` object, `app.state.config` unchanged, `current_principals()` unchanged, empty expiries, and `log_authorization_change` uncalled; add a stale-generation plus valid `ttl_seconds` (`3600`) test asserting 409 with `error="generation_conflict"`; in `TestAdminGating`, add metadata-only tests (raw `admin_client.post`: `{"expected_generation": n}` and `{"expected_generation": n, "ttl_seconds": 3600}`) asserting 422, `consumer_authorization` in the detail, and the same state assertions; add a test that an unchanged explicit mapping is still 200 with `changed=false` (existing `test_response_changed_false_when_noop` already covers it: cite it, do not duplicate); add 401 and 403 precedence tests that send an invalid body (stale generation plus invalid TTL) with no token and with the consumer token and assert 401 and 403.
  - Validation: `uv run pytest tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py -q`.

## Compatibility considerations
- Public runtime contract change: a body with only `expected_generation` (optionally `ttl_seconds`) changes from 200 `changed=false` to 422. A scan of `tests/` (checked in the Plan) found no caller that sends such a body (`post_topics_authorization` callers all carry `consumer_authorization`). Response bodies of existing paths are unchanged.

## Security considerations
- Authentication (401) and role (403) run in the `require_role` dependency before the handler body, so precedence is unchanged. A stale caller can learn the TTL bound from a 422 detail; the caller is already an authenticated Admin and ADR-013 Decision Detail 13 mandates this order.

## Rollback considerations
- Revert the commit; no persisted state or schema is involved.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/admin_route.py` and companion | Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py tests/eventbus/test_eventbus_auth.py -q` | All pass |
| `scripts/eventbus/admin_route.py` | Static | `uv run ruff format scripts/eventbus/admin_route.py`, `uv run ruff check scripts/eventbus/admin_route.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -c pyproject.toml scripts/eventbus/admin_route.py` | Clean |
| `scripts/eventbus/admin_route.py` | Complexity | `uv run radon cc scripts/eventbus/admin_route.py -s` | Handler at or below D (22) |
| Generated reference | Drift | `uv run python tools/generate_reference_table.py --check` | No drift (docstring first line unchanged) |

## Completion criteria
- A stale generation with an invalid TTL returns 422; with a valid TTL returns 409 `generation_conflict` (`REQ-001`, `REQ-002`).
- A metadata-only body returns 422 and an unchanged explicit mapping returns 200 `changed=false` (`REQ-003`).
- Every rejection path leaves the generation, `app.state.config`, principals, expiries, and audit output unchanged; 401 and 403 precedence tests pass (`REQ-004`).
- Handler complexity does not exceed D (22).

## Out of Scope
- Publication atomicity, `publish_generation`, and `app.state.config` replacement (adrr002); the API reference and ADR text (procedures 03 and 04); a non-object JSON body (Plan UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder checks, add `_validate_ttl_seconds` (new) and the `consumer_authorization` requirement in `scripts/eventbus/admin_route.py` | Pending | — | — | |
| 2 | Add the companion tests in `tests/eventbus/test_admin_topics_authorization.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (TTL before generation), `REQ-002` (409 kept), `REQ-003` (metadata-only 422), `REQ-004` (rejections change nothing)
- **Source issue**: issues/20261125-103307_adrr001_admin-ttl-precedence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172318_adrr001_admin-ttl-precedence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173757
- **Related target files**: `scripts/eventbus/admin_route.py`, `tests/eventbus/test_admin_topics_authorization.py`
