# Implementation Procedure: Add authorization validation tests for ACK/NACK endpoints

## Goal

Update `tests/eventbus/test_eventbus_ack_nack.py` to add tests for authorization validation in the ACK/NACK endpoints, including principal ownership validation and event delivery verification.

## Scope

- Add tests for principal ownership validation when ACKing/NACKing an event.
- Add tests for event delivery verification before accepting ACK/NACK.
- Add tests for mandatory consumer_id enforcement.
- Update existing tests to use Principal-based authentication.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current test file has basic ACK/NACK endpoint tests.
- D: The current test file uses `auth_token="test-token"` for authentication.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Empty consumer_id semantics**: Empty consumer_id is permitted only when no authorization context is available (legacy mode). When authorization context exists, consumer_id must be non-empty.
- **Test isolation**: Each test should have its own isolated database and configuration.

## Alternatives considered

- **Keep role-based authorization**: Continue using `_role: Role` for ACK/NACK authorization. This was rejected because it doesn't provide per-consumer/per-topic granularity needed for REQ-001—REQ-007.
- **Separate admin ACK/NACK endpoint**: Create a separate operator-only endpoint for administrative ACK/NACK. This was rejected because it requires additional endpoint definition and authorization wiring.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original test file content.
- The revert is mechanical — no semantic changes beyond restoring original test cases.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

#### Step 1: Add new imports (REQ-001)

Add new imports after the existing imports (after line 10):

Current code:
```python
import pytest
```

New code:
```python
import pytest

from eventbus.auth import Principal, Role
```

#### Step 2: Add Principal-based fixture (REQ-001)

Add a new fixture after the existing `db` fixture (after line 17):

Current code:
```python
@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))
```

New code:
```python
@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))


@pytest.fixture
def principal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Create a TestClient with Principal-based authentication."""
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8017,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="principal-token",
        # Per-role tokens for principal-based auth
        publisher_token="publisher-token",
        consumer_token="consumer-token",
        operator_token="operator-token",
        monitoring_token="monitoring-token",
        admin_token="admin-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c
```

Key changes:
- Added `principal_client` fixture with Principal-based authentication.
- Uses `consumer-token` for consumer role authorization.

#### Step 3: Add tests for principal ownership validation (REQ-002, REQ-008)

Add new test methods to the appropriate test classes (after the existing tests):

Current code:
```python
class TestNackEvent:
    ...
```

New code:
```python
class TestNackEvent:
    ...

    def test_nack_event_principal_ownership_validation(self, principal_client: TestClient) -> None:
        """NACK endpoint validates principal owns the requested consumer ID."""
        body = _event()
        resp = principal_client.post("/publish", json=body)
        assert resp.status_code == 200

        # Try to NACK with a consumer ID not owned by the principal
        resp = principal_client.post(
            "/nack", params={"event_id": body['event_id'], "consumer_id": "unauthorized-consumer"}
        )
        assert resp.status_code == 403

    def test_nack_event_delivery_verification(self, principal_client: TestClient) -> None:
        """NACK endpoint verifies event was delivered to the consumer before accepting NACK."""
        body = _event()
        resp = principal_client.post("/publish", json=body)
        assert resp.status_code == 200

        # Try to NACK without first delivering the event to the consumer
        resp = principal_client.post(
            "/nack", params={"event_id": body['event_id'], "consumer_id": "consumer-A"}
        )
        assert resp.status_code == 409

    def test_nack_event_mandatory_consumer_id(self, principal_client: TestClient) -> None:
        """NACK endpoint requires consumer_id parameter."""
        body = _event()
        resp = principal_client.post("/publish", json=body)
        assert resp.status_code == 200

        # Try to NACK without providing consumer_id
        resp = principal_client.post("/nack", params={"event_id": body['event_id']})
        assert resp.status_code == 400
```

Key changes:
- Added `test_nack_event_principal_ownership_validation`: Tests that NACK endpoint rejects requests where the principal doesn't own the requested consumer ID.
- Added `test_nack_event_delivery_verification`: Tests that NACK endpoint rejects requests where the event wasn't delivered to the consumer.
- Added `test_nack_event_mandatory_consumer_id`: Tests that NACK endpoint requires consumer_id parameter.

### Details

- REQ-001: Principal-based authentication added to ACK/NACK endpoint tests.
- REQ-002: Principal ownership validation tested for ACK endpoint.
- REQ-003: Event delivery verification tested for ACK endpoint.
- REQ-004: Mandatory consumer_id enforced for ACK endpoint.
- REQ-005: Consumer-less fallback removed from ACK endpoint.
- REQ-006: Administrative override handled separately (not tested here).
- REQ-007: Mandatory consumer_id enforced for NACK endpoint.
- REQ-008: Principal ownership validation tested for NACK endpoint.
- REQ-009: Event delivery verification tested for NACK endpoint.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original test file content.
- The revert is mechanical — no semantic changes beyond restoring original test cases.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_ack_nack.py | Unit: ownership validation contract; Integration: consumer mismatch scenarios | uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v | New tests pass; existing tests unchanged |
| scripts/eventbus/ack_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/ack_route.py | Type checking | uv run mypy scripts/eventbus/ack_route.py | No new type errors |

## Completion criteria

- [ ] Principal-based authentication added to ACK/NACK endpoint tests.
- [ ] Principal ownership validation tested for ACK/NACK endpoint.
- [ ] Event delivery verification tested for ACK/NACK endpoint.
- [ ] Mandatory consumer_id enforced for ACK/NACK endpoint.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new imports for Principal | Pending | — | — | |
| 2 | Add Principal-based fixture | Pending | — | — | |
| 3 | Add tests for principal ownership validation | Pending | — | — | |
| 4 | Add tests for event delivery verification | Pending | — | — | |
| 5 | Add tests for mandatory consumer_id enforcement | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-203335
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
