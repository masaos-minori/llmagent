## Goal

Add tests to `tests/eventbus/test_eventbus_consumer_authorization.py` that verify the `load_config()` mapping pass-through (`REQ-001`) and the preserved missing-vs-empty mapping semantics (`REQ-005`): a consumer/topic mapping written to a TOML file survives `load_config()` and reaches the consumer principal after `_populate_token_maps()`, an empty mapping stays deny-all, and a missing required mapping still raises.

## Scope

- Modify `tests/eventbus/test_eventbus_consumer_authorization.py` only: append a new test class exercising the config-load path.
- Do not modify `scripts/eventbus/config.py` or `scripts/eventbus/auth.py` here — those are the sibling implementation procedures. This file only verifies their behavior through the loader.

## Assumptions

- The new tests follow the existing local-import style in this file (`_build_client` imports `EventBusConfig` from `eventbus.config`; `_delivery_state` imports `eventbus.app`), importing `eventbus.config` and `eventbus.auth` locally inside each method.
- `_populate_token_maps()` clears and repopulates the module-global `_TOKEN_PRINCIPAL_MAP`; each test snapshots and restores it to stay self-contained (the conftest autouse fixture also restores it across tests).
- A missing required mapping still raises from `_populate_token_maps()` regardless of the fix, so that test is a regression guard; the empty-mapping and pass-through tests fail until `load_config()` carries the mapping through.

## Design decisions

- **Drive the real loader path.** Write a TOML file and call `load_config(toml_path)` rather than constructing `EventBusConfig` directly, so the tests exercise the authoritative loader the plan makes authoritative instead of the dataclass-constructor path used by other tests.
- **Snapshot/restore of global state.** `_populate_token_maps()` mutates `_TOKEN_PRINCIPAL_MAP`; each test snapshots and restores it to avoid cross-test contamination.

## Alternatives considered

- Constructing `EventBusConfig(consumer_authorization={...})` directly: rejected — that bypasses `load_config()`, which is exactly the path under test (`REQ-001`).

## Implementation

### Target file

`tests/eventbus/test_eventbus_consumer_authorization.py`

### Procedure

Append the `TestConsumerMappingConfigPath` (new) class below to the end of the file. Each method imports `eventbus.config` and `eventbus.auth` locally, writes a TOML file under `tmp_path`, drives `load_config()`, and calls `_populate_token_maps()` directly to inspect the resulting principal.

### Method

```python
class TestConsumerMappingConfigPath:
    """REQ-001, REQ-005: a consumer/topic mapping written to a TOML file survives
    load_config() and reaches the consumer principal; an empty mapping stays
    deny-all and a missing required mapping raises."""

    def test_mapping_loaded_via_config_reaches_consumer_principal(
        self, tmp_path: Path
    ) -> None:
        """A consumer mapping written to a TOML file survives load_config() and
        reaches the consumer principal after _populate_token_maps()."""
        import eventbus.auth as eb_auth
        import eventbus.config as eb_config

        snapshot = dict(eb_auth._TOKEN_PRINCIPAL_MAP)
        try:
            toml_path = tmp_path / "eventbus_consumer.toml"
            toml_path.write_text(
                'port = 8015\n'
                'db_path = "/tmp/test-eventbus-consumer.sqlite"\n'
                'storage_dir = "/tmp/test-eventbus-consumer"\n'
                'deadletter_dir = "/tmp/test-eventbus-consumer"\n'
                "max_retry = 3\n"
                'host = "127.0.0.1"\n'
                'auth_token = "shared-auth-token"\n'
                'consumer_token = "consumer-token"\n'
                'consumer_authorization = { "c1" = ["topicA"] }\n'
                'topic_authorization = { "topicA" = ["c1"] }\n'
            )
            cfg = eb_config.load_config(toml_path)
            assert cfg.consumer_authorization == {"c1": ["topicA"]}
            eb_auth._populate_token_maps(cfg)
            principal = eb_auth._TOKEN_PRINCIPAL_MAP["consumer-token"]
            assert principal.allowed_consumer_ids == frozenset({"c1"})
            assert principal.allowed_topics == frozenset({"topicA"})
        finally:
            eb_auth._TOKEN_PRINCIPAL_MAP.clear()
            eb_auth._TOKEN_PRINCIPAL_MAP.update(snapshot)

    def test_empty_mapping_via_config_denies_all(self, tmp_path: Path) -> None:
        """An empty consumer mapping written to a TOML file reaches
        _populate_token_maps() as deny-all (empty frozensets)."""
        import eventbus.auth as eb_auth
        import eventbus.config as eb_config

        snapshot = dict(eb_auth._TOKEN_PRINCIPAL_MAP)
        try:
            toml_path = tmp_path / "eventbus_empty.toml"
            toml_path.write_text(
                'port = 8015\n'
                'db_path = "/tmp/test-eventbus-empty.sqlite"\n'
                'storage_dir = "/tmp/test-eventbus-empty"\n'
                'deadletter_dir = "/tmp/test-eventbus-empty"\n'
                "max_retry = 3\n"
                'host = "127.0.0.1"\n'
                'auth_token = "shared-auth-token"\n'
                'consumer_token = "consumer-token"\n'
                'consumer_authorization = {}\n'
            )
            cfg = eb_config.load_config(toml_path)
            assert cfg.consumer_authorization == {}
            eb_auth._populate_token_maps(cfg)
            principal = eb_auth._TOKEN_PRINCIPAL_MAP["consumer-token"]
            assert principal.allowed_consumer_ids == frozenset()
            assert principal.allowed_topics == frozenset()
        finally:
            eb_auth._TOKEN_PRINCIPAL_MAP.clear()
            eb_auth._TOKEN_PRINCIPAL_MAP.update(snapshot)

    def test_missing_mapping_via_config_raises(self, tmp_path: Path) -> None:
        """A consumer_token configured without consumer_authorization raises from
        _populate_token_maps() when loaded through the config path."""
        import eventbus.auth as eb_auth
        import eventbus.config as eb_config

        snapshot = dict(eb_auth._TOKEN_PRINCIPAL_MAP)
        try:
            toml_path = tmp_path / "eventbus_missing.toml"
            toml_path.write_text(
                'port = 8015\n'
                'db_path = "/tmp/test-eventbus-missing.sqlite"\n'
                'storage_dir = "/tmp/test-eventbus-missing"\n'
                'deadletter_dir = "/tmp/test-eventbus-missing"\n'
                "max_retry = 3\n"
                'host = "127.0.0.1"\n'
                'auth_token = "shared-auth-token"\n'
                'consumer_token = "consumer-token"\n'
            )
            cfg = eb_config.load_config(toml_path)
            with pytest.raises(
                ValueError, match="consumer_authorization is missing"
            ) as exc_info:
                eb_auth._populate_token_maps(cfg)
            message = str(exc_info.value)
            assert "Add consumer_authorization" in message
        finally:
            eb_auth._TOKEN_PRINCIPAL_MAP.clear()
            eb_auth._TOKEN_PRINCIPAL_MAP.update(snapshot)
```

### Details

- The pass-through test asserts both `cfg.consumer_authorization` survives `load_config()` and the consumer principal carries `{"c1"}` / `{"topicA"}` after `_populate_token_maps()`, covering `REQ-001` end-to-end.
- The empty-mapping test asserts `{}` survives `load_config()` and resolves to empty frozensets (deny-all), distinct from the missing case.
- The missing-mapping test is a regression guard: the raise is existing behavior preserved by `REQ-005`, so it passes before and after the fix; it locks in the actionable message.
- All three methods use loopback `host = "127.0.0.1"` and absolute temp paths so `EventBusConfig.__post_init__` validation passes without touching production directories.

## Compatibility considerations

- N/A: test-only additions; no production code touched by this document.

## Security considerations

- The pass-through and empty-mapping tests confirm the fail-closed authorization table reaches the consumer principal through the loader (`REQ-001`), and the missing-mapping test confirms a misconfigured `consumer_token` still fails closed (`REQ-005`, ADR-013 INV-02/INV-07).

## Rollback considerations

- Delete the `TestConsumerMappingConfigPath` (new) class.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Unit: mapping pass-through via `load_config()`, empty→deny-all, missing→raises | `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py` | new tests pass; existing tests still pass |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- `test_mapping_loaded_via_config_reaches_consumer_principal`(new) passes: `consumer_authorization` survives `load_config()` and the consumer principal carries the mapped `consumer_id` and topics (`REQ-001`).
- `test_empty_mapping_via_config_denies_all`(new) passes: an empty mapping survives `load_config()` and resolves to deny-all empty frozensets (`REQ-005`).
- `test_missing_mapping_via_config_raises`(new) passes: a `consumer_token` without `consumer_authorization` raises an actionable `ValueError` (`REQ-005`).

## Out of Scope

- Duplicate-token rejection and one-role-per-token — handled by the sibling test procedure for `test_eventbus_auth.py` (`REQ-003`, `REQ-004`).
- Type normalization of the mappings — handled by the sibling test procedure for `test_eventbus_config.py` (`REQ-002`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261026 | 20261026 | Applied during verification; `TestConsumerMappingConfigPath` appended |
| 2 | Add or update tests per Validation plan | Completed | 20261026 | 20261026 | 3 new tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | N/A: test-only |

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
- **Requirement ID**: `REQ-001` (mapping pass-through), `REQ-005` (missing-vs-empty semantics)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `tests/eventbus/test_eventbus_consumer_authorization.py`
