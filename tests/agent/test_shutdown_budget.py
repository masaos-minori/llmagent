"""tests/agent/test_shutdown_budget.py

Unit tests for agent/shutdown_budget.py: ShutdownBudget arming, first-request-wins
idempotence, remaining() clamping, phase transitions, the step names, and the
outcome vocabulary (cliplc004 REQ-001, REQ-002, REQ-012).
"""

from __future__ import annotations

import dataclasses

import pytest
from agent.shutdown_budget import (
    SHUTDOWN_STEPS,
    ShutdownBudget,
    ShutdownOutcome,
    ShutdownPhase,
    ShutdownReport,
    ShutdownStepRecord,
)


class FakeClock:
    """Injectable monotonic clock: tests advance it instead of sleeping."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestArming:
    def test_unarmed_budget_is_accepting_and_keeps_the_full_window(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        assert budget.armed is False
        assert budget.phase is ShutdownPhase.ACCEPTING
        assert budget.remaining() == 45.0

    def test_first_arm_starts_the_deadline_and_moves_to_draining(self) -> None:
        clock = FakeClock()
        budget = ShutdownBudget(45.0, clock=clock)
        assert budget.arm() is True
        assert budget.armed is True
        assert budget.phase is ShutdownPhase.DRAINING

    def test_later_arms_return_false_and_never_extend_the_deadline(self) -> None:
        clock = FakeClock()
        budget = ShutdownBudget(45.0, clock=clock)
        assert budget.arm() is True
        clock.advance(40.0)
        assert budget.arm() is False
        assert budget.arm() is False
        # A re-arm that extended the deadline would reset remaining() to 45.0.
        assert budget.remaining() == 5.0

    def test_negative_total_rejected(self) -> None:
        with pytest.raises(ValueError, match="total_seconds"):
            ShutdownBudget(-1.0, clock=FakeClock())


class TestRemainingClamping:
    def test_remaining_counts_down_with_the_clock(self) -> None:
        clock = FakeClock()
        budget = ShutdownBudget(45.0, clock=clock)
        budget.arm()
        clock.advance(20.0)
        assert budget.remaining() == 25.0

    def test_remaining_is_zero_at_the_deadline(self) -> None:
        clock = FakeClock()
        budget = ShutdownBudget(45.0, clock=clock)
        budget.arm()
        clock.advance(45.0)
        assert budget.remaining() == 0.0

    def test_remaining_stays_zero_past_the_deadline(self) -> None:
        clock = FakeClock()
        budget = ShutdownBudget(45.0, clock=clock)
        budget.arm()
        clock.advance(60.0)
        assert budget.remaining() == 0.0


class TestPhaseTransitions:
    def test_arm_moves_accepting_to_draining(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        budget.arm()
        assert budget.phase is ShutdownPhase.DRAINING

    def test_mark_closed_moves_draining_to_closed(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        budget.arm()
        budget.mark_closed()
        assert budget.phase is ShutdownPhase.CLOSED

    def test_rearm_after_close_does_not_reopen_acceptance(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        budget.arm()
        budget.mark_closed()
        assert budget.arm() is False
        assert budget.phase is ShutdownPhase.CLOSED


class TestInterruptChannel:
    def test_interrupt_defaults_to_false(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        assert budget.interrupt_requested is False

    def test_request_interrupt_is_visible_and_idempotent(self) -> None:
        budget = ShutdownBudget(45.0, clock=FakeClock())
        budget.request_interrupt()
        budget.request_interrupt()
        assert budget.interrupt_requested is True


class TestOutcomeVocabulary:
    def test_the_five_outcome_values(self) -> None:
        assert [o.value for o in ShutdownOutcome] == [
            "completed",
            "timed_out",
            "failed",
            "not_started",
            "outcome_unknown",
        ]

    def test_the_eight_step_names_in_sequence_order(self) -> None:
        assert SHUTDOWN_STEPS == (
            "enter_shutdown",
            "settle_writers",
            "persist_snapshot",
            "checkpoint",
            "backup",
            "terminate_lifecycles",
            "close_hooks",
            "report",
        )


class TestStepRecordAndReport:
    def test_record_names_its_step_outcome_elapsed_and_detail(self) -> None:
        record = ShutdownStepRecord(
            name="checkpoint",
            outcome=ShutdownOutcome.TIMED_OUT,
            elapsed_s=30.0,
            detail="deadline exhausted",
        )
        assert record.name == "checkpoint"
        assert record.outcome is ShutdownOutcome.TIMED_OUT
        assert record.elapsed_s == 30.0
        assert record.detail == "deadline exhausted"

    def test_record_is_frozen(self) -> None:
        record = ShutdownStepRecord(
            name="backup", outcome=ShutdownOutcome.COMPLETED, elapsed_s=1.0
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.outcome = ShutdownOutcome.FAILED

    def test_report_carries_records_and_the_counts_the_report_step_prints(self) -> None:
        record = ShutdownStepRecord(
            name="settle_writers",
            outcome=ShutdownOutcome.OUTCOME_UNKNOWN,
            elapsed_s=10.0,
            detail="writer still running",
        )
        report = ShutdownReport(
            records=(record,), refused_write_count=3, unsettled_writers=("worker-1",)
        )
        assert report.records == (record,)
        assert report.refused_write_count == 3
        assert report.unsettled_writers == ("worker-1",)

    def test_report_is_frozen(self) -> None:
        report = ShutdownReport()
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.refused_write_count = 1
