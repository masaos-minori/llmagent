## Goal
Extend `_is_public_host()` to reject private-LAN (RFC 1918) and other
non-loopback addresses, not only wildcard/unspecified addresses, and remove
`EventBusConfig.allow_public_bind` entirely so the check cannot be bypassed.

## Scope
- **In-Scope**: `_is_public_host()` (verified 2026-09-04, lines 25-36);
  `EventBusConfig.allow_public_bind` field (line 54) and its
  `__post_init__` usage (line 62); `load_config()`'s
  `allow_public_bind=data.get(...)` construction (line 92).
- **Out-of-Scope**: `EventBusConfig.host`'s own default value (line 53,
  already `"127.0.0.1"`, unaffected); `get_config_path()`/`get_schema_path()`/
  `_REMOVED_CONFIG_KEYS` handling (lines 15-22, 69-83), unrelated to bind-
  address validation.

## Assumptions
- `::1` (IPv6 loopback) is intentionally retained per the Plan's Assumptions
  section and `tests/eventbus/test_eventbus_startup.py`'s existing
  `test_safe_bind_loopback_v6()` (verified 2026-09-04) — the extended check
  must continue to accept `::1` alongside `127.0.0.1`.
- Coupled to row 4 (`tests/eventbus/test_eventbus_startup.py`) — that file's
  existing `test_private_ip_allowed_without_override()` and
  `test_unsafe_bind_0000_succeeds_with_override()` tests currently document
  the pre-fix gap/escape-hatch and must be removed or inverted once this row
  lands.

## Design decisions
- Extend `_is_public_host()`'s logic to accept only `127.0.0.1` and `::1` as
  non-public, rejecting every other address (private-LAN, other public,
  unresolvable hostname) — implement as an allow-list (`host in
  {"127.0.0.1", "::1"}` → not public) rather than an expanded deny-list of
  private-LAN ranges, since an allow-list cannot miss a future address class
  the way enumerating RFC 1918 ranges could.
- Remove `allow_public_bind` as a dataclass field, its `__post_init__`
  reference, and its `load_config()` TOML-key read — not merely default it to
  `False` permanently — per REQ-002's explicit "no override possible"
  requirement and `rules/coding.md`'s no-dead-parameter guidance.
- `__post_init__`'s validation `if _is_public_host(self.host) and not
  self.allow_public_bind:` becomes unconditional: `if
  _is_public_host(self.host):`.

## Alternatives considered
- Keeping `allow_public_bind` but hardcoding its effective value to `False`
  everywhere: rejected — same reasoning as the `localremoval` plan's
  `retry_helper.py` row: a parameter no caller may legitimately vary invites
  future regression; REQ-002 explicitly calls for removing the TOML key too.
- Enumerating `ipaddress.ip_network("10.0.0.0/8")` etc. and checking
  containment: rejected in favor of the simpler allow-list approach (Design
  decisions) — an allow-list is the minimal change that satisfies AC-1/AC-2
  without maintaining a private-LAN range list that could itself go stale.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Rewrite `_is_public_host()` (lines 25-36) to return `False` only for
   `host in ("127.0.0.1", "::1")`, and `True` for every other valid or
   invalid address (including private-LAN and other public IPs).
2. Remove `allow_public_bind: bool = False` from `EventBusConfig` (line 54).
3. Remove the `allow_public_bind`-related docstring text (line 44) and
   change `__post_init__`'s check (line 62) to
   `if _is_public_host(self.host): raise ValueError(...)`, unconditional.
4. Remove `allow_public_bind=data.get("allow_public_bind", False)` from
   `load_config()` (line 92).
5. Update the raised `ValueError`'s message (lines 63-66) to drop the
   "without allow_public_bind=true" clause, since there is no longer an
   override to mention.

### Method
Direct `Edit` at the 5 sites above.

### Details
Current (verified 2026-09-04, full function/class read):
```python
def _is_public_host(host: str) -> bool:
    """Return True if host is a public/wildcard address (0.0.0.0, ::)."""
    try:
        addr = ipaddress.ip_address(host)
        return (
            addr.is_unspecified
            or addr == ipaddress.IPv4Address("0.0.0.0")
            or addr == ipaddress.IPv6Address("::")
        )
    except ValueError:
        return True


@dataclass(frozen=True)
class EventBusConfig:
    ...
    host: str = "127.0.0.1"
    allow_public_bind: bool = False

    def __post_init__(self) -> None:
        ...
        if _is_public_host(self.host) and not self.allow_public_bind:
            raise ValueError(
                f"Event Bus bound to public address {self.host} without allow_public_bind=true. "
                "The API has no authentication — this is a security risk."
            )
```
After:
```python
def _is_public_host(host: str) -> bool:
    """Return True unless host is exactly the loopback address 127.0.0.1 or ::1."""
    return host not in ("127.0.0.1", "::1")


@dataclass(frozen=True)
class EventBusConfig:
    ...
    host: str = "127.0.0.1"

    def __post_init__(self) -> None:
        ...
        if _is_public_host(self.host):
            raise ValueError(
                f"Event Bus bound to non-loopback address {self.host}. "
                "The API has no authentication — this is a security risk."
            )
```
`load_config()`'s `EventBusConfig(...)` call drops the
`allow_public_bind=data.get("allow_public_bind", False)` line entirely.

## Compatibility considerations
`config/eventbus.toml` was confirmed (2026-09-04) to have no `host` or
`allow_public_bind` key set — it relies entirely on `EventBusConfig`'s
defaults, so this change does not affect the current deployed configuration.
If any external caller of `load_config()`/`EventBusConfig(...)` passes
`allow_public_bind=` as a keyword argument, that call now raises
`TypeError` — confirmed via `rg -n "allow_public_bind"` (2026-09-04) that
the only such caller is `tests/eventbus/test_eventbus_startup.py` (row 4,
coupled).

## Security considerations
This is the core security-hardening change of this Plan: closes the
confirmed private-LAN bind gap and removes the only bypass mechanism.

## Rollback considerations
Small, localized dataclass/function edit under version control; revert via
`git revert` if needed, together with row 4's test updates.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Private-LAN/wildcard/public addresses rejected; `127.0.0.1`/`::1` accepted; `allow_public_bind` no longer exists |

## Completion criteria
`_is_public_host()` rejects every address except `127.0.0.1`/`::1`;
`EventBusConfig` has no `allow_public_bind` field or TOML-key read.

## Out of scope
`get_config_path()`, `get_schema_path()`, `_REMOVED_CONFIG_KEYS` handling,
and the rest of `load_config()`'s TOML-parsing logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Verified exact match; no drift |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; `tests/eventbus/test_eventbus_startup.py` 16 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260904 | 20260904 | `docs/00_index.md`'s "Event Bus (config/ops)" row maps this file to `06_eventbus_05_configuration-and-operations.md` — updated per row 3's own Notes (shared update covering rows 1-3) |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260902-143334_loopbackonly_enforce_loopback_only_http_remove_external_publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091921_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-092757
- **Related target files**: scripts/eventbus/config.py
