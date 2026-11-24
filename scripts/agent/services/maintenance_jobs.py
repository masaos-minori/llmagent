"""scripts/agent/services/maintenance_jobs.py

MaintenanceJobRegistry — the in-process record of every Session, RAG, and Memory
maintenance run: job id, operation, target store, approval level, cancelability,
state, progress, recorded grants, and terminal outcome (REQ-001).

Data and transitions only. The module holds no database connection, runs no SQL,
formats no command output, and does not import `agent.commands`; the command layer
and the store accessors are its callers. Approval is enforced here, and the
one-writer-per-store guard is process-global because the registry has one owner
built in `scripts/agent/factory.py` and carried on `AppServices`.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum


class JobState(StrEnum):
    """Lifecycle states of a maintenance run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OUTCOME_UNKNOWN = "outcome_unknown"

    @property
    def is_terminal(self) -> bool:
        """Return whether no further transition is possible from this state."""
        return self in {
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELLED,
            JobState.OUTCOME_UNKNOWN,
        }


class ApprovalLevel(StrEnum):
    """Approval a run needs, declared with the operation rather than the command line."""

    NONE = "none"
    CONFIRM = "confirm"
    GUARD = "guard"


class Cancelability(StrEnum):
    """Whether SQLite can still interrupt the operation at its next progress callback."""

    COOPERATIVE = "cooperative"
    NOT_CANCELABLE = "not_cancelable"


class StoreTarget(StrEnum):
    """Target store a write job runs against; one running writer per store."""

    SESSION = "session"
    RAG = "rag"


class JobConflictError(RuntimeError):
    """Raised when a write job is registered against a store that has one running."""

    def __init__(self, running_job_id: str, store: StoreTarget) -> None:
        """Record the running job id so the caller can name it in its message."""
        self.running_job_id = running_job_id
        self.store = store
        super().__init__(
            f"store '{store}' already has a running job ({running_job_id})"
        )


@dataclass
class MaintenanceJob:
    """One maintenance run as the registry records it."""

    job_id: str
    operation: str
    store: StoreTarget
    approval_level: ApprovalLevel
    cancelability: Cancelability
    is_write: bool
    state: JobState = JobState.PENDING
    started_at: float | None = None
    progress: int = 0
    outcome: str = ""
    verified: bool = False
    # Grants the caller observed for this run, recorded as provenance. They are not the
    # authority that permits the run; `approval_level` is (REQ-003).
    grants: list[str] = field(default_factory=list)
    session_target: str = ""
    stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    precondition: Callable[[], bool] | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ApprovalDecision:
    """Result of the approval step for one run, recorded on the job."""

    job_id: str
    level: ApprovalLevel
    approved: bool
    precondition_ok: bool | None = None
    detail: str = ""


@dataclass(frozen=True)
class CancelResult:
    """Result of a cancellation request, so the caller can state it instead of guessing."""

    job_id: str
    interrupted: bool
    reason: str


REFUSED_NOT_CANCELABLE = "operation cannot be interrupted"
REFUSED_TERMINAL = "job already finished"
CANCELLATION_REQUESTED = "cancellation requested"


@dataclass(frozen=True)
class OperationProfile:
    """What the registry declares about one operation: level, cancelability, writer slot."""

    operation: str
    approval_level: ApprovalLevel
    cancelability: Cancelability
    is_write: bool


# The level and cancelability are properties of the operation, not of the command
# line (REQ-003). A single long statement — VACUUM, a WAL checkpoint — has no
# progress callback left to interrupt at, so it is declared `not_cancelable`.
OPERATION_PROFILES: dict[str, OperationProfile] = {
    "stats": OperationProfile(
        "stats", ApprovalLevel.NONE, Cancelability.NOT_CANCELABLE, False
    ),
    "health": OperationProfile(
        "health", ApprovalLevel.NONE, Cancelability.NOT_CANCELABLE, False
    ),
    "consistency": OperationProfile(
        "consistency", ApprovalLevel.NONE, Cancelability.NOT_CANCELABLE, False
    ),
    "checkpoint": OperationProfile(
        "checkpoint", ApprovalLevel.NONE, Cancelability.NOT_CANCELABLE, True
    ),
    "vacuum": OperationProfile(
        "vacuum", ApprovalLevel.GUARD, Cancelability.NOT_CANCELABLE, True
    ),
    "purge": OperationProfile(
        "purge", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "recover": OperationProfile(
        "recover", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "reindex": OperationProfile(
        "reindex", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "rebuild": OperationProfile(
        "rebuild", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "prune": OperationProfile(
        "prune", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "delete": OperationProfile(
        "delete", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
    "import": OperationProfile(
        "import", ApprovalLevel.CONFIRM, Cancelability.COOPERATIVE, True
    ),
}


def profile_for(operation: str) -> OperationProfile:
    """Return the declared profile for one operation."""
    try:
        return OPERATION_PROFILES[operation]
    except KeyError:
        raise KeyError(f"no operation profile for '{operation}'") from None


class MaintenanceJobRegistry:
    """Owner of the maintenance job records for one process."""

    def __init__(self) -> None:
        """Start with no jobs and no running writer on any store."""
        self._jobs: dict[str, MaintenanceJob] = {}
        self._running_writer: dict[StoreTarget, str] = {}
        self._grants: dict[str, ApprovalDecision] = {}

    def register(
        self,
        *,
        operation: str,
        store: StoreTarget,
        approval_level: ApprovalLevel | None = None,
        cancelability: Cancelability | None = None,
        is_write: bool | None = None,
        session_target: str = "",
        precondition: Callable[[], bool] | None = None,
    ) -> MaintenanceJob:
        """Create the job record for one run, using the operation's declared profile.

        A second write job against a store that already has a running writer is
        refused with `JobConflictError` naming the running job id, not queued.
        Read-only runs do not take the writer slot.
        """
        profile = profile_for(operation)
        level = approval_level or profile.approval_level
        cancelability_value = cancelability or profile.cancelability
        write = profile.is_write if is_write is None else is_write
        running = self._running_writer.get(store)
        if write and running is not None:
            raise JobConflictError(running, store)
        job = MaintenanceJob(
            job_id=uuid.uuid4().hex[:8],
            operation=operation,
            store=store,
            approval_level=level,
            cancelability=cancelability_value,
            is_write=write,
            session_target=session_target,
            precondition=precondition,
        )
        self._jobs[job.job_id] = job
        return job

    def lookup(self, job_id: str) -> MaintenanceJob | None:
        """Return the job record for one id, or None when the id is unknown."""
        return self._jobs.get(job_id)

    def running_writer(self, store: StoreTarget) -> str | None:
        """Return the job id of the running write job on a store, if any."""
        return self._running_writer.get(store)

    def running_jobs(self) -> list[MaintenanceJob]:
        """Return the job records that are currently running, in registration order."""
        return [job for job in self._jobs.values() if job.state is JobState.RUNNING]

    def authorize(
        self,
        job: MaintenanceJob,
        *,
        confirmed: bool,
    ) -> ApprovalDecision:
        """Enforce the approval level declared for the run.

        `none` needs no grant; `confirm` needs a request-bound confirmation bound to
        this run; `guard` needs the confirmation plus the stored precondition, whose
        result is recorded on the decision. `confirmed` is the caller's statement that a
        grant was obtained for this run, through the input controller or through a grant
        recorded on the job with `record_grant`. A flag the caller read without recording
        it grants nothing here.
        """
        if job.approval_level is ApprovalLevel.NONE:
            decision = ApprovalDecision(job.job_id, job.approval_level, True)
        elif not confirmed:
            decision = ApprovalDecision(
                job.job_id,
                job.approval_level,
                False,
                detail=f"{job.approval_level} approval requires a confirmation",
            )
        elif job.approval_level is ApprovalLevel.GUARD:
            if job.precondition is None or not job.precondition():
                decision = ApprovalDecision(
                    job.job_id,
                    job.approval_level,
                    False,
                    precondition_ok=False,
                    detail="guard precondition does not hold",
                )
            else:
                decision = ApprovalDecision(
                    job.job_id,
                    job.approval_level,
                    True,
                    precondition_ok=True,
                )
        else:
            decision = ApprovalDecision(job.job_id, job.approval_level, True)
        self._grants[job.job_id] = decision
        return decision

    def grant(self, job_id: str) -> ApprovalDecision | None:
        """Return the approval decision recorded for one run, if any."""
        return self._grants.get(job_id)

    def record_grant(self, job: MaintenanceJob, grant: str) -> MaintenanceJob:
        """Record one grant the caller observed for a run on the job record.

        The grant is provenance: it says how the run was approved, so a later read of the
        record can distinguish a granted run from one that decided itself (REQ-003).
        Recording it does not approve the run; `authorize` does.
        """
        job.grants.append(grant)
        return job

    def start(self, job: MaintenanceJob) -> MaintenanceJob:
        """Move a pending job to running once its approval level is satisfied.

        A write job takes the store's writer slot here, so the guard sees the run
        that is actually writing, not a run that was only registered.
        """
        if job.state is not JobState.PENDING:
            raise RuntimeError(
                f"job {job.job_id} cannot start from state '{job.state}'"
            )
        decision = self._grants.get(job.job_id)
        if job.approval_level is ApprovalLevel.NONE:
            if decision is not None and not decision.approved:
                raise RuntimeError(
                    f"job {job.job_id} is not approved: {decision.detail}"
                )
        elif decision is None or not decision.approved:
            raise RuntimeError(f"job {job.job_id} is not approved: no grant recorded")
        if job.is_write:
            running = self._running_writer.get(job.store)
            if running is not None and running != job.job_id:
                raise JobConflictError(running, job.store)
            self._running_writer[job.store] = job.job_id
        job.state = JobState.RUNNING
        job.started_at = time.time()
        return job

    def record_progress(self, job: MaintenanceJob, progress: int) -> None:
        """Record the worker's progress count for a running job."""
        job.progress = progress

    def finish(
        self,
        job: MaintenanceJob,
        *,
        outcome: str,
        verified: bool,
        state: JobState = JobState.COMPLETED,
    ) -> MaintenanceJob:
        """Record the terminal outcome; a run is verified only when its postcondition ran.

        `verified` is the postcondition result, so a caller cannot report success
        without having measured it (REQ-004).
        """
        if state not in {
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELLED,
            JobState.OUTCOME_UNKNOWN,
        }:
            raise RuntimeError(f"job {job.job_id} cannot finish in state '{state}'")
        if job.state is JobState.OUTCOME_UNKNOWN:
            raise RuntimeError(f"job {job.job_id} already ended in 'outcome_unknown'")
        if verified and state is not JobState.COMPLETED:
            raise RuntimeError(
                f"job {job.job_id} cannot report success from state '{state}'"
            )
        job.state = state
        job.outcome = outcome
        job.verified = verified
        if job.is_write:
            self._running_writer.pop(job.store, None)
        return job

    def mark_outcome_unknown(self, job: MaintenanceJob) -> MaintenanceJob:
        """End a running job as unknown because its awaiter was cancelled.

        Such a run is never reported as success and is never re-run automatically.
        """
        return self.finish(
            job,
            outcome="awaiter cancelled",
            verified=False,
            state=JobState.OUTCOME_UNKNOWN,
        )

    def cancel(self, job_id: str) -> CancelResult:
        """Set the stop event for a cooperative job, or refuse with the stated reason.

        The worker converts the interrupt into the `cancelled` outcome when the
        statement reaches its next progress callback; this method only requests it.
        """
        job = self._jobs.get(job_id)
        if job is None:
            return CancelResult(job_id, False, "unknown job id")
        if job.state.is_terminal:
            return CancelResult(job_id, False, REFUSED_TERMINAL)
        if job.cancelability is Cancelability.NOT_CANCELABLE:
            return CancelResult(job_id, False, REFUSED_NOT_CANCELABLE)
        job.stop_event.set()
        return CancelResult(job_id, True, CANCELLATION_REQUESTED)
