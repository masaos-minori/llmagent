## Goal

Add tests to `tests/eventbus/test_eventbus_auth.py` that verify the `_populate_token_maps()` changes: a per-role token equal to the shared `auth_token` is rejected rather than admitted with control-plane + CONSUMER roles, duplicate non-empty token values raise naming the colliding fields (and never the values), and a distinct-token config gives each token exactly its documented role (`REQ-003`, `REQ-004`).

## Scope

- Modify `tests/eventbus/test_eventbus_auth.py` only: append a new test class covering the duplicate-binding and one-role-per-token behavior.
- Do not modify `scripts/eventbus/auth.py` or `scripts/eventbus/config.py` here — those are the sibling implementation procedures. This file only verifies their behavior.

## Assumptions

- The new tests follow the existing `TestFailClosedConsumerAuthorization` pattern: build an `EventBusConfig`, snapshot `_TOKEN_PRINCIPAL_MAP`, call `_populate_token_maps(cfg)`, assert, then restore the snapshot.
- The duplicate-token guard runs before the missing-required-mapping check, so a config with a duplicate token raises the duplicate error regardless of `consumer_authorization`; the tests pass an empty mapping (`{}`) so the missing-mapping check cannot interfere.

## Design decisions

- **Per-role-equals-auth-token via the guard.** A `consumer_token` equal to `auth_token` is the exact case REQ-004 targets (control-plane + CONSUMER collision). Because the guard rejects any two equal non-empty tokens, this test asserts `ValueError` is raised — proving the collided principal is never built.
- **Snapshot/restore of global state.** `_populate_token_maps()` mutates the module-global `_TOKEN_PRINCIPAL_MAP`; each test snapshots and restores it to avoid cross-test contamination, matching the established pattern.

## Alternatives considered

- Asserting the collided principal exists with control-plane + CONSUMER roles: rejected — that is the pre-fix bug; REQ-004 requires it to be rejected, so the test must assert the raise, not the principal.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

Append the `TestDuplicateTokenBinding` (new) class below to the end of the file, after `TestFailClosedConsumerAuthorization`. Each test imports `_populate_token_maps` and `_TOKEN_PRINCIPAL_MAP` from `eventbus.auth` and `EventBusConfig` from `eventbus.config` inside the test body, mirroring the existing `TestFailClosedConsumerAuthorization` imports.

### Method

```python
class TestDuplicateTokenBinding:
    """REQ-003, REQ-004: duplicate non-empty token values are rejected and each
    token holds exactly its documented role."""

    @staticmethod
    def _snapshot():
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        return dict(_TOKEN_PRINCIPAL_MAP)

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        _TOKEN_PRINCIPAL_MAP.clear()
        _TOKEN_PRINCIPAL_MAP.update(snapshot)

    def test_consumer_token_equal_to_auth_token_is_rejected(self) -> None:
        """A per-role token equal to the shared auth_token is rejected, not
        admitted with control-plane + CONSUMER roles."""
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP, _populate_token_maps
        from eventbus.config import EventBusConfig

        snapshot = self._snapshot()
        try:
            cfg = EventBusConfig(
                port=8091,
                db_path="/tmp/test-eventbus-dup1.sqlite",
                storage_dir="/tmp/test-eventbus-dup1",
                deadletter_dir="/tmp/test-eventbus-dup1",
                max_retry=2,
                host="127.0.0.1",
                auth_token="shared-dup",
                consumer_token="shared-dup",
                consumer_authorization={},
            )
            with pytest.raises(ValueError, match="duplicate token") as exc_info:
                _populate_token_maps(cfg)
            message = str(exc_info.value)
            assert "shared-dup" not in message
            for field in ("auth_token", "consumer_token"):
                assert field in message
        finally:
            self._restore(snapshot)

    def test_distinct_tokens_get_exactly_their_documented_role(self) -> None:
        """A distinct-token config gives each token exactly its documented role."""
        from eventbus.auth import (
            _TOKEN_PRINCIPAL_MAP,
            Principal,
            Role,
            _populate_token_maps,
        )
        from eventbus.config import EventBusConfig

        snapshot = self._snapshot()
        try:
            cfg = EventBusConfig(
                port=8091,
                db_path="/tmp/test-eventbus-distinct.sqlite",
                storage_dir="/tmp/test-eventbus-distinct",
                deadletter_dir="/tmp/test-eventbus-distinct",
                max_retry=2,
                host="127.0.0.1",
                auth_token="auth-token",
                publisher_token="publisher-token",
                consumer_token="consumer-token",
                operator_token="operator-token",
                monitoring_token="monitoring-token",
                admin_token="admin-token",
                consumer_authorization={"consumer_a": ["test"]},
                topic_authorization={"test": ["consumer_a"]},
            )
            _populate_token_maps(cfg)
            assert _TOKEN_PRINCIPAL_MAP["auth-token"].roles == frozenset(
                {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
            )
            assert _TOKEN_PRINCIPAL_MAP["publisher-token"].roles == frozenset(
                {Role.PUBLISHER}
            )
            assert _TOKEN_PRINCIPAL_MAP["consumer-token"].roles == frozenset(
                {Role.CONSUMER}
            )
            assert _TOKEN_PRINCIPAL_MAP["admin-token"].roles == frozenset(
                {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
            )
        finally:
            self._restore(snapshot)

    @pytest.mark.parametrize(
        "field_a,field_b",
        [
            ("auth_token", "admin_token"),
            ("publisher_token", "consumer_token"),
            ("operator_token", "monitoring_token"),
        ],
    )
    def test_any_two_equal_tokens_raise_naming_fields(
        self, field_a: str, field_b: str
    ) -> None:
        """Every pair of distinct token fields sharing a non-empty value raises,
        naming both fields and not the shared value."""
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP, _populate_token_maps
        from eventbus.config import EventBusConfig

        snapshot = self._snapshot()
        try:
            cfg = EventBusConfig(
                port=8091,
                db_path="/tmp/test-eventbus-dup2.sqlite",
                storage_dir="/tmp/test-eventbus-dup2",
                deadletter_dir="/tmp/test-eventbus-dup2",
                max_retry=2,
                host="127.0.0.1",
                auth_token="auth-token",
                publisher_token="",
                consumer_token="",
                operator_token="",
                monitoring_token="",
                admin_token="",
                consumer_authorization={},
            )
            setattr(cfg, field_a, "shared-value")
            setattr(cfg, field_b, "shared-value")
            with pytest.raises(ValueError, match="duplicate token") as exc_info:
                _populate_token_maps(cfg)
            message = str(exc_info.value)
            assert "shared-value" not in message
            assert field_a in message
            assert field_b in message
        finally:
            self._restore(snapshot)
```

### Details

- The parametrized test covers a control-plane pair (`auth_token`/`admin_token`), a per-role pair (`publisher_token`/`consumer_token`), and another per-role pair (`operator_token`/`monitoring_token`), exercising the uniform six-field guard.
- `setattr(cfg, field, "shared-value")` forces two distinct fields to share a value without writing six separate TOML configs.
- The no-value assertions (`assert "shared-dup" not in message`, `assert "shared-value" not in message`) cover the no-secret-leak requirement.

## Compatibility considerations

- N/A: test-only additions; no production code touched by this document.

## Security considerations

- The duplicate-rejection tests assert the error message omits the shared token value, covering the no-secret-leak requirement (`REQ-003`).
- The one-role-per-token test asserts no principal carries control-plane + CONSUMER together, covering the ADR-013 INV-02/INV-07 invariant (`REQ-004`).

## Rollback considerations

- Delete the `TestDuplicateTokenBinding` (new) class.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_auth.py` | Unit: duplicate rejection (every pair), one-role-per-token, no control-plane+CONSUMER principal | `uv run pytest tests/eventbus/test_eventbus_auth.py` | new tests pass; existing tests still pass (baseline 329 passed, 1 skipped) |
| `scripts/eventbus/auth.py` | Static: no `existing.roles | {role}` union remains | `rg "roles \| \{" scripts/eventbus/auth.py` | zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- `test_consumer_token_equal_to_auth_token_is_rejected`(new) passes: no control-plane + CONSUMER principal is built; the raise names `auth_token`/`consumer_token` (`REQ-003`, `REQ-004`).
- `test_distinct_tokens_get_exactly_their_documented_role`(new) passes: each token holds exactly its documented role set (`REQ-004`).
- `test_any_two_equal_tokens_raise_naming_fields`(new) passes: every tested pair raises naming both fields and not the shared value (`REQ-003`).

## Out of Scope

- The admin runtime-rebuild caller (`admin_route.py`) — covered by the sibling test procedure for `test_admin_topics_authorization.py` (`REQ-003`, `REQ-004`).
- Missing-required-mapping raise and empty-deny-all — handled by `test_eventbus_consumer_authorization.py` (`REQ-005`).

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
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
