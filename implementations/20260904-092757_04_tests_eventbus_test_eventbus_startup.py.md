## Goal
Update this file's tests for row 1's extended `_is_public_host()` (allow-list
of `127.0.0.1`/`::1` only) and removed `allow_public_bind`, and add the
private-LAN-rejection coverage REQ-005/AC-7 requires.

## Scope
- **In-Scope**: `test_is_public_host_private_192/10/172` (verified
  2026-09-04, lines 29-38, currently asserting `False` — must flip to
  `True`); `test_is_public_host_valid_hostname` (lines 40-42, unaffected —
  already asserts `True`); `test_safe_bind_127_0_0_1`/
  `test_safe_bind_loopback_v6` (lines 45-70, unaffected); `test_unsafe_bind_0000_succeeds_with_override`
  (lines 100-111, must be removed — the override no longer exists);
  `test_private_ip_allowed_without_override` (lines 114-124, must be removed
  or inverted — this test currently documents the exact gap this Plan
  closes).
- **Out-of-Scope**: any test in this file unrelated to `_is_public_host()`/
  `EventBusConfig` bind validation — confirmed by direct read that this
  entire 124-line file is scoped to bind-address safety guards only, no
  out-of-scope tests exist here.

## Assumptions
- Must execute together with, or after, row 1's `scripts/eventbus/config.py`
  edit — every assertion in this file directly exercises `_is_public_host()`
  and `EventBusConfig`'s validation, both of which row 1 changes.

## Design decisions
- Flip `test_is_public_host_private_192()`, `test_is_public_host_private_10()`,
  `test_is_public_host_private_172()` (lines 29-38) from asserting `False`
  to asserting `True` — these addresses are now correctly classified as
  public/non-loopback per row 1's allow-list logic.
- Remove `test_unsafe_bind_0000_succeeds_with_override()` (lines 100-111)
  entirely — `allow_public_bind` no longer exists as a constructor
  parameter, so this test would fail with `TypeError` at construction, not
  merely produce a wrong assertion.
- Remove `test_private_ip_allowed_without_override()` (lines 114-124)
  entirely and replace it with a new test
  `test_private_ip_rejected()` asserting `EventBusConfig(..., host="192.168.1.1")`
  now raises `ValueError` — this is the direct regression test for the gap
  the Plan's Problem section identifies.
- Add new tests for `10.x`/`172.16.x` addresses rejected at `EventBusConfig`
  construction (not just at the `_is_public_host()` unit level), for
  symmetry with the existing `test_unsafe_bind_0000_fails_without_override()`/
  `test_unsafe_bind_ipv6_wildcard_fails_without_override()` pattern (lines
  77-98).

## Alternatives considered
- Keeping `test_unsafe_bind_0000_succeeds_with_override()` but changing it to
  expect a `TypeError`: rejected — a test asserting a removed parameter's
  absence via `TypeError` is testing Python's own call-signature mechanics,
  not this Plan's actual security behavior; simple removal is clearer.

## Implementation
### Target file
`tests/eventbus/test_eventbus_startup.py`

### Procedure
1. Flip the three private-address assertions (lines 29-38) from `is False`
   to `is True`.
2. Remove `test_unsafe_bind_0000_succeeds_with_override()` (lines 100-111).
3. Replace `test_private_ip_allowed_without_override()` (lines 114-124) with
   `test_private_ip_rejected()`, asserting
   `pytest.raises(ValueError, match="bound to non-loopback address")` for
   `host="192.168.1.1"` (matching row 1's updated error message wording —
   re-confirm the exact message string against row 1's final implementation
   before finalizing the `match=` regex).
4. Add `test_unsafe_bind_private_10_fails()` and
   `test_unsafe_bind_private_172_fails()`, mirroring the existing
   `test_unsafe_bind_0000_fails_without_override()` pattern (lines 77-87)
   for `host="10.0.0.1"` and `host="172.16.0.1"`.

### Method
Direct `Edit`/test addition at the sites above.

### Details
Current (verified 2026-09-04, lines 29-38):
```python
def test_is_public_host_private_192() -> None:
    assert _is_public_host("192.168.1.1") is False


def test_is_public_host_private_10() -> None:
    assert _is_public_host("10.0.0.1") is False


def test_is_public_host_private_172() -> None:
    assert _is_public_host("172.16.0.1") is False
```
After:
```python
def test_is_public_host_private_192() -> None:
    assert _is_public_host("192.168.1.1") is True


def test_is_public_host_private_10() -> None:
    assert _is_public_host("10.0.0.1") is True


def test_is_public_host_private_172() -> None:
    assert _is_public_host("172.16.0.1") is True
```
Current (verified 2026-09-04, lines 114-124):
```python
def test_private_ip_allowed_without_override() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="192.168.1.1",
    )
    assert cfg.host == "192.168.1.1"
```
After:
```python
def test_private_ip_rejected() -> None:
    with pytest.raises(ValueError, match="bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="192.168.1.1",
        )
```

## Compatibility considerations
Coupled to row 1 — must land after it, since these tests exercise its
edited functions/classes directly.

## Security considerations
This file's edits are themselves the regression coverage for row 1's
security fix.

## Rollback considerations
Test-only edit under version control; revert via `git revert` if needed,
together with row 1.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_startup.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Private-LAN/wildcard/public addresses rejected at both `_is_public_host()` and `EventBusConfig` construction; `127.0.0.1`/`::1` accepted; no reference to `allow_public_bind` remains |

## Completion criteria
No test in this file references `allow_public_bind`; every private-LAN
address is confirmed rejected at both levels (function and dataclass).

## Out of scope
None — this entire file is in scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 1's own edit |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260902-143334_loopbackonly_enforce_loopback_only_http_remove_external_publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091921_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-092757
- **Related target files**: tests/eventbus/test_eventbus_startup.py
