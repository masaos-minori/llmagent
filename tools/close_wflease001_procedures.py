#!/usr/bin/env python3
"""tools/close_wflease001_procedures.py

Close a list of wflease001 implementation procedures: set every Execution
Status step to Completed with per-step notes, then run close-implementation
--stage-only. One invocation per procedure list; reusable across groups.
"""

from __future__ import annotations

import subprocess
import sys

NOTES: dict[int, list[str]] = {
    3: [
        "Implemented per procedure (owner_id/lease_expires_at stamping).",
        "Covered by tests/agent/workflow/test_workflow_engine.py lease tests and test_stale_recovery_lease.py.",
        "ruff + mypy (changed files) + lint-imports 6 kept + bandit 0 + check_module_size OK + full suite 10908 passed, diff-cover exit 0.",
        "N/A: documentation updates owned by procedures 15 and 16.",
    ],
    4: [
        "Implemented per procedure (lease_duration_sec threaded through begin_stage_if_new).",
        "Covered by tests/agent/workflow/test_workflow_engine.py lease tests and test_stale_recovery_lease.py.",
        "ruff + mypy (changed files) + lint-imports 6 kept + bandit 0 + check_module_size OK + full suite 10908 passed, diff-cover exit 0.",
        "N/A: documentation updates owned by procedures 15 and 16.",
    ],
    5: [
        "Implemented: _LEASE_MARGIN_SEC=30 and lease_duration_sec=timeout+margin at the engine attempt-start site.",
        "Covered by tests/agent/workflow/test_workflow_engine.py lease tests (delta 35/31) and stamping test.",
        "ruff + mypy (changed files) + lint-imports 6 kept + bandit 0 + check_module_size OK + full suite 10908 passed, diff-cover exit 0.",
        "N/A: documentation updates owned by procedures 15 and 16.",
    ],
    11: [
        "Implemented: lease assertions in retry/timeout tests and TestWorkflowEngineLeaseStamping.",
        "N/A: this procedure is the test update itself.",
        "ruff + full suite 10908 passed, diff-cover exit 0.",
        "N/A: documentation updates owned by procedures 15 and 16.",
    ],
    12: [
        "Implemented: tests/agent/workflow/test_stale_recovery_lease.py (9 scenario tests, AC-2/3/4/5/7).",
        "N/A: this procedure is the test file itself.",
        "ruff + full suite 10908 passed, diff-cover exit 0. AC-7 fence is an absence-gate test pending wfrecovery001.",
        "N/A: documentation updates owned by procedures 15 and 16.",
    ],
    15: [
        "Startup Recovery section rewritten with lease semantics, timestamp contract, and manual recovery path; Known Limitations bullet updated (stale grace period -> lease expiry).",
        "N/A: documentation-only procedure.",
        "check_docs_quality/structure/content_policy --strict/consistency --domain agent/japanese all exit 0.",
        "N/A: this procedure is the documentation update.",
    ],
    16: [
        "Amendment (wflease001, 2026-11-01) subsection added under Decision; INV-07 bullet text preserved (checker forbids rewording) with the refined 'interrupted' definition carried by the Amendment; test-evidence row gains test_stale_recovery_lease.py.",
        "N/A: documentation-only procedure.",
        "check_adr_preservation exit 0 (1 warning: Decision section text changed; sentence-level mapping = the Amendment paragraph).",
        "N/A: this procedure is the documentation update.",
    ],
}


def main(paths: list[str]) -> int:
    for path in paths:
        num = int(path.split("_")[1])
        notes = NOTES[num]
        for step, note in enumerate(notes, start=1):
            subprocess.run(
                [
                    "uv", "run", "tools/manage_workitem_stage.py",
                    "set-step-status", "implementation-procedure", path,
                    "Completed", "--step", str(step), "--notes", note,
                ],
                check=True,
            )
        subprocess.run(
            ["uv", "run", "tools/manage_workitem_stage.py", "close-implementation", path, "--stage-only"],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
