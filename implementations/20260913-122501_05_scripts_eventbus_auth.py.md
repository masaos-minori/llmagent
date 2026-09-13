## Goal
Make per-role tokens actually authorize (REQ-005): `verify_bearer_token` must accept
any configured token (shared `auth_token` or a per-role token), and `require_role`'s
`_check_role` must resolve the caller's actual role(s) from which token they
presented, instead of only checking the endpoint's own hardcoded `role` argument
against `_ROUTE_ROLE_MAP`. Also fix `require_consumer_identity`'s consumer_id
allowlist check (REQ-006, added after REQ-005's own end-to-end validation surfaced
it): a token with no `_TOKEN_CONSUMER_MAP` entry must be treated as "any consumer_id
allowed", per that map's own "Empty means any consumer_id" comment — not as "no
consumer_id allowed", which is what the current check actually does.

## Scope
Only `scripts/eventbus/auth.py`: `_populate_token_maps`, `verify_bearer_token`,
`require_role`'s inner `_check_role`, and `attach_auth_middleware`'s
`_is_authorized` helper (see Details — found during Step 3a/Step 4 re-verification
to be a second, independent gate that also only recognized `auth_token`). No change
to `_ROUTE_ROLE_MAP` (eb001, already implemented), `require_consumer_identity`
(eb004, already implemented), or `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP`'s existing
consumer/topic-allowlist semantics.

## Assumptions
- This closes the gap left by `plans/done/20260912-111042_plan.md` (`ebauth01`),
  which already scoped this exact change ("re-architect `require_role` to map
  caller's token → Role using config") but whose committed result
  (`implementations/done/20260912-144827_02_scripts_eventbus_auth_py.md`) only added
  `_populate_token_maps()`'s `auth_token`-only mapping, leaving `_check_role`
  unchanged — confirmed by reading both that archived document and current
  `scripts/eventbus/auth.py`.
- `docs/adr/ADR-013-eventbus-authentication-authorization.md` currently documents a
  single-shared-Bearer-token model only (Decision Details #1) and does not yet
  reflect per-role tokens — this is a pre-existing documentation gap this Plan's
  Step 4 (Update Documentation) will close, per the user's explicit direction to
  update the ADR alongside this code change.
- `EventBusConfig` already has `publisher_token`/`consumer_token`/`operator_token`/
  `monitoring_token`/`admin_token` fields (confirmed by reading
  `scripts/eventbus/config.py`) — this document only wires them into authorization;
  it does not add new config fields (already covered by the companion `config.py`
  document, `implementations/20260913-122501_01_scripts_eventbus_config.py.md`).

## Design decisions
Add a new module-level `_TOKEN_ROLE_MAP: dict[str, set[Role]]` (alongside the
existing `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP`), populated by
`_populate_token_maps()`:
- The shared `auth_token`, if set, maps to **every** `Role` — preserves the
  single-shared-token deployment model's existing behavior (any caller holding it
  could reach every endpoint before this change; this must not regress per this
  Plan's own Constraint "do not weaken the underlying security intent" combined with
  not breaking the existing deployment model, which the source `ebauth01` issue's own
  Constraints also required).
- `publisher_token`/`consumer_token`/`operator_token`/`monitoring_token`, if set,
  each map to their own single `Role` only (`Role.PUBLISHER`, `Role.CONSUMER`,
  `Role.OPERATOR`, `Role.MONITORING` respectively).
- `admin_token`, if set, maps to **every** `Role` (same treatment as `auth_token`) —
  the natural reading of "admin" as a superset credential, consistent with
  `EventBusConfig.__post_init__`'s per-role-token-required check already treating
  `admin_token` as an acceptable substitute for `consumer_token`/`operator_token`.

`verify_bearer_token` changes its comparison from "equals `get_auth_token(config)`"
to "is a key in `_TOKEN_ROLE_MAP`" — this accepts the shared token and every
configured per-role token uniformly, while still calling `get_auth_token(config)`
first (unchanged) to preserve the existing fail-closed 500 when `auth_token` itself
is not configured at all (REQ-005 does not touch that startup-configuration
invariant).

`require_role`'s `_check_role` adds one check before the existing
`_ROUTE_ROLE_MAP` lookup: resolve `caller_roles = _TOKEN_ROLE_MAP.get(token, set())`
and reject (403) if the endpoint's required `role` is not in `caller_roles`. The
existing `_ROUTE_ROLE_MAP` lookup (comparing the endpoint's own `role` argument
against the route's allowed-roles set) is unchanged — it remains a
defense-in-depth check that the route registration and `require_role(...)` call
site agree, independent of which caller is asking.

## Alternatives considered
- **Have `admin_token` map to no role (require explicit per-role tokens for
  everything)**: rejected — `EventBusConfig.__post_init__`'s existing "at least one
  per-role token" check already treats `admin_token` as satisfying that requirement
  alongside `consumer_token`/`operator_token`, implying it was already intended as a
  broad/superuser credential, not a narrow one.
- **Resolve caller role by looking up in `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP`
  instead of a new `_TOKEN_ROLE_MAP`**: rejected — those two maps encode
  consumer_id/topic allowlists for a token, an orthogonal concern from which
  role(s) a token has; conflating them would make a token's role implicit in
  whether it happens to have consumer/topic entries, which is fragile and unclear.
- **Move `_check_role`'s new caller-role check ahead of the whole `_ROUTE_ROLE_MAP`
  loop (reject before even checking if the path is known)**: rejected — an unknown
  route must still 403 with "Forbidden: unknown route" (existing, unchanged
  behavior, and the specific message some tests may rely on); doing the caller-role
  check first would surface "Forbidden: requires {role} role" for a caller hitting a
  wrong/unknown path with an otherwise-insufficient role, which is a less accurate
  error for that case. Checking caller role first (this document's chosen order) is
  still correct because `role not in caller_roles` is independent of which route
  matched — see Details for the exact ordering.

## Implementation
### Target file
scripts/eventbus/auth.py

### Procedure
1. Add `_TOKEN_ROLE_MAP: dict[str, set[Role]] = {}` as a new module-level dict,
   declared alongside the existing `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP`.
2. In `_populate_token_maps(config)`, add `_TOKEN_ROLE_MAP.clear()` alongside the
   existing two `.clear()` calls, then populate it per Design decisions: shared
   `auth_token` → every `Role`; each of `publisher_token`/`consumer_token`/
   `operator_token`/`monitoring_token` → its own single `Role`; `admin_token` →
   every `Role`.
3. In `verify_bearer_token`, change the comparison from `if token !=
   expected_token: ... return ""` to `if token not in _TOKEN_ROLE_MAP: ... return
   ""` — keep the preceding `get_auth_token(config)` call (and its existing 500
   on missing `auth_token`) unchanged.
4. In `require_role`'s `_check_role`, after the existing `if not token: raise 401`
   guard and before the `_ROUTE_ROLE_MAP` loop, add: resolve `caller_roles =
   _TOKEN_ROLE_MAP.get(token, set())`; if `role not in caller_roles`, log a warning
   and raise the same `403 Forbidden: requires {role} role` the existing code
   already raises for the analogous case (reuse the message, do not invent a new
   one) — then proceed to the unchanged `_ROUTE_ROLE_MAP` loop.
5. In `attach_auth_middleware`'s `_is_authorized`, after the existing exact-match
   check against `config.auth_token` fails, also accept the request if the
   presented Bearer token value is a key in `_TOKEN_ROLE_MAP` — this is the
   Step 3a-discovered second gate (see Details) that must also recognize per-role
   tokens, or no per-role-token request ever reaches `verify_bearer_token`/
   `_check_role` at all.
6. **(REQ-006)** In `require_consumer_identity`, change `if consumer_id and
   consumer_id not in _TOKEN_CONSUMER_MAP.get(token, set()): raise 403` to
   first resolve `allowed_consumers = _TOKEN_CONSUMER_MAP.get(token, set())`,
   then only raise when `consumer_id and allowed_consumers and consumer_id not in
   allowed_consumers` — an empty `allowed_consumers` (no entry, or an explicit
   empty set) now means "no consumer_id restriction for this token" per
   `_populate_token_maps()`'s own comment, matching its treatment of `auth_token`
   (which is deliberately given an empty set to mean "any consumer_id").

### Method
Two additive changes (a new dict, a new dict-population branch), three small
conditional changes (the equality check in `verify_bearer_token`, one new guard
clause in `_check_role`, one new fallback branch in `_is_authorized`), and one
narrowed-condition fix in `require_consumer_identity` (REQ-006) — no removal of
existing logic, no change to `_ROUTE_ROLE_MAP`.

### Details
- **Correction (found during Step 3a/Step 4 re-verification, not anticipated by the
  original Design decisions above):** `attach_auth_middleware`'s `_is_authorized`
  helper is a *second*, independent authentication gate that runs before any
  `Depends(require_role(...))` dependency ever executes — it rejects with 401 any
  request whose `Authorization` header does not exactly equal `f"Bearer
  {request.app.state.config.auth_token}"`, with no awareness of per-role tokens at
  all (confirmed by reading `_is_authorized` and reproducing the 401 directly against
  a `publisher_token`-authenticated request). Fixing only `verify_bearer_token`/
  `_check_role` (Procedure steps 3-4) is therefore not sufficient — a per-role-token
  request never reaches those functions in the first place. Add the equivalent
  `_TOKEN_ROLE_MAP` membership check to `_is_authorized`: after the existing exact
  `auth_token` match fails, also accept the request if the presented Bearer value is
  a key in `_TOKEN_ROLE_MAP`. This is Procedure step 5 (added below).
- Do not remove `get_auth_token(config)`'s call in `verify_bearer_token` — it still
  enforces the pre-existing fail-closed startup invariant (missing `auth_token` →
  500), which REQ-005 does not touch.
- Do not change `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP`'s own population or
  `require_consumer_identity`'s use of them — orthogonal to role resolution, out of
  scope.
- `_check_role`'s existing `_ROUTE_ROLE_MAP` loop and its own `if role not in
  allowed_roles` check stay exactly where they are, after the new caller-role check
  — both must pass for the request to succeed: the caller must actually hold the
  required role, AND the endpoint's own declared role must be one the matched route
  permits (unchanged defense-in-depth).
- Every existing test in `tests/eventbus/test_eventbus_auth.py` that authenticates
  with a per-role token (from the companion document's fixture fix,
  `implementations/20260913-122501_02_tests_eventbus_test_eventbus_auth.py.md`) is
  written assuming this document's `_TOKEN_ROLE_MAP` design — e.g.
  `TestPublishAuth` presents `publisher_token`, requires `Role.PUBLISHER` on
  `/publish`; this must resolve to `caller_roles = {Role.PUBLISHER}` and pass.

## Compatibility considerations
The shared `auth_token` continues to grant every role exactly as before (any holder
of it could reach every endpoint pre-fix; this maps it to every `Role` here,
preserving that same breadth) — no regression for the existing single-shared-token
deployment model. A per-role token is new, additive behavior: it did not previously
authenticate at all (rejected by `verify_bearer_token`'s old exact-match-only
check), so no existing caller can depend on a per-role token being rejected.

## Security considerations
This is a **security-tightening** change for any deployment that configures
per-role tokens: a `consumer_token` holder can no longer reach `/publish` (previously
impossible anyway, since a per-role token was rejected entirely) — it makes the
already-declared, but previously-inert, four-role model (ADR-013) actually
enforceable. `auth_token`/`admin_token` remain broad/superuser credentials by
design (Design decisions), which must be documented (Step 4) so operators
understand these two grant every role.

## Rollback considerations
Single-file change adding one dict and two small conditionals — revert this file's
diff to roll back. No schema, migration, or on-disk data impact. Independent of the
companion `config.py`/test-file documents' own reverts (this document's
`_TOKEN_ROLE_MAP` becomes simply unpopulated for any per-role token field that
reverts to absent, with no error).

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` and confirm every
  per-role-token-authenticated case (`TestPublishAuth`, `TestSubscribeAuth`,
  `TestDlqListAuth`, `TestReplayAuth`) passes with its own role's token, per AC-3/
  AC-4.
- Add a regression case confirming AC-4's negative direction: a `consumer_token`
  bearer calling `/publish` (or another operator/publisher-only route) is rejected
  with 403 — the existing test file has no such cross-role-rejection case for
  per-role tokens specifically (only the pre-existing `test_subscribe_as_wrong_role`,
  which uses a literal non-configured token string, not a real per-role token from
  another role).
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no regression
  elsewhere (in particular, confirm the shared-`auth_token`-only deployment path —
  e.g. `tests/eventbus/eventbus_helpers.py`'s fixture — still authorizes every role
  as before).
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `verify_bearer_token` accepts the shared `auth_token` and every configured
  per-role token; rejects any other value (REQ-005).
- `require_role`'s `_check_role` rejects a caller whose token's mapped role(s) do
  not include the endpoint's required role, even when the token is otherwise valid
  (AC-4).
- The shared `auth_token`/`admin_token` continue to authorize every role (no
  regression to the existing single-shared-token deployment model).
- All per-role-token-authenticated cases in `tests/eventbus/test_eventbus_auth.py`
  pass (AC-3, AC-4).

## Out of scope
- `_ROUTE_ROLE_MAP` itself (eb001, already implemented) and
  `require_consumer_identity`'s own consumer_id/topic allowlist logic (eb004,
  already implemented; `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP` unchanged here).
- The `_dlq_loop` shutdown/segfault issue (eb003, already implemented).
- The previously-undiscovered `_TOKEN_CONSUMER_MAP`/`require_consumer_identity`
  allowlist bug found during eb001's implementation (empty set should mean "any
  consumer_id" per its own comment, but the check rejects every consumer_id when the
  set is empty) — unrelated to role resolution, needs its own issue/plan.
- `docs/adr/ADR-013-eventbus-authentication-authorization.md`'s own update — tracked
  by this same Plan's Step 4 (Update Documentation) as a separate step, not folded
  into this code-only document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-142430 | 20260913-142430 | Added _TOKEN_ROLE_MAP + population; verify_bearer_token/_check_role/_is_authorized now recognize per-role tokens (REQ-005); fixed require_consumer_identity's consumer_id allowlist empty-set semantics (REQ-006) |
| 2 | Add or update tests per Validation plan | Completed | 20260913-142430 | 20260913-142430 | test_eventbus_auth.py 14/14 pass including new unit-level AC-4 negative test; test_eventbus_subscribe.py 1/2 pass (1 Blocked on separate _TOKEN_TOPIC_MAP bug, see new issue) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-142430 | 20260913-142430 | ruff/mypy/bandit/lint-imports/diff-cover(100%)/pre-commit all passed; full tests/eventbus/ suite diffed against pre-fix baseline: 29 pre-existing failures/errors resolved, 0 new regressions (1 known Blocked case: test_subscribe_duplicate_consumer_id_returns_409) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-142430 | 20260913-142430 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/auth.py |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260913-093422_eb002_eventbus-per-role-token-validation-incomplete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260913-094809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122501
- **Related target files**: scripts/eventbus/auth.py