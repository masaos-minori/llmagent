"""tests/agent/services/test_maintenance_jobs.py

Behavior tests for MaintenanceJobRegistry on the in-process job record.

Contracts under test (REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4):
- every run registered through the registry carries job id, operation, target store,
  approval level, cancelability, state, progress, and terminal outcome;
- a second write job against a store that already has one running is refused, and the
  refusal names the running job id rather than queueing;
- a cooperative job is interrupted by setting its event, and a `not_cancelable` job
  refuses cancellation with a stated reason;
- approval is a property of the operation: `confirm` requires a recorded grant and
  `guard` requires the grant plus the stored precondition;
- a run whose awaiter was cancelled ends `outcome_unknown` and is never verified.

The registry holds no database connection, so these tests build it directly.
"""

from __future__ import annotations

import pytest
from agent.services.maintenance_jobs import (
    ApprovalDecision,
    ApprovalLevel,
    Cancelability,
    JobConflictError,
    JobState,
    MaintenanceJob,
    MaintenanceJobRegistry,
    StoreTarget,
)


def _register(
    registry: MaintenanceJobRegistry,
    *,
    operation: str = "checkpoint",
    store: StoreTarget = StoreTarget.SESSION,
    level: ApprovalLevel = ApprovalLevel.NONE,
    cancelability: Cancelability = Cancelability.COOPERATIVE,
    is_write: bool = True,
    precondition=None,
) -> MaintenanceJob:
    """Register one job with the default single-operation shape."""
    return registry.register(
        operation=operation,
        store=store,
        approval_level=level,
        cancelability=cancelability,
        is_write=is_write,
        precondition=precondition,
    )


class TestJobRecord:
    def test_record_carries_the_fields_the_plan_lists(self):
        registry = MaintenanceJobRegistry()
        job = _register(
            registry,
            operation="vacuum",
            store=StoreTarget.RAG,
            level=ApprovalLevel.GUARD,
            cancelability=Cancelability.NOT_CANCELABLE,
        )
        assert job.job_id
        assert job.operation == "vacuum"
        assert job.store is StoreTarget.RAG
        assert job.approval_level is ApprovalLevel.GUARD
        assert job.cancelability is Cancelability.NOT_CANCELABLE
        assert job.state is JobState.PENDING
        assert job.progress == 0
        assert job.verified is False
        assert job.session_target == ""

    def test_session_target_is_passed_in_by_the_caller(self):
        registry = MaintenanceJobRegistry()
        job = registry.register(
            operation="reindex",
            store=StoreTarget.SESSION,
            approval_level=ApprovalLevel.NONE,
            cancelability=Cancelability.COOPERATIVE,
            session_target="gen-7",
        )
        assert job.session_target == "gen-7"

    def test_job_ids_are_unique(self):
        registry = MaintenanceJobRegistry()
        first = _register(registry, operation="checkpoint")
        registry.finish(first, outcome="completed", verified=True)
        second = _register(registry, operation="checkpoint")
        assert first.job_id != second.job_id

    def test_lookup_returns_the_record_by_id(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        assert registry.lookup(job.job_id) is job
        assert registry.lookup("no-such-job") is None


class TestStateTransitions:
    def test_pending_to_running_to_completed(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        assert job.state is JobState.RUNNING
        assert job.started_at is not None
        registry.record_progress(job, 250)
        assert job.progress == 250
        registry.finish(job, outcome="completed", verified=True)
        assert job.state is JobState.COMPLETED
        assert job.outcome == "completed"
        assert job.verified is True

    def test_failure_is_terminal_and_never_verified(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        registry.finish(
            job,
            outcome="operation failed",
            verified=False,
            state=JobState.FAILED,
        )
        assert job.state is JobState.FAILED
        assert job.verified is False

    def test_starting_a_terminal_job_is_rejected(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        registry.finish(job, outcome="completed", verified=True)
        with pytest.raises(RuntimeError, match=job.job_id):
            registry.start(job)

    def test_outcome_unknown_when_the_awaiter_is_cancelled(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        registry.mark_outcome_unknown(job)
        assert job.state is JobState.OUTCOME_UNKNOWN
        assert job.verified is False
        # A run that never reported its postcondition cannot claim success later.
        with pytest.raises(RuntimeError, match="outcome_unknown"):
            registry.finish(job, outcome="completed", verified=True)

    def test_store_guard_is_released_after_a_terminal_state(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        registry.finish(job, outcome="completed", verified=True)
        second = _register(registry)
        assert second.state is JobState.PENDING


class TestOneWriterPerStore:
    def test_second_write_job_is_refused_naming_the_running_job(self):
        registry = MaintenanceJobRegistry()
        first = _register(registry, operation="vacuum")
        registry.start(first)
        with pytest.raises(JobConflictError) as excinfo:
            _register(registry, operation="purge")
        assert excinfo.value.running_job_id == first.job_id
        assert first.job_id in str(excinfo.value)

    def test_read_only_runs_do_not_take_the_writer_slot(self):
        registry = MaintenanceJobRegistry()
        writer = _register(registry, operation="vacuum")
        registry.start(writer)
        reader = _register(
            registry,
            operation="health",
            level=ApprovalLevel.NONE,
            is_write=False,
        )
        registry.start(reader)
        assert reader.state is JobState.RUNNING
        assert registry.running_writer(StoreTarget.SESSION) == writer.job_id

    def test_a_second_read_only_run_is_allowed_against_the_same_store(self):
        registry = MaintenanceJobRegistry()
        first = _register(registry, operation="stats", is_write=False)
        registry.start(first)
        second = _register(registry, operation="health", is_write=False)
        registry.start(second)
        assert first.job_id != second.job_id

    def test_other_stores_are_not_blocked(self):
        registry = MaintenanceJobRegistry()
        session_writer = _register(registry, operation="vacuum")
        registry.start(session_writer)
        rag_writer = _register(registry, operation="reindex", store=StoreTarget.RAG)
        registry.start(rag_writer)
        assert rag_writer.state is JobState.RUNNING


class TestApprovalLevels:
    def test_none_level_needs_no_grant(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="stats", is_write=False)
        decision = registry.authorize(job, confirmed=False)
        assert decision.approved is True
        registry.start(job)
        assert job.state is JobState.RUNNING

    def test_confirm_level_requires_a_recorded_grant(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="reindex", level=ApprovalLevel.CONFIRM)
        refused = registry.authorize(job, confirmed=False)
        assert refused.approved is False
        with pytest.raises(RuntimeError, match=job.job_id):
            registry.start(job)
        granted = registry.authorize(job, confirmed=True)
        assert granted.approved is True
        registry.start(job)
        assert job.state is JobState.RUNNING

    def test_grant_is_bound_to_the_run_that_requested_it(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="delete", level=ApprovalLevel.CONFIRM)
        registry.authorize(job, confirmed=True)
        other = _register(registry, operation="prune", level=ApprovalLevel.CONFIRM)
        assert registry.authorize(other, confirmed=False).approved is False

    def test_guard_level_requires_the_stored_precondition(self):
        registry = MaintenanceJobRegistry()
        job = _register(
            registry,
            operation="vacuum",
            level=ApprovalLevel.GUARD,
            precondition=lambda: True,
        )
        decision = registry.authorize(job, confirmed=True)
        assert decision.approved is True
        assert decision.precondition_ok is True
        registry.start(job)
        assert job.state is JobState.RUNNING

    def test_guard_level_refuses_when_the_precondition_does_not_hold(self):
        registry = MaintenanceJobRegistry()
        job = _register(
            registry,
            operation="vacuum",
            level=ApprovalLevel.GUARD,
            precondition=lambda: False,
        )
        decision = registry.authorize(job, confirmed=True)
        assert decision.approved is False
        assert decision.precondition_ok is False
        with pytest.raises(RuntimeError, match=job.job_id):
            registry.start(job)


class TestCancellation:
    def test_cooperative_job_is_interrupted_through_the_event(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="reindex")
        registry.start(job)
        result = registry.cancel(job.job_id)
        assert result.interrupted is True
        assert result.reason == "cancellation requested"
        assert job.stop_event.is_set()
        registry.finish(
            job,
            outcome="interrupted at progress callback",
            verified=False,
            state=JobState.CANCELLED,
        )

    def test_not_cancelable_job_refuses_with_a_stated_reason(self):
        registry = MaintenanceJobRegistry()
        job = _register(
            registry,
            operation="vacuum",
            cancelability=Cancelability.NOT_CANCELABLE,
        )
        registry.start(job)
        result = registry.cancel(job.job_id)
        assert result.interrupted is False
        assert result.reason == "operation cannot be interrupted"
        assert not job.stop_event.is_set()

    def test_cancelling_a_terminal_job_does_not_set_the_event(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        registry.start(job)
        registry.finish(job, outcome="completed", verified=True)
        result = registry.cancel(job.job_id)
        assert result.interrupted is False
        assert not job.stop_event.is_set()


class TestRunningSurface:
    def test_running_jobs_are_listed_for_the_status_command(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="vacuum")
        registry.start(job)
        assert [record.job_id for record in registry.running_jobs()] == [job.job_id]

    def test_completed_runs_are_not_listed_as_running(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry, operation="vacuum")
        registry.start(job)
        registry.finish(job, outcome="completed", verified=True)
        assert registry.running_jobs() == []

    def test_approval_decision_shape_is_frozen(self):
        registry = MaintenanceJobRegistry()
        job = _register(registry)
        decision = registry.authorize(job, confirmed=True)
        assert isinstance(decision, ApprovalDecision)
        with pytest.raises(AttributeError):
            setattr(decision, "approved", False)
