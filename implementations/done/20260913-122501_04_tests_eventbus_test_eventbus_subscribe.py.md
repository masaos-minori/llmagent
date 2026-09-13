## Goal
Fix `tests/eventbus/test_eventbus_subscribe.py`'s `client` fixture (REQ-004) so it
constructs a valid `EventBusConfig` — it currently passes `auth_token=None`, which
`EventBusConfig.__post_init__` already rejects today (independent of this Plan's
`UNK-01` change), causing `test_health_ok` and
`test_subscribe_duplicate_consumer_id_returns_409` to fail at fixture setup.

## Scope
Only the `client` fixture in `tests/eventbus/test_eventbus_subscribe.py`. No change to
`scripts/eventbus/config.py` (covered by the companion `config.py` document) or any
other test file.

## Assumptions
- `EventBusConfig.__post_init__`'s existing `if not self.auth_token: raise
  ValueError(...)` check (confirmed by reading `scripts/eventbus/config.py`) is
  unchanged by this Plan (REQ-001/UNK-01 only add a per-role-token check; they do not
  relax the pre-existing `auth_token` requirement) — so `auth_token=None` fails today,
  before and independent of the companion `config.py` document's own change.
- The fixture already sets `consumer_token="consumer-token"`, `operator_token=
  "operator-token"`, and `admin_token="admin-token"` (confirmed by reading the
  fixture) — so the companion `config.py` document's new "at least one per-role
  token" `__post_init__` check is already satisfied here; only `auth_token` needs a
  real value.

## Design decisions
Change `auth_token=None` to `auth_token="shared-token"` (a value distinct from the
three per-role tokens already present, to make it visually clear in the fixture that
this is a separate credential slot, not one of the per-role tokens) and remove the
now-inaccurate `# No shared token — using per-role tokens only` comment — the
fixture cannot actually omit a shared token today (`auth_token` is unconditionally
required by `__post_init__`), so the comment describes an intent the current code
does not support; correcting the value without correcting the comment would leave a
misleading trace of that same confusion for the next reader.

## Alternatives considered
- **Leave the comment and instead relax `EventBusConfig.__post_init__`'s `auth_token`
  requirement to allow per-role-tokens-only configs**: rejected — out of scope for
  this Plan (REQ-001/UNK-01 concern the per-role-token check only; relaxing the
  pre-existing, unrelated `auth_token` requirement is a separate design decision
  with its own security implications, not requested by any Requirement here).

## Implementation
### Target file
tests/eventbus/test_eventbus_subscribe.py

### Procedure
1. In the `client` fixture (`EventBusConfig(...)` call), change `auth_token=None,  #
   No shared token — using per-role tokens only` to `auth_token="shared-token",`
   (drop the now-inaccurate comment).

### Method
Single-line value change plus a comment removal; no other line in this fixture
changes.

### Details
- Do not change `consumer_token`/`operator_token`/`admin_token` — already valid.
- Do not change the `client.headers["Authorization"] = "Bearer consumer-token"` line
  — tests in this file authenticate as a consumer via `consumer_token`, which is
  unaffected by the `auth_token` fix.

## Compatibility considerations
Test-only file; no production code or API-contract impact.

## Security considerations
N/A: test-only change; no production authorization logic modified.

## Rollback considerations
Single-line change in one file — revert to roll back. No interaction with the
companion `config.py` document's own revert.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_subscribe.py -v` and confirm
  `test_health_ok` passes.
  **Correction (found during Step 3a/Step 4 re-verification):**
  `test_subscribe_duplicate_consumer_id_returns_409` still fails after this
  fixture's own fix and after the companion `auth.py` document's REQ-005/REQ-006
  changes land — its `client` fixture's `consumer_token` has no `_TOKEN_TOPIC_MAP`
  entry, and `require_consumer_identity` returns `{"topics": set()}` for that case,
  which `subscribe_route.py` (outside this Plan's `Implementation Target Files`)
  then interprets as "no topic is allowed" rather than "no topic restriction" — the
  same class of empty-set-meaning bug REQ-006 fixed for `_TOKEN_CONSUMER_MAP`, but
  this one also requires changing `subscribe_route.py`'s interpretation, which is
  out of scope for this Plan (see this Plan's Blocker Log). This one test is
  therefore `Blocked`, not fixed by this document — tracked by a new issue instead
  of expanding this Plan a third time, per explicit user direction.
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no new regression
  beyond the one already-`Blocked` case above.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- The `client` fixture constructs `EventBusConfig` without raising.
- `test_health_ok` passes (AC-2).
- `test_subscribe_duplicate_consumer_id_returns_409` remains `Blocked` on a
  distinct, out-of-scope bug (see Validation plan Correction) — not a completion
  criterion for this document.

## Out of scope
- `scripts/eventbus/config.py`'s own validation logic (companion document).
- `tests/eventbus/test_eventbus_auth.py` and
  `tests/eventbus/test_eventbus_config.py`'s own fixtures — each has its own
  target-file document in this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-142413 | 20260913-142413 | Fixed auth_token=None to a real shared-token value; per-role tokens already valid |
| 2 | Add or update tests per Validation plan | Completed | 20260913-142413 | 20260913-142413 | test_health_ok passes; test_subscribe_duplicate_consumer_id_returns_409 remains Blocked on a distinct, out-of-scope _TOKEN_TOPIC_MAP/subscribe_route.py bug (see Blocker Log / new issue) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-142413 | 20260913-142413 | ruff/mypy/pre-commit all passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-142413 | 20260913-142413 | N/A: test-only file |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260913-093422_eb002_eventbus-per-role-token-validation-incomplete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122501
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py