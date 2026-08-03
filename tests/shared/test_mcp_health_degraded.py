"""Tests for McpServerHealthRegistry degraded state tracking."""

from unittest.mock import patch

from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

# --- McpServerHealthRegistry unit tests ---


def test_record_degraded_sets_degraded_state():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="unhealthy")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED


def test_record_degraded_stores_reason():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="queue full")
    assert registry.get_degraded_reason("srv1") == "queue full"


def test_record_degraded_no_reason():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1")
    assert registry.get_degraded_reason("srv1") is None


def test_degraded_does_not_make_unavailable():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="slow")
    assert not registry.is_unavailable("srv1")


def test_record_success_clears_degraded():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="bad")
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY
    assert registry.get_degraded_reason("srv1") is None


def test_record_degraded_idempotent():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="reason1")
    registry.record_degraded("srv1", reason="reason2")
    assert registry.get_degraded_reason("srv1") == "reason2"


def test_get_degraded_reason_unknown_server():
    registry = McpServerHealthRegistry()
    assert registry.get_degraded_reason("unknown") is None


def test_record_degraded_does_not_downgrade_unavailable():
    registry = McpServerHealthRegistry(failure_threshold=1)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE

    registry.record_degraded("srv1", reason="reachable but slow")

    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
    assert registry.get_degraded_reason("srv1") is None


def test_record_degraded_does_not_downgrade_half_open():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    # Cooldown elapsed immediately (0.0s); is_unavailable() transitions to HALF_OPEN.
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN

    registry.record_degraded("srv1", reason="reachable but slow")

    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN
    assert registry.get_degraded_reason("srv1") is None


def test_record_failure_below_threshold_sets_degraded():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED


def test_record_failure_reaches_threshold_sets_unavailable():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE


def test_is_unavailable_transitions_to_half_open_after_cooldown():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN


def test_record_success_from_half_open_sets_healthy():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY


def test_record_failure_from_half_open_sets_unavailable_and_resets_cooldown():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("time.monotonic", return_value=100.0):
        registry.record_failure("srv1")
        assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
        assert registry.is_unavailable("srv1") is True

        # Simulate cooldown elapsing — transition to HALF_OPEN
        with patch("time.monotonic", return_value=131.0):
            assert registry.is_unavailable("srv1") is False
            assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN

            # Another failure while HALF_OPEN — back to UNAVAILABLE, cooldown reset
            with patch("time.monotonic", return_value=132.0):
                registry.record_failure("srv1")
                assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
                assert registry.is_unavailable("srv1") is True


def test_record_success_resets_failure_count_and_unavailable_timestamp():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED
