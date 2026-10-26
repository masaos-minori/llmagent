## Goal

Make `_populate_token_maps()` reject duplicate non-empty token values across every token field before building the principal map, and assign each configured token exactly its documented role by removing the collision-driven union/overwrite behavior (`REQ-003`, `REQ-004`). Keep the missing-required-mapping raise and empty-mapping deny-all semantics unchanged (`REQ-005`).

## Scope

- Modify `scripts/eventbus/auth.py` only, inside `_populate_token_maps()` (lines 97-205): add the duplicate-token guard before the map is populated, and simplify the per-role assignment to a single documented role.
- Do not modify `scripts/eventbus/config.py` here — the mapping pass-through and type normalization are the sibling procedure for `config.py`. This file owns only the guard, the role binding, and preserving the missing-vs-empty distinction.

## Assumptions

- Rejecting duplicate non-empty token values as a hard error in every deployment is required by the fail-closed rule (`UNK-01`); the rejection covers all six token fields including `auth_token` versus `admin_token` for uniformity (`UNK-02`).
- Because duplicates are rejected, no token is both a control-plane token and a per-role token, so the `existing` lookup in the per-role loop is always `None` — the union collapses to the single documented role.

## Design decisions

- **Guard placement.** Insert the duplicate check immediately after the `_fingerprint` helper definition (line 112) and before the `auth_token` control-plane block (line 141), i.e. before `_TOKEN_PRINCIPAL_MAP` is populated. This covers the `app.py` startup path, the `admin_route.py` runtime rebuild, and direct test callers uniformly.
- **Field set and message.** Iterate all six token fields (`auth_token`, `publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`, `admin_token`), group non-empty values by value, and raise `ValueError` naming the colliding field names only — never interpolate or log the values.

## Alternatives considered

- Guarding in `load_config()` only: rejected — the issue scopes the guard to "before token maps are built," and `_populate_token_maps()` is the sole map-builder reached by startup, runtime rebuild, and tests; `load_config()` owns only pass-through/normalization.
- Keeping the union but only for non-control-plane tokens: rejected — the whole point of REQ-004 is that a per-role token equal to `auth_token` must be rejected, not admitted with control-plane + CONSUMER.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Insert the duplicate-non-empty-token guard after the `_fingerprint` helper (ends line 112) and before the `auth_token` control-plane comment (line 137).
2. Simplify the per-role assignment in the `_PER_ROLE_TOKEN_FIELDS` loop (lines 185-195) to assign exactly the single documented role, dropping the `existing.roles | {role}` union and the `existing` fallbacks.
3. Leave the `admin_token` block (lines 197-205) unchanged — with duplicates rejected it can only add a fresh entry.

### Method

Insert this block right after line 112 (the closing of the `_fingerprint` helper):

```python
    # Duplicate-non-empty-token guard (REQ-003): reject any two distinct token
    # fields that share a non-empty value before the principal map is built. Name
    # the colliding fields only; never interpolate or log the values.
    seen: dict[str, list[str]] = {}
    for field in (
        "auth_token",
        "publisher_token",
        "consumer_token",
        "operator_token",
        "monitoring_token",
        "admin_token",
    ):
        value = getattr(config, field, None)
        if value:
            seen.setdefault(value, []).append(field)
    for fields in seen.values():
        if len(fields) > 1:
            raise ValueError(
                "eventbus config duplicate token: "
                f"{', '.join(sorted(fields))} share a non-empty value. "
                "Each token field must hold a distinct value."
            )
```

Replace the body of the per-role loop (lines 185-195) with:

```python
    for field, role in _PER_ROLE_TOKEN_FIELDS:
        token = getattr(config, field, None)
        if not token:
            continue
        has_consumer = role == Role.CONSUMER
        _TOKEN_PRINCIPAL_MAP[token] = Principal(
            roles=frozenset({role}),
            allowed_consumer_ids=consumer_allowed_ids if has_consumer else frozenset(),
            allowed_topics=consumer_allowed_topics if has_consumer else frozenset(),
            token_fingerprint=_fingerprint(token),
        )
```

### Details

- The guard groups by raw token value but only ever emits the sorted field-name list in the message; the value itself is never formatted into the string, satisfying the no-log-values requirement.
- `has_consumer = role == Role.CONSUMER` replaces the old `Role.CONSUMER in roles` check: since each token now holds exactly one role, membership reduces to an equality against the CONSUMER role. Only the consumer token therefore receives `consumer_allowed_ids`/`consumer_allowed_topics`; every other principal keeps deny-all.
- The `existing` variable and both `existing.*` fallbacks are removed entirely — they can no longer apply because a colliding token is rejected upstream.
- The `admin_token` block (lines 178-186) is left verbatim; with duplicates rejected it cannot overwrite another principal.
- The missing-required-mapping raise (lines 160-164) and the empty-mapping deny-all (lines 176-180) are untouched (`REQ-005`).

## Compatibility considerations

- `_populate_token_maps()` keeps its signature `_populate_token_maps(config: Any) -> None`; no caller changes. It is reached from `scripts/eventbus/app.py` (lifespan line 74, `_main()`), `scripts/eventbus/admin_route.py` (runtime rebuild), and the test files directly.
- Behavior change: a deployment currently running with two token fields sharing a value will now fail startup instead of silently admitting a collided principal. This is the intended fail-closed outcome (`REQ-003`, `REQ-004`).

## Security considerations

- Rejecting duplicate token values closes the path where a per-role token equal to the shared `auth_token` gained the control-plane roles plus CONSUMER (contradicting ADR-013 INV-02/INV-07), and where `admin_token` equal to another token silently overwrote that principal.
- The error message names only field names, never token values, so it cannot leak a secret into logs or client responses.

## Rollback considerations

- Revert the guard insertion and the per-role loop simplification to restore the union/overwrite behavior.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/auth.py` | Unit: duplicate rejection (every pair, direct call), one-role-per-token, admin overwrite gone | `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_admin_topics_authorization.py` | no control-plane+CONSUMER principal; each token has exactly its role; duplicate raises naming fields |
| `scripts/eventbus/auth.py` | Static: no `existing.roles | {role}` union, no unconditional admin overwrite | `rg "roles \| \{" scripts/eventbus/auth.py` | zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- Two distinct token fields sharing a non-empty value raise `ValueError` naming the fields (and not the values) before the map is built (`REQ-003`).
- Each accepted token holds exactly its documented role set; no principal carries control-plane-plus-CONSUMER (`REQ-004`).
- A missing required mapping still raises and an empty mapping stays deny-all (`REQ-005`).

## Out of Scope

- Mapping pass-through and type normalization in `load_config()` — handled by the sibling procedure for `scripts/eventbus/config.py` (`REQ-001`, `REQ-002`).
- Missing-required-mapping message wording and empty-deny-all implementation details — unchanged (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement token-role binding and duplicate rejection in `scripts/eventbus/auth.py` | Completed | 20261025 | 20261025 | Matches current `_populate_token_maps()` (lines 114-205) |
| 2 | Add or update tests per Validation plan | Completed | 20261025 | 20261025 | `test_eventbus_auth.py` + `test_admin_topics_authorization.py`: 46 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261025 | 20261025 | `tests/eventbus/`: 329 passed, 1 skipped, 0 failures; `rg` union check clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A: documentation unchanged per Out of Scope |

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
- **Requirement ID**: `REQ-003` (duplicate rejection), `REQ-004` (one-role-per-token), `REQ-005` (missing-raises / empty-deny-all preserved)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `scripts/eventbus/auth.py`
