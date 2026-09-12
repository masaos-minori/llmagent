## Goal

Un-skip `test_subscribe_with_valid_consumer_token` in `tests/eventbus/test_eventbus_auth.py` and add replacement test that verifies disconnect detection works (REQ-001, REQ-003).

## Scope

- **In-Scope**: Modifying `tests/eventbus/test_eventbus_auth.py` to un-skip the SSE subscribe test
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The timeout-based disconnect detection added to `scripts/eventbus/subscribe_route.py` will make the test pass without hanging
- The test can now reliably detect client disconnect under TestClient's ASGI transport
- The test should complete within a bounded time after the client disconnects

## Design decisions

- Un-skip the `test_subscribe_with_valid_consumer_token` test
- Add a replacement test that verifies disconnect detection works under TestClient
- The test should verify that the generator exits cleanly after the client disconnects

## Alternatives considered

- Keeping the test skipped and adding a separate test for disconnect detection — would leave the original test incomplete
- Adding a timeout to the test using `pytest-timeout` — would mask the underlying issue rather than fix it

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. Un-skip the `test_subscribe_with_valid_consumer_token` test
2. Add a replacement test that verifies disconnect detection works under TestClient
3. Ensure the test completes within a bounded time

### Method

For the test update:
- Remove the `@pytest.mark.skip` decorator from the `test_subscribe_with_valid_consumer_token` test
- Add a replacement test that verifies disconnect detection works under TestClient

### Details

#### Step 1: Update test class

```python
# Before:
class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    @pytest.mark.skip(
        reason="Hangs indefinitely: the /subscribe SSE generator never detects "
        "this client disconnecting (TestClient's in-process ASGI transport never "
        "delivers http.disconnect here, and sub.disconnect only fires on broker "
        "queue overflow), regardless of .stream()/.send(stream=True)/timeout — see "
        "issues/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md"
    )
    def test_subscribe_with_valid_consumer_token(self) -> None:
        """Authorized consumer can subscribe to events."""
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        ) as response:
            assert response.status_code == 200

    def test_subscribe_without_token(self) -> None:
        """Unauthenticated request to /subscribe is rejected."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
        )
        assert response.status_code == 401

    def test_subscribe_as_wrong_role(self) -> None:
        """Non-consumer role cannot subscribe."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 401

# After:
class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_subscribe_with_valid_consumer_token(self) -> None:
        """Authorized consumer can subscribe to events."""
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        ) as response:
            assert response.status_code == 200

    def test_subscribe_with_timeout_disconnect_detection(self) -> None:
        """Verify disconnect detection works under TestClient when no events arrive."""
        # This test verifies the timeout-based disconnect detection mechanism
        # added to _sse_gen's live-delivery loop. Under TestClient, even if
        # is_disconnected() doesn't fire, the lack of incoming events will
        # eventually trigger the timeout and clean up the generator.
        import time
        
        start_time = time.time()
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_b"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        ) as response:
            assert response.status_code == 200
            # Read one event to confirm the stream is working
            data = b""
            while True:
                chunk = response.read(1)
                if not chunk:
                    break
                data += chunk
                if b"\n\n" in data:
                    break
        
        elapsed = time.time() - start_time
        # The stream should close within the idle timeout window (default 60 seconds)
        # plus some margin for network latency
        assert elapsed < 120, f"Stream did not close within expected timeout: {elapsed}s"

    def test_subscribe_without_token(self) -> None:
        """Unauthenticated request to /subscribe is rejected."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
        )
        assert response.status_code == 401

    def test_subscribe_as_wrong_role(self) -> None:
        """Non-consumer role cannot subscribe."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 401
```

## Compatibility considerations

- The test fixture uses the shared token mechanism, which should work alongside per-role tokens
- The test should complete within a bounded time after the client disconnects
- The test should not rely on `pytest-timeout` to unblock it

## Security considerations

- The timeout-based disconnect detection prevents resource leaks in production by ensuring generators are cleaned up even when `is_disconnected()` doesn't fire
- This improves security by preventing indefinite resource consumption from abandoned subscriptions

## Rollback considerations

- If the timeout-based disconnect causes premature closure of active subscriptions during periods of low event frequency, roll back to the previous state where only `is_disconnected()` was used
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py::subscribe | Integration: verify disconnect detection under TestClient | pytest tests/eventbus/test_eventbus_auth.py::TestSubscribeAuth::test_subscribe_with_valid_consumer_token | Test completes without hanging |
| scripts/eventbus/subscribe_route.py::subscribe | Integration: verify disconnect detection under uvicorn | Manual: run eventbus, connect /subscribe, close client, check broker subscription freed | Subscription removed within timeout |
| scripts/eventbus/subscribe_route.py::_sse_gen | Unit: verify timeout triggers when no events arrive | pytest with mock broker that stops sending events | Generator exits after timeout |
| scripts/eventbus/subscribe_route.py::_sse_gen | Unit: verify existing disconnect mechanisms still work | pytest with mock sub.disconnect set / None sentinel sent | Generator exits via original mechanism |

## Completion criteria

- [ ] `@pytest.mark.skip` decorator removed from `test_subscribe_with_valid_consumer_token`
- [ ] Replacement test added that verifies disconnect detection works under TestClient
- [ ] Tests pass with the new disconnect detection model

## Out of scope

- Changes to `scripts/eventbus/subscribe_route.py` (handled in separate procedure document)
- Changes to config files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Un-skip test_subscribe_with_valid_consumer_token | Pending | — | — | |
| 2 | Add replacement test for disconnect detection | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-113940_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: tests/eventbus/test_eventbus_auth.py
