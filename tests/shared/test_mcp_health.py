"""tests/shared/test_mcp_health.py
State-transition coverage for McpServerHealthRegistry: failure-threshold
accumulation, success-reset, HALF_OPEN cooldown/trial dispatch, and failed-trial
recovery back to UNAVAILABLE.
"""

from __future__ import annotations

import math
import time

import pytest
from shared.mcp_health import (
    HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
    HEALTH_REASON_SERVER_UNAVAILABLE,
    McpServerHealthRegistry,
    McpServerHealthState,
)


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


class TestHalfOpenSingleTrialFlag:
    """Per-server in-flight trial flag: single-shot acquire, release on outcomes."""

    def test_acquire_trial_is_single_shot(self) -> None:
        registry = McpServerHealthRegistry()
        assert registry.acquire_trial("srv") is True
        assert registry.acquire_trial("srv") is False

    def test_trial_in_flight_reflects_acquire_release(self) -> None:
        registry = McpServerHealthRegistry()
        assert registry.trial_in_flight("srv") is False
        registry.acquire_trial("srv")
        assert registry.trial_in_flight("srv") is True
        registry.release_trial("srv")
        assert registry.trial_in_flight("srv") is False

    def test_release_trial_is_idempotent(self) -> None:
        registry = McpServerHealthRegistry()
        registry.release_trial("srv")  # no error when never acquired
        registry.acquire_trial("srv")
        registry.release_trial("srv")
        registry.release_trial("srv")  # no error on double release

    def test_is_unavailable_transition_sets_trial_flag(self) -> None:
        """ACC-001: the UNAVAILABLE->HALF_OPEN transition atomically sets the flag."""
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.0
        )
        registry.record_failure("srv")
        assert registry.trial_in_flight("srv") is False

        registry.is_unavailable("srv")  # transitions to HALF_OPEN

        assert registry.get_state("srv") == McpServerHealthState.HALF_OPEN
        assert registry.trial_in_flight("srv") is True

    def test_successful_trial_releases_flag(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        registry.record_failure("srv")
        time.sleep(0.02)
        registry.is_unavailable("srv")  # -> HALF_OPEN, flag set
        assert registry.trial_in_flight("srv") is True

        registry.record_success("srv")

        assert registry.get_state("srv") == McpServerHealthState.HEALTHY
        assert registry.trial_in_flight("srv") is False

    def test_failed_trial_releases_flag(self) -> None:
        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        registry.record_failure("srv")
        time.sleep(0.02)
        registry.is_unavailable("srv")  # -> HALF_OPEN, flag set
        assert registry.trial_in_flight("srv") is True

        registry.record_failure("srv")

        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE
        assert registry.trial_in_flight("srv") is False


class TestRetryAfterDerivation:
    """cooldown_remaining()/retry_after_seconds(): boundary, state mapping, purity."""

    @staticmethod
    def _unavailable_registry(
        monkeypatch: pytest.MonkeyPatch, cooldown: float = 30.0
    ) -> tuple[McpServerHealthRegistry, dict[str, float]]:
        """Registry driven to UNAVAILABLE at fake-clock time 1000.0."""
        clock = {"now": 1000.0}
        monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
        registry = McpServerHealthRegistry(
            failure_threshold=3, half_open_cooldown_sec=cooldown
        )
        for _ in range(3):
            registry.record_failure("srv")
        return registry, clock

    def test_just_before_expiry_ceil_is_one_second(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry, clock = self._unavailable_registry(monkeypatch)
        clock["now"] = 1029.999
        remaining = registry.cooldown_remaining("srv")
        assert 0.0 < remaining < 1.0
        assert registry.retry_after_seconds("srv") == 1
        assert registry.retry_after_seconds("srv") == math.ceil(remaining)

    def test_at_and_after_expiry_is_zero_never_negative(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry, clock = self._unavailable_registry(monkeypatch)
        clock["now"] = 1030.0
        assert registry.cooldown_remaining("srv") == 0.0
        assert registry.retry_after_seconds("srv") == 0
        clock["now"] = 1200.0
        assert registry.cooldown_remaining("srv") == 0.0
        assert registry.retry_after_seconds("srv") == 0

    def test_state_mapping_only_unavailable_carries_an_int(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry, _ = self._unavailable_registry(monkeypatch)
        assert registry.retry_after_seconds("srv") is not None
        registry.record_success("srv")
        assert registry.get_state("srv") == McpServerHealthState.HEALTHY
        assert registry.retry_after_seconds("srv") is None
        assert registry.cooldown_remaining("srv") == 0.0
        registry.record_failure("srv")  # DEGRADED
        assert registry.get_state("srv") == McpServerHealthState.DEGRADED
        assert registry.retry_after_seconds("srv") is None
        assert registry.retry_after_seconds("unknown-key") is None
        assert registry.cooldown_remaining("unknown-key") == 0.0

    def test_half_open_carries_no_retry_after(self, monkeypatch: pytest.MonkeyPatch) -> None:
        registry, clock = self._unavailable_registry(monkeypatch)
        clock["now"] = 1031.0
        assert registry.is_unavailable("srv") is False  # UNAVAILABLE -> HALF_OPEN
        assert registry.get_state("srv") == McpServerHealthState.HALF_OPEN
        assert registry.retry_after_seconds("srv") is None
        assert registry.cooldown_remaining("srv") == 0.0

    def test_derivation_is_pure_no_state_or_trial_mutation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry, _ = self._unavailable_registry(monkeypatch)
        before = (
            dict(registry._states),
            dict(registry._failure_counts),
            dict(registry._unavailable_since),
            set(registry._half_open_trials),
        )
        for _ in range(5):
            registry.cooldown_remaining("srv")
            registry.retry_after_seconds("srv")
        after = (
            dict(registry._states),
            dict(registry._failure_counts),
            dict(registry._unavailable_since),
            set(registry._half_open_trials),
        )
        assert after == before
        # A repeated read must never perform the UNAVAILABLE -> HALF_OPEN
        # transition that is_unavailable()'s side effect would cause.
        assert registry.get_state("srv") == McpServerHealthState.UNAVAILABLE

    def test_reason_constants_match_the_hint_literal_values(self) -> None:
        assert HEALTH_REASON_SERVER_UNAVAILABLE == "server_unavailable"
        assert HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS == (
            "half_open_trial_in_progress"
        )
