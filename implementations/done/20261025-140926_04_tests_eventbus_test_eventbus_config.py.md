## Goal

Add tests to `tests/eventbus/test_eventbus_config.py` that exercise the `load_config()` changes: a valid mapping is surfaced on the built config (`REQ-001`), the TOML array value types are normalized to `set[str]` / `list[str]` as annotated (`REQ-002`), and a duplicate token value fed through the load path is rejected (`REQ-003`).

## Scope

- Modify `tests/eventbus/test_eventbus_config.py` only: append new test functions under the existing `tmp_path`-based pattern (write a TOML string, call `load_config(toml_path)`, assert on the result).
- Do not modify `scripts/eventbus/config.py` or `scripts/eventbus/auth.py` here — those are the sibling implementation procedures. This file only verifies their behavior.

## Assumptions

- The new tests follow the file's existing convention: a `tmp_path` fixture, an inline TOML string, and `load_config()` from `eventbus.config` (already imported at module level, line 10).
- The duplicate-token guard lives in `_populate_token_maps()` (the sibling `auth.py` procedure); this file drives it by calling `_populate_token_maps(cfg)` after `load_config()`, i.e. the load-then-populate path.

## Design decisions

- **Load-then-populate for the duplicate test.** Because the guard is in `_populate_token_maps()` and not in `load_config()`, the "via the load path" test builds the config with `load_config()` and then calls `_populate_token_maps(cfg)`, asserting it raises — this proves the loaded config (with its normalized types) feeds the guard correctly.
- **Distinct TOML per test.** Each new test writes its own minimal TOML (only the keys it needs) to avoid cross-test coupling, matching the existing per-test `tmp_path` files.

## Alternatives considered

- Asserting `load_config()` itself raises on duplicate tokens: rejected — the guard is intentionally in `_populate_token_maps()`, not `load_config()`; asserting otherwise would test the wrong function.

## Implementation

### Target file

`tests/eventbus/test_eventbus_config.py`

### Procedure

Append the three test functions below to the end of the file. Each uses the `tmp_path` fixture and the module-level `load_config` import.

### Method

`test_load_config_surfaces_authorization_mappings` (new) — `REQ-001`:

```python
def test_load_config_surfaces_authorization_mappings(tmp_path) -> None:
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        'host = "127.0.0.1"\n'
        'auth_token = "test-token"\n'
        'consumer_token = "consumer-token"\n'
        'consumer_authorization = { "svc-a" = [ "orders/*" ] }\n'
        'topic_authorization = { "orders/*" = [ "svc-a" ] }\n'
    )
    cfg = load_config(config_file)
    assert cfg.consumer_authorization is not None
    assert cfg.topic_authorization is not None
```

`test_load_config_normalizes_mapping_types` (new) — `REQ-002`:

```python
def test_load_config_normalizes_mapping_types(tmp_path) -> None:
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        'host = "127.0.0.1"\n'
        'auth_token = "test-token"\n'
        'consumer_token = "consumer-token"\n'
        'consumer_authorization = { "svc-a" = [ "orders/*", "inventory/*" ] }\n'
        'topic_authorization = { "orders/*" = [ "svc-a", "svc-b" ] }\n'
    )
    cfg = load_config(config_file)
    assert all(isinstance(v, set) for v in cfg.topic_authorization.values())
    assert all(isinstance(v, list) for v in cfg.consumer_authorization.values())
```

`test_load_config_duplicate_token_via_load_path_raises` (new) — `REQ-003`:

```python
def test_load_config_duplicate_token_via_load_path_raises(tmp_path) -> None:
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        'host = "127.0.0.1"\n'
        'auth_token = "shared-dup"\n'
        'admin_token = "shared-dup"\n'
    )
    cfg = load_config(config_file)
    with pytest.raises(ValueError, match="duplicate token") as exc_info:
        _populate_token_maps(cfg)
    message = str(exc_info.value)
    assert "shared-dup" not in message
    for field in ("auth_token", "admin_token"):
        assert field in message
```

- The duplicate test imports `_populate_token_maps` from `eventbus.auth` (new import) — add it inside the test function or at module level, mirroring the existing in-function import style used by `test_admin_token_grants_control_plane_roles_only`.
- The assertion `assert "shared-dup" not in message` enforces the no-value-leak requirement; the field-name assertions enforce the naming requirement.

### Details

- `auth_token` vs `admin_token` share identical control-plane roles today, so this pair exercises the uniform six-field guard without depending on per-role semantics; the sibling `test_eventbus_auth.py` covers the per-role pairs.
- The type-normalization test asserts the concrete runtime types on the config produced by `load_config()`, which is what REQ-002 fixes.

## Compatibility considerations

- N/A: test-only additions; no production code touched by this document.

## Security considerations

- The duplicate-rejection test asserts the error message does not contain the shared token value, covering the no-secret-leak requirement (`REQ-003`).

## Rollback considerations

- Delete the three appended test functions.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_config.py` | Unit: mapping surfaces, type normalization, duplicate rejection via load path | `uv run pytest tests/eventbus/test_eventbus_config.py` | three new tests pass; existing tests still pass |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- `test_load_config_surfaces_authorization_mappings` (new) passes: both mappings present on the loaded config (`REQ-001`).
- `test_load_config_normalizes_mapping_types` (new) passes: `topic_authorization` values are `set`, `consumer_authorization` values are `list` (`REQ-002`).
- `test_load_config_duplicate_token_via_load_path_raises` (new) passes: `_populate_token_maps()` raises naming `auth_token`/`admin_token` and not the shared value (`REQ-003`).

## Out of Scope

- Duplicate-pair coverage for the other token fields and one-role-per-token — handled by the sibling test procedures for `test_eventbus_auth.py` and `test_admin_topics_authorization.py` (`REQ-003`, `REQ-004`).
- Missing-required-mapping raise and empty-deny-all — handled by `test_eventbus_consumer_authorization.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261026 | 20261026 | Applied during verification; 3 new tests appended |
| 2 | Add or update tests per Validation plan | Completed | 20261026 | 20261026 | `test_load_config_surfaces_authorization_mappings`, `test_load_config_normalizes_mapping_types`, `test_load_config_duplicate_token_via_load_path_raises`: 3 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261026 | 20261026 | `tests/eventbus/`: 344 passed, 1 skipped, 0 failures |
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
- **Requirement ID**: `REQ-001` (mapping surfaces), `REQ-002` (type normalization), `REQ-003` (duplicate rejection via load path)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `tests/eventbus/test_eventbus_config.py`
