## Goal

Close EVENTBUS-008 in `scripts/eventbus/auth.py`: make an empty `consumer_authorization`
AND empty `topic_authorization` pair for the CONSUMER role resolve to deny-all
(`frozenset()`) instead of `None` (unrestricted), and correct the stale comment in
`require_consumer_identity()` that conflates an explicit empty set with "no restriction".

## Scope

Single file: `scripts/eventbus/auth.py`. Two changes:

- `_populate_token_maps()`: empty-mapping case for the CONSUMER role → `frozenset()`
  (deny-all) instead of `None`.
- `require_consumer_identity()`: correct the stale comment (lines 298-301) so it states
  `None`=unrestricted / `frozenset()`=deny-all. No logic change (an empty `frozenset()`
  already triggers rejection).

Everything else is out of scope (see Out of scope).

## Assumptions

- `UNK-01` is resolved to **deny-all at runtime** (`frozenset()`); startup-rejection of an
  empty mapping is the documented alternative, not adopted here.
- An explicitly empty mapping (`{}`) is distinct from a missing key (`None`): `None` stays
  a startup config error (REQ-005), `{}` becomes deny-all (REQ-001).
- `config/eventbus.toml` and `scripts/eventbus/config.py` are unchanged; the optional
  `consumer_authorization`/`topic_authorization` fields keep their `None` default.
- The ROLE-gated `prod_client` fixture passes no `consumer_id`, so deny-all does not affect
  it.

## Design decisions

- Resolve both `allowed_consumer_ids` and `allowed_topics` to `frozenset()` when both
  mappings are empty, via a single shallow branch (an `else` on the existing guard at line
  136), keeping cyclomatic complexity at or below the D(22) baseline.
- Keep `None` as the only "unrestricted" sentinel; `frozenset()` is rejected by the
  existing check in `require_consumer_identity()` (lines 302-306), so no logic change is
  needed there.
- Preserve the missing-key startup `ValueError` (lines 130-134) so empty stays distinct
  from missing.

## Alternatives considered

- **Startup-rejection of an empty mapping** (reject when `consumer_authorization`/
  `topic_authorization` is present but empty): documented alternative in the plan. Rejected
  as primary because it depends on the config schema and fails at load time rather than at
  request time. Chosen approach fails closed regardless of config-load timing.
- **Per-caller distinct allowlists**: out of scope; union-apply semantics for non-empty
  mappings are unchanged (REQ-003).

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. **Correct the stale comment (REQ-002).** In `require_consumer_identity()`, rewrite the
   comment at lines 298-301 so it states `None`=unrestricted and `frozenset()`=deny-all,
   matching the actual rejection logic at lines 302-306. Do not change the logic. Correct
   the parallel topic-access comment at lines 324-327 in lockstep: it carries the same
   now-invalid convention ("explicit empty set means no topic restriction") and leaving it
   stale next to the corrected consumer_id comment would be inconsistent.
2. **Change the empty-mapping interpretation (REQ-001, REQ-005).** In `_populate_token_maps()`,
   add a shallow branch so that when both `consumer_authorization` and `topic_authorization`
   are empty, `consumer_allowed_ids` and `consumer_allowed_topics` resolve to `frozenset()`
   instead of staying `None`. Preserve the existing `None`→startup-raise check for a missing
   key (lines 130-134).

### Method

Add an `else` to the existing guard `if consumer_authorization or topic_authorization:`
(line 136). For empty dicts (falsy) the current overwrite is skipped and the `None`
initializer survives; the `else` sets both to `frozenset()`. Keep it to one branch to bound
complexity.

### Details

- Lines 124-125 initializers stay `None`; this value is still used by the missing-key path
  (raises) and the `auth_token`/`admin_token` superuser path (unchanged).
- Line 136 guard: non-empty dicts take the existing overwrite path (union-apply), unchanged
  (REQ-003); empty dicts take the new `else` → `frozenset()`.
- `require_consumer_identity()` needs no logic edit: an empty `frozenset()` makes
  `consumer_id not in principal.allowed_consumer_ids` true, so every `consumer_id` is
  rejected (REQ-002). Only the comments at 298-301 and 324-327 are corrected.

## Compatibility considerations

- `config/eventbus.toml` and `config.py` are unchanged; keys remain optional `None`-default.
- Behavior change: deployments that currently rely on an empty mapping meaning "unrestricted"
  will now get deny-all. This is the intended fix; verify the ROLE-gated `prod_client` tests
  still pass before commit.

## Security considerations

- Security-sensitive trust-boundary change; the chosen direction is fail-closed.
- Use `frozenset()`, never `None`, for the empty-mapping case; using `None` reintroduces the
  fail-open bug.
- bandit baseline: 1 pre-existing high-confidence/low-severity finding unrelated to this
  change; expect no new findings.

## Rollback considerations

- Single-file revert (`git checkout scripts/eventbus/auth.py`) restores prior behavior.
- Reverting re-introduces the fail-open gap; treat any revert as temporary until the fix is
  redeployed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py` | Unit: empty→deny-all, non-empty→allowlist, superuser unchanged, missing→raise | `uv run pytest tests/eventbus/test_eventbus_auth.py` | All pass; new deny-all test green |
| `scripts/eventbus/auth.py` | Static: cyclomatic complexity bounded | `uv run radon cc scripts/eventbus/auth.py -s` | `_populate_token_maps` not worse than D(22) |
| `scripts/eventbus/auth.py` | Security lint | `uv run bandit -r scripts/eventbus/auth.py -c pyproject.toml` | Same pre-existing baseline (1 high/low-sev), no new findings |
| `scripts/eventbus/auth.py` | Type check | per `rules/toolchain.md` | Pass |

## Completion criteria

- Empty-mapping CONSUMER token resolves `allowed_consumer_ids`/`allowed_topics` to
  `frozenset()`; every `consumer_id` is rejected.
- Missing `consumer_authorization` (`None`) with `consumer_token` set still raises at startup.
- Non-empty mapping still restricts the CONSUMER token to the union of its allowlist.
- `auth_token`/`admin_token` superuser behavior unchanged.
- Stale comments corrected; all validation commands pass.

## Out of scope

- `auth_token`/`admin_token` superuser path (`allowed_consumer_ids=None`) — REQ-004 handled
  in the test-row document.
- Union-apply semantics for non-empty mappings.
- Other roles (`PUBLISHER`, `OPERATOR`, `MONITORING`, `ADMIN`).
- `config/eventbus.toml` / `scripts/eventbus/config.py`.
- Test additions — handled in the `tests/eventbus/test_eventbus_auth.py` document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-005
- **Source issue**: issues/20261013-161114_eballow01_require-non-empty-consumer-authorization-for-eventbus-consumer-token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-185233_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-202733
- **Related target files**: scripts/eventbus/auth.py
