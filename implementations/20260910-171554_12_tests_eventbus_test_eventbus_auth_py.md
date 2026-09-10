## Goal

Create `tests/eventbus/test_eventbus_auth.py`: positive/negative authorization tests for every route category (publish, subscribe, ack, nack, dlq list, dlq requeue, replay).

## Scope

- New test file `tests/eventbus/test_eventbus_auth.py` containing:
  - Positive authorization tests: authorized caller succeeds on each route category
  - Negative authorization tests: unauthorized/wrong-role caller rejected on each route category
- No other test file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- The FastAPI `TestClient` can be used for integration testing without starting the actual server.
- Each route category needs one authorized-success case and one unauthorized/wrong-role-rejection case.
- The authentication middleware will be registered in `scripts/eventbus/app.py` (REQ-002).
- The permission model will be wired into routes via `require_role()` dependencies (REQ-002, REQ-003, REQ-004).

## Design decisions

- **Test structure**: One test class per route category, with positive/negative sub-tests.
- **Authorization header**: Use `HTTPBearer` token format (`Authorization: Bearer <token>`).
- **Role-based access**: Test each role against routes it should/shouldn't access.

## Alternatives considered

- Parametrized tests for all route/role combinations: Would reduce code duplication but make failures harder to diagnose; separate tests more readable.
- Mocking the authentication middleware: Would isolate unit tests but miss integration-level bugs; integration tests preferred.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

Create a new test file covering positive/negative authorization tests for every route category.

### Method

1. Create test classes for each route category: `TestPublishAuth`, `TestSubscribeAuth`, `TestAckAuth`, `TestNackAuth`, `TestDlqListAuth`, `TestDlqRequeueAuth`, `TestReplayAuth`.
2. For each class, add positive test (authorized caller succeeds) and negative test (unauthorized/wrong-role caller rejected).
3. Use FastAPI `TestClient` for integration testing.

### Details

```python
#!/usr/bin/env python3
"""tests/eventbus/test_eventbus_auth.py

Positive/negative authorization tests for every EventBus route category.

Each route category has:
- One authorized-success case
- One unauthorized/wrong-role-rejection case

Precedent: scripts/mcp_servers/server.py::attach_auth_middleware() pattern
"""

import pytest
from fastapi.testclient import TestClient

# Note: These tests require the EventBus app to have the authentication middleware
# registered (scripts/eventbus/app.py) and the permission model wired into routes
# (scripts/eventbus/auth.py). They cannot be run until those changes land.

class TestPublishAuth:
    """Tests for POST /publish authorization."""
    
    def test_publish_with_valid_publisher_token(self, client: TestClient) -> None:
        """Authorized publisher can publish events."""
        response = client.post(
            "/publish",
            json={"topic": "test", "payload": {"key": "value"}},
            headers={"Authorization": "Bearer publisher-token"},
        )
        assert response.status_code == 200
    
    def test_publish_without_token(self, client: TestClient) -> None:
        """Unauthenticated request to /publish is rejected."""
        response = client.post("/publish", json={"topic": "test", "payload": {"key": "value"}})
        assert response.status_code == 401

class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""
    
    def test_subscribe_with_valid_consumer_token(self, client: TestClient) -> None:
        """Authorized consumer can subscribe to events."""
        response = client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert response.status_code == 200
    
    def test_subscribe_as_wrong_role(self, client: TestClient) -> None:
        """Non-consumer role cannot subscribe."""
        response = client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 403

class TestAckAuth:
    """Tests for POST /events/{event_id}/ack authorization."""
    
    def test_ack_with_valid_consumer_token(self, client: TestClient) -> None:
        """Authorized consumer can ack events."""
        response = client.post(
            "/events/test-event-id/ack",
            params={"consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert response.status_code == 200
    
    def test_ack_without_token(self, client: TestClient) -> None:
        """Unauthenticated request to /ack is rejected."""
        response = client.post("/events/test-event-id/ack", params={"consumer_id": "consumer_a"})
        assert response.status_code == 401

class TestNackAuth:
    """Tests for POST /nack authorization."""
    
    def test_nack_with_valid_consumer_token(self, client: TestClient) -> None:
        """Authorized consumer can nack events."""
        response = client.post(
            "/nack",
            params={"event_id": "test-event-id"},
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert response.status_code == 200
    
    def test_nack_as_wrong_role(self, client: TestClient) -> None:
        """Non-consumer role cannot nack events."""
        response = client.post(
            "/nack",
            params={"event_id": "test-event-id"},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 403

class TestDlqListAuth:
    """Tests for GET /dlq authorization."""
    
    def test_dlq_list_with_valid_operator_token(self, client: TestClient) -> None:
        """Authorized operator can list DLQ entries."""
        response = client.get(
            "/dlq",
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 200
    
    def test_dlq_list_without_token(self, client: TestClient) -> None:
        """Unauthenticated request to /dlq is rejected."""
        response = client.get("/dlq")
        assert response.status_code == 401

class TestDlqRequeueAuth:
    """Tests for POST /dlq/{event_id}/requeue authorization."""
    
    def test_dlq_requeue_with_valid_operator_token(self, client: TestClient) -> None:
        """Authorized operator can requeue DLQ entries."""
        response = client.post(
            "/dlq/test-event-id/requeue",
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 200
    
    def test_dlq_requeue_as_wrong_role(self, client: TestClient) -> None:
        """Non-operator role cannot requeue DLQ entries."""
        response = client.post(
            "/dlq/test-event-id/requeue",
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert response.status_code == 403

class TestReplayAuth:
    """Tests for GET /replay authorization."""
    
    def test_replay_with_valid_operator_token(self, client: TestClient) -> None:
        """Authorized operator can replay events."""
        response = client.get(
            "/replay",
            params={"since_seq": 0, "limit": 100},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 200
    
    def test_replay_without_token(self, client: TestClient) -> None:
        """Unauthenticated request to /replay is rejected."""
        response = client.get("/replay", params={"since_seq": 0, "limit": 100})
        assert response.status_code == 401
```

## Compatibility considerations

- The test fixture `client` must provide a FastAPI `TestClient` instance with the authenticated app.
- The test tokens (`publisher-token`, `consumer-token`, `operator-token`) are arbitrary strings used only for testing.

## Security considerations

- **No secret leakage**: Test tokens are short-lived and not committed to version control.
- **Test data isolation**: All test requests use temporary event IDs that don't exist in production.

## Rollback considerations

- Rolling back these tests means removing them; the original behavior would still be tested by the existing tests.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` — all new tests should pass.
- Run full EventBus suite: `uv run pytest tests/eventbus/ -q` (baseline: 169 passed + 1 pre-existing unrelated failure).

## Completion criteria

- [ ] `tests/eventbus/test_eventbus_auth.py` created
- [ ] Positive authorization test for each route category
- [ ] Negative authorization test for each route category
- [ ] All auth tests passing
- [ ] Full EventBus suite passes at baseline (no regressions)

## Out of scope

- Adding authorization tests for monitoring endpoints (defined in ADR but no code change in this Plan).
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create test file with positive/negative tests | Pending | — | — | |
| 2 | Add publish auth tests | Pending | — | — | |
| 3 | Add subscribe auth tests | Pending | — | — | |
| 4 | Add ack auth tests | Pending | — | — | |
| 5 | Add nack auth tests | Pending | — | — | |
| 6 | Add dlq list auth tests | Pending | — | — | |
| 7 | Add dlq requeue auth tests | Pending | — | — | |
| 8 | Add replay auth tests | Pending | — | — | |
| 9 | Validate tests pass | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: tests/eventbus/test_eventbus_auth.py
