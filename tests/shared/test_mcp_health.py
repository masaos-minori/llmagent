"""tests/shared/test_mcp_health.py
State-transition coverage for McpServerHealthRegistry: failure-threshold
accumulation, success-reset, HALF_OPEN cooldown/trial dispatch, and failed-trial
recovery back to UNAVAILABLE.
"""

from __future__ import annotations

import time

from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState


class TestFailureThresholdAndReset:
    """record_failure() accumulation and record_success() reset behavior."""

    def test_failures_below_threshold_stay_degraded(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        assert registry.record_failure("srv") == McpServerHealthState.DEGRADED
        assert registry.record_failure("srv") == McpServerHealthState.DEGRADED
        assert registry.get_state("srv") == McpServerHealthState.DEGRADED

    def test_failure_at_threshold_becomes_unavailable(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        registry.record_failure("srv")
        registry.record_failure("srv")
        assert registry.record_failure("srv") == McpServerHealthState.UNAVAILABLE
        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE

    def test_record_success_resets_to_healthy_and_clears_failure_count(
        self,
    ) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        registry.record_failure("srv")
        registry.record_failure("srv")
        registry.record_success("srv")
        assert registry.get_state("srv") == McpServerHealthState.HEALTHY

        # A subsequent failure must start over from DEGRADED, not jump to
        # UNAVAILABLE — proving the failure count was reset, not just the state.
        assert registry.record_failure("srv") == McpServerHealthState.DEGRADED


class TestHalfOpenCooldownAndTrialDispatch:
    """is_unavailable()'s cooldown-driven HALF_OPEN transition and one-shot trial semantics."""

    def test_is_unavailable_true_before_cooldown_elapses(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=10.0
        )
        registry.record_failure("srv")
        assert registry.is_unavailable("srv") is True
        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE

    def test_is_unavailable_transitions_to_half_open_after_cooldown(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        registry.record_failure("srv")
        time.sleep(0.02)

        # First call after cooldown: allows exactly one trial dispatch.
        assert registry.is_unavailable("srv") is False
        assert registry.get_state("srv") == McpServerHealthState.HALF_OPEN

    def test_is_unavailable_not_idempotent_after_half_open_trial_granted(
        self,
    ) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        registry.record_failure("srv")
        time.sleep(0.02)
        assert registry.is_unavailable("srv") is False  # trial granted
        # HALF_OPEN is not itself UNAVAILABLE, so a repeated call does not
        # block dispatch — callers must not assume repeated calls are
        # idempotent (per is_unavailable()'s own docstring).
        assert registry.is_unavailable("srv") is False
        assert registry.get_state("srv") == McpServerHealthState.HALF_OPEN


class TestHalfOpenTrialOutcomes:
    """record_failure()/record_success() from a HALF_OPEN trial state."""

    def _reach_half_open(
        self, registry: McpServerHealthRegistry, server_key: str = "srv"
    ) -> None:
        registry.record_failure(server_key)
        time.sleep(0.02)
        registry.is_unavailable(server_key)
        assert registry.get_state(server_key) == McpServerHealthState.HALF_OPEN

    def test_failed_trial_returns_to_unavailable_not_degraded(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        self._reach_half_open(registry)

        assert registry.record_failure("srv") == McpServerHealthState.UNAVAILABLE
        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE

    def test_failed_trial_resets_cooldown(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        self._reach_half_open(registry)
        registry.record_failure("srv")

        # Immediately after the failed trial, the cooldown must have reset —
        # dispatch stays blocked even though the original cooldown window
        # (from the first UNAVAILABLE transition) would have already elapsed.
        assert registry.is_unavailable("srv") is True

    def test_successful_trial_returns_to_healthy(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        self._reach_half_open(registry)

        registry.record_success("srv")
        assert registry.get_state("srv") == McpServerHealthState.HEALTHY
