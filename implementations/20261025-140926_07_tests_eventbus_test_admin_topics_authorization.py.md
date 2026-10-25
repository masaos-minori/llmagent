## Goal

Add tests to `tests/eventbus/test_admin_topics_authorization.py` that verify `_populate_token_maps()` enforces one-role-per-token (`REQ-004`) and rejects duplicate non-empty token values naming the colliding fields (`REQ-003`), calling `_populate_token_maps()` exactly as `admin_route.py` rebuilds the maps at runtime.

## Scope

- Modify `tests/eventbus/test_admin_topics_authorization.py` only: append two new test classes that drive `_populate_token_maps()` directly.
- Do not modify `scripts/eventbus/auth.py` or `scripts/eventbus/admin_route.py` here — those are the sibling implementation procedures. This file only verifies the choke point `admin_route.py` calls (`REQ-003`, `REQ-004`).

## Assumptions

- The new tests follow the existing local-import style in this file (`_init_state` imports `_populate_token_maps`; `TestUpdateTakesEffect` imports `_TOKEN_PRINCIPAL_MAP`), reusing those exact standalone import statements that already exist in the file.
- `_populate_token_maps()` clears and repopulates the module-global `_TOKEN_PRINCIPAL_MAP`; each test snapshots and restores it to stay self-contained (the conftest autouse fixture also restores it across tests).
- `EventBusConfig` is a frozen dataclass, so a modified copy is built with `dataclasses.replace` — the same immutable-rebuild pattern `admin_route.py` uses when it swaps the config on a runtime update.
- `Role` is a `StrEnum`, so a principal's `roles` frozenset compares equal to the equivalent set of role-name strings.

## Design decisions

- **Call the runtime-rebuild choke point directly.** Each test builds an `EventBusConfig` and calls `_populate_token_maps(cfg)`, the identical call `admin_route.py` makes on a runtime authorization update and `_init_state` makes at client setup, so the tests cover the production rebuild path, not a separate code path.
- **Snapshot/restore of global state.** `_populate_token_maps()` mutates `_TOKEN_PRINCIPAL_MAP`; each test snapshots and restores it to avoid cross-test contamination.

## Alternatives considered

- Driving the change through the `POST /admin/topics/authorization` endpoint with a TestClient: rejected — the acceptance criteria are about the map-builder's guard and role binding, which are asserted most directly on `_populate_token_maps()` output; the endpoint is already covered by the existing `TestUpdateTakesEffect` class.

## Implementation

### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

Append the `TestOneRolePerTokenAdminRebuild` (new) and `TestDuplicateRejectionAdminRebuild` (new) classes below to the end of the file. Each builds an `EventBusConfig` with distinct tokens, calls `_populate_token_maps(cfg)`, and asserts on `_TOKEN_PRINCIPAL_MAP`. Import `_populate_token_maps`, `_TOKEN_PRINCIPAL_MAP`, and `EventBusConfig` locally inside each method using the standalone import forms that already exist in this file.

### Method

```python
class TestOneRolePerTokenAdminRebuild:
    """REQ-004: each configured token holds exactly its documented role when
    _populate_token_maps() runs as admin_route.py rebuilds the maps."""

    @staticmethod
    def _snapshot():
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        return dict(_TOKEN_PRINCIPAL_MAP)

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        _TOKEN_PRINCIPAL_MAP.clear()
        _TOKEN_PRINCIPAL_MAP.update(snapshot)

    def test_each_token_holds_exactly_its_documented_role(self) -> None:
        """A distinct-token config gives every token exactly its documented role
        set, with no control-plane-plus-CONSUMER collision."""
        from eventbus.auth import _populate_token_maps
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP
        from eventbus.config import EventBusConfig

        snapshot = self._snapshot()
        try:
            cfg = EventBusConfig(
                port=8016,
                db_path="/tmp/test-admin-distinct.sqlite",
                storage_dir="/tmp/test-admin-distinct",
                deadletter_dir="/tmp/test-admin-distinct",
                max_retry=3,
                auth_token="auth-token",
                publisher_token="publisher-token",
                consumer_token="consumer-token",
                operator_token="operator-token",
                monitoring_token="monitoring-token",
                admin_token="admin-token",
                consumer_authorization={"c1": ["topicA"]},
                topic_authorization={"topicA": ["c1"]},
            )
            _populate_token_maps(cfg)
            assert set(_TOKEN_PRINCIPAL_MAP["auth-token"].roles) == {
                "operator",
                "monitoring",
                "admin",
            }
            assert set(_TOKEN_PRINCIPAL_MAP["publisher-token"].roles) == {"publisher"}
            assert set(_TOKEN_PRINCIPAL_MAP["consumer-token"].roles) == {"consumer"}
            assert set(_TOKEN_PRINCIPAL_MAP["operator-token"].roles) == {"operator"}
            assert set(_TOKEN_PRINCIPAL_MAP["monitoring-token"].roles) == {
                "monitoring"
            }
            assert set(_TOKEN_PRINCIPAL_MAP["admin-token"].roles) == {
                "operator",
                "monitoring",
                "admin",
            }
        finally:
            self._restore(snapshot)


class TestDuplicateRejectionAdminRebuild:
    """REQ-003: duplicate non-empty token values are rejected by
    _populate_token_maps() as admin_route.py calls it, naming the fields."""

    @staticmethod
    def _snapshot():
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        return dict(_TOKEN_PRINCIPAL_MAP)

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        _TOKEN_PRINCIPAL_MAP.clear()
        _TOKEN_PRINCIPAL_MAP.update(snapshot)

    @pytest.mark.parametrize(
        "field_a,field_b",
        [
            ("auth_token", "consumer_token"),
            ("auth_token", "admin_token"),
            ("publisher_token", "consumer_token"),
        ],
    )
    def test_two_equal_tokens_raise_naming_fields(
        self, field_a: str, field_b: str
    ) -> None:
        """Every tested pair of distinct token fields sharing a non-empty value
        raises, naming both fields and not the shared value."""
        import dataclasses

        from eventbus.auth import _populate_token_maps
        from eventbus.config import EventBusConfig

        base = EventBusConfig(
            port=8016,
            db_path="/tmp/test-admin-dup.sqlite",
            storage_dir="/tmp/test-admin-dup",
            deadletter_dir="/tmp/test-admin-dup",
            max_retry=3,
            auth_token="auth-token",
            publisher_token="",
            consumer_token="",
            operator_token="",
            monitoring_token="",
            admin_token="",
            consumer_authorization={},
        )
        cfg = dataclasses.replace(
            base, **{field_a: "shared-value", field_b: "shared-value"}
        )
        with pytest.raises(ValueError, match="duplicate token") as exc_info:
            _populate_token_maps(cfg)
        message = str(exc_info.value)
        assert "shared-value" not in message
        assert field_a in message
        assert field_b in message
```

### Details

- The one-role-per-token test asserts all six tokens resolve to exactly their documented role sets: the two control-plane tokens to `{operator, monitoring, admin}`, and each per-role token to its single role — proving no `existing.roles | {role}` union remains (`REQ-004`).
- The parametrized duplicate test covers a consumer-collision pair (`auth_token`/`consumer_token`, the control-plane-plus-CONSUMER case), a control-plane pair (`auth_token`/`admin_token`, the overwrite case), and a per-role pair (`publisher_token`/`consumer_token`), exercising the uniform six-field guard.
- `dataclasses.replace(base, ...)` produces a fresh frozen `EventBusConfig` with two fields sharing `"shared-value"`, mirroring how `admin_route.py` builds a replacement config on a runtime update rather than mutating the live one.
- Role sets are compared against role-name strings because `Role` is a `StrEnum`; no `Role` import is needed.
- The duplicate guard fires before the missing-required-mapping check, so the `consumer_authorization={}` on the base config never masks the duplicate raise.

## Compatibility considerations

- N/A: test-only additions; no production code touched by this document.

## Security considerations

- The one-role-per-token test asserts no principal carries more than its documented role, covering the ADR-013 INV-02/INV-07 one-role-per-token model (`REQ-004`).
- The duplicate-rejection test asserts the error names the colliding fields and omits the shared token value, covering the no-secret-leak requirement (`REQ-003`).

## Rollback considerations

- Delete the `TestOneRolePerTokenAdminRebuild` (new) and `TestDuplicateRejectionAdminRebuild` (new) classes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_admin_topics_authorization.py` | Unit: one-role-per-token for each token, duplicate rejection (every pair) via `_populate_token_maps` | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` | new tests pass; existing tests still pass |
| `scripts/eventbus/*` | Static: no `existing.roles | {role}` union, no unconditional admin overwrite | `rg "roles \| \{" scripts/eventbus/auth.py` | zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- `test_each_token_holds_exactly_its_documented_role`(new) passes: each of the six tokens holds exactly its documented role set with no control-plane-plus-CONSUMER principal (`REQ-004`).
- `test_two_equal_tokens_raise_naming_fields`(new) passes: every tested pair raises a `ValueError` naming both fields and omitting the shared value (`REQ-003`).

## Out of Scope

- Mapping pass-through and type normalization — handled by the sibling test procedure for `test_eventbus_config.py` (`REQ-001`, `REQ-002`).
- Missing-required-mapping raise and empty-deny-all — handled by the sibling test procedure for `test_eventbus_consumer_authorization.py` (`REQ-005`).

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
- **Requirement ID**: `REQ-003` (duplicate rejection), `REQ-004` (one-role-per-token)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `tests/eventbus/test_admin_topics_authorization.py`
