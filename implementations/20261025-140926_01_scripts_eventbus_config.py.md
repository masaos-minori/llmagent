## Goal

Make `load_config()` the authoritative path that carries the validated `consumer_authorization` and `topic_authorization` mappings into `EventBusConfig` instead of dropping them, and normalize the TOML array value types to the `EventBusConfig` annotations (`topic_authorization` values → `set[str]`; `consumer_authorization` values stay `list[str]`) (`REQ-001`, `REQ-002`).

## Scope

- Modify `scripts/eventbus/config.py` only: add both mapping keys to the `EventBusConfig(...)` call in `load_config()` and normalize their value types before construction.
- Do not modify `scripts/eventbus/auth.py` here — the duplicate-token guard and union/overwrite removal are the sibling procedure for `auth.py`. This file owns only the pass-through and normalization (`REQ-001`, `REQ-002`).

## Assumptions

- A missing mapping key stays `None` through `load_config()` so the empty-vs-missing distinction that `_populate_token_maps()` relies on (missing raises, empty denies-all) is preserved — resolves `UNK-03` for the load path.
- `consumer_authorization` TOML arrays are already Python `list`s after parsing, so they need no conversion; only `topic_authorization` values are converted to `set`.
- The validators in `EventBusConfig.__post_init__` already accept both `list` and `set` for `topic_authorization` (lines 177-192), so converting to `set[str]` cannot break validation.

## Design decisions

- **Normalize before construction.** Compute the two normalized values in a small block immediately before the `EventBusConfig(...)` call, then pass them by keyword. This keeps `load_config()`'s single responsibility (pass-through + normalization) separate from `_populate_token_maps()`'s (guard + binding).
- **Convert only `topic_authorization`.** Wrap each `topic_authorization` value list in `set(...)` to match the annotation `dict[str, set[str]]`; leave `consumer_authorization` untouched to match its `dict[str, list[str]]` annotation. A `None` value passes through unchanged.

## Alternatives considered

- Normalizing inside `EventBusConfig.__post_init__`: rejected — the annotation-level validator already accepts both types, and the plan scopes normalization to the loader so the runtime collection type is fixed at the authoritative load path, not per-instance.
- Leaving both as raw lists and letting `_populate_token_maps()` coerce: rejected — REQ-002 requires the config built by `load_config()` itself to expose `set[str]` for `topic_authorization`, so the test on the loaded config would fail.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Insert a normalization block between the `auth_token` non-empty check (line 323-324) and the `cfg = EventBusConfig(` call (line 326).
2. Add `consumer_authorization` and `topic_authorization` keyword arguments to the `EventBusConfig(...)` call (lines 326-347).

### Method

Insert this block right before line 326 (`cfg = EventBusConfig(`):

```python
# Normalize authorization-mapping value types to the EventBusConfig annotations
# (REQ-002): topic_authorization values become set[str]; consumer_authorization
# values stay list[str]. A missing key stays None so the empty-vs-missing
# distinction _populate_token_maps() depends on is preserved.
consumer_authorization = data.get("consumer_authorization")
topic_authorization = data.get("topic_authorization")
if topic_authorization is not None:
    topic_authorization = {
        topic: set(consumers) for topic, consumers in topic_authorization.items()
    }
```

Then add the two keyword arguments to the constructor (after `admin_token=...`, line 341):

```python
        consumer_authorization=consumer_authorization,
        topic_authorization=topic_authorization,
```

### Details

- The normalization block reads from `data` (the parsed TOML dict) via `data.get(...)`, so a missing key yields `None` rather than `{}` — the load path preserves the exact `None` that `_populate_token_maps()` treats as "missing required" (lines 137-141 in `scripts/eventbus/auth.py`).
- `topic_authorization` is converted only when present; an absent key stays `None` and is passed straight through.
- `consumer_authorization` is passed through as the parsed list-of-lists, matching its annotation; no conversion is applied.
- The conversion is safe because `__post_init__` already accepts `set` for `topic_authorization` (lines 177-192) and `_populate_token_maps()` already wraps values in `set(...)`.

## Compatibility considerations

- The return type of `load_config()` stays `EventBusConfig`; no caller signature changes. The only production caller is `scripts/eventbus/app.py` (lifespan line 71, `_main()` line 297), which consumes the config unchanged.
- `topic_authorization` now holds `set[str]` values instead of the raw TOML `list`. Any code reading `cfg.topic_authorization` directly sees the normalized type; `_populate_token_maps()` already expected sets, so no regression.

## Security considerations

- Carrying the mappings into `EventBusConfig` restores the fail-closed authorization table that was silently dropped on the production load path (`REQ-001`); a configured `consumer_token` with a valid mapping now reaches `_populate_token_maps()` instead of raising `consumer_authorization is missing`.
- The normalization touches only mapping value containers, never token values; `${ENV:...}` resolution (lines 317-320) still runs before these values are read.

## Rollback considerations

- Revert the normalization block and the two added keyword arguments to restore the previous drop-the-mappings behavior.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | Unit: mapping pass-through + type normalization via `load_config(toml_path)` | `uv run pytest tests/eventbus/test_eventbus_config.py` | both mappings present on the built config; `topic_authorization` values are `set`, `consumer_authorization` values are `list`; missing key yields `None` |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | clean; all contracts KEPT |

## Completion criteria

- The `EventBusConfig(...)` call in `load_config()` includes `consumer_authorization` and `topic_authorization` sourced from `data.get(...)` (`REQ-001`).
- On the config built by `load_config()`, `topic_authorization` values are `set[str]` and `consumer_authorization` values are `list[str]`; a missing key remains `None` (`REQ-002`).

## Out of Scope

- The duplicate-non-empty-token guard and union/overwrite removal in `_populate_token_maps()` — handled by the sibling procedure for `scripts/eventbus/auth.py` (`REQ-003`, `REQ-004`).
- Missing-required-mapping raise and empty-mapping deny-all semantics — unchanged, owned by `auth.py` (`REQ-005`).
- Test additions for duplicate rejection and one-role-per-token — handled by the sibling test procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement mapping pass-through and type normalization in `scripts/eventbus/config.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (mapping pass-through), `REQ-002` (value-type normalization)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `scripts/eventbus/config.py`
