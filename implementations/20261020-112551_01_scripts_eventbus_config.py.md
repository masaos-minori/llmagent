## Goal
Make `scripts/eventbus/config.py` expand `${ENV:VAR_NAME}` references for the six token keys before any
token value is validated or stored, so an unresolved placeholder can never become a live bearer token and
an unset variable stops the Event Bus at config load with an error naming the variable.

## Scope
- Add one import of `shared.config_utils.resolve_env_ref` (line 10 region).
- Add the module-level `_TOKEN_CONFIG_KEYS` (new) tuple after `_CONFIG_KEY_TYPES`.
- Insert the resolution loop between the type-validation loop (`:296-305`) and the non-empty check
  (`:307-309`) in `load_config`.

## Assumptions
- The type loop has already guaranteed each present token value is `str`, so `resolve_env_ref` is always
  called with a `str`.
- `resolve_env_ref` returns the input unchanged when it does not match `^\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}$`
  (`scripts/shared/config_utils.py:19-31`), so literal tokens keep working.
- `scripts/shared/config_utils.py:34-37` raises `ValueError` naming the unset variable, which is the message
  `AC-2` requires on the config side.

## Design decisions
- Resolve in `load_config`, not in `auth.py`: `scripts/eventbus/auth.py:118-125` registers whatever string the
  config object holds as a principal, so the value must already be resolved before the dataclass is built.
- Resolve before validation, not after: an unresolved reference is non-empty and would pass the
  `:307-309` guard, which is the defect this row fixes.
- New `_TOKEN_CONFIG_KEYS` (new) tuple instead of deriving the token subset from `_CONFIG_KEY_TYPES`: the subset is
  a security-relevant list that should be readable and greppable, not computed.
- Call `resolve_env_ref` directly rather than `shared.config_utils.get_str` (`:42`): `get_str` substitutes a
  default for a missing value, which is weaker than the fail-closed contract.

## Alternatives considered
- Resolve inside the existing type loop: rejected because it mixes environment access with type checking and
  makes the ordering (resolve, then validate) implicit.
- Resolve lazily in `scripts/eventbus/auth.py:get_auth_token` (`:189`): rejected because the placeholder would
  already be stored in `EventBusConfig` (`:322-327`) and reachable from any other reader.
- Expand references for all config keys: rejected; only the six token keys carry credentials, and expanding
  paths would change unrelated validation messages.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Add the resolver import after the existing shared import.
2. Add `_TOKEN_CONFIG_KEYS` (new) after `_CONFIG_KEY_TYPES`.
3. Insert the resolution loop immediately before `# Validate auth_token is non-empty`.

### Method
- Edit 1 adds one line to the import block; import order stays `shared.config_loader` then
  `shared.config_utils` (isort-compatible).
- Edit 2 adds a commented tuple of the six keys exactly as they appear in `_CONFIG_KEY_TYPES:238-251`.
- Edit 3 adds a five-line loop that mutates `data` in place, guarded by `isinstance(value, str)` so a key
  absent from the TOML is left untouched.

### Details
Edit 1:

```python
# Before:
from shared.config_loader import ConfigLoader
# After:
from shared.config_loader import ConfigLoader
from shared.config_utils import resolve_env_ref
```

Edit 2:

```python
# Before:
    "publish_rate": float,
}
# After:
    "publish_rate": float,
}

# Token keys whose value may be a "${ENV:VAR_NAME}" reference. Resolved in
# load_config() before any value is validated, so a reference can never be used
# as a literal token and an unset variable fails the load.
_TOKEN_CONFIG_KEYS: tuple[str, ...] = (
    "auth_token",
    "publisher_token",
    "consumer_token",
    "operator_token",
    "monitoring_token",
    "admin_token",
)
```

Edit 3:

```python
# Before:
    # Validate auth_token is non-empty
    if not data["auth_token"]:
# After:
    # Resolve "${ENV:VAR_NAME}" references before validating any token value
    for key in _TOKEN_CONFIG_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            data[key] = resolve_env_ref(value)

    # Validate auth_token is non-empty
    if not data["auth_token"]:
```

## Compatibility considerations
- Literal token configurations (the shape used by every existing case in
  `tests/eventbus/test_eventbus_config.py`) are unchanged: `resolve_env_ref` returns them as-is.
- The only new failure mode is `ValueError` from `scripts/shared/config_utils.py` when a referenced variable
  is unset. Every existing message, including `eventbus config 'auth_token' must not be empty.`, is kept, and
  the set-but-empty path still reaches it.
- `eventbus` importing `shared` is permitted: `.importlinter`'s `eventbus-is-isolated` forbids `agent`,
  `mcp_servers`, `rag`, and `db` only, and `scripts/eventbus/config.py:10` already imports `shared`.

## Security considerations
- Closes the bypass measured by `/tmp/opencode/probe_eventbus_env_ref.py`: with a reference present,
  `cfg.auth_token` stayed the literal placeholder and `scripts/eventbus/auth.py` would have registered it as
  a control-plane principal.
- Fail-closed is preserved: unset variable raises before the service binds the port.
- No token value is logged; the resolver reports only the variable name.

## Rollback considerations
Single-path revert: `git checkout HEAD -- scripts/eventbus/config.py`. No data, schema, or configuration file
depends on the new behavior.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Targeted tests | `uv run pytest tests/eventbus/test_eventbus_config.py -q -p no:randomly` | All existing cases green |
| Revert-and-bite | revert this file, re-run the new cases added by seq 05, restore | The reference case fails, proving the cases bite |
| Type | `uv run mypy --no-namespace-packages --no-incremental scripts/eventbus/config.py` | No issues |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept, 0 broken |
| Module size | `uv run python tools/check_module_size.py` | No new finding |

## Completion criteria
- The three edits are present in the order above and `bash`-free (Python only).
- `T-1`, `T-2`, `T-3` from the Plan pass, and the revert-and-bite check fails without this change.
- `lint-imports`, `mypy`, and `check_module_size` are clean.

## Out of Scope
- `config/eventbus.toml` (seq 02), the deployment scripts (seq 03, 04), and the test modules (seq 05).
- `scripts/eventbus/auth.py`, role semantics, `consumer_authorization` mappings, and the envelope schema.
- Per-role tokens in the shipped TOML (`UNK-03` in the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-124854 | 20261020-125657 | three edits applied; verified against source at :10, :259-260, :307-308 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-125657 | tests are owned by seq 05 N/A here: tests owned by seq 05; existing tests/eventbus suite green (360 passed, 1 skipped); revert-and-bite deferred to seq 05 per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-125657 | ruff format/check, mypy, lint-imports (6 kept), check_module_size (OK), bandit clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-125657 | docs are owned by seq 07, 08 N/A: docs owned by seq 07, 08 |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `scripts/eventbus/config.py`, `scripts/shared/config_utils.py` (read-only),
  `scripts/eventbus/auth.py` (read-only)