"""tools/_workitem_stage_parser.py

Command-line parser of tools/manage_workitem_stage.py: every subcommand and option.
Not a CLI; the entry module dispatches on `args.subcommand`.
"""

from __future__ import annotations

import argparse

from tools._workitem_status_table import _normalize_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive workflow-stage transitions via git mv",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    issue_parser = subparsers.add_parser(
        "close-issue", help="Move an issues/*.md file to issues/done/"
    )
    issue_parser.add_argument("issue_path", help="Path to the issue file")
    issue_parser.add_argument(
        "--force",
        action="store_true",
        help="Override a non-Frozen Plan block (requires --reason)",
    )
    issue_parser.add_argument(
        "--reason", help="Justification for --force (required alongside --force)"
    )
    issue_parser.add_argument(
        "--stage-only",
        action="store_true",
        help="Stage (not commit) an uncommitted source before the move",
    )

    plan_parser = subparsers.add_parser(
        "close-plan", help="Move a plans/*.md file to plans/done/"
    )
    plan_parser.add_argument("plan_path", help="Path to the plan file")
    plan_parser.add_argument(
        "--stage-only",
        action="store_true",
        help="Stage (not commit) an uncommitted source before the move",
    )

    impl_parser = subparsers.add_parser(
        "close-implementation",
        help="Move an implementations/*.md file to implementations/done/",
    )
    impl_parser.add_argument(
        "implementation_path", help="Path to the implementation procedure file"
    )
    impl_parser.add_argument(
        "--force",
        action="store_true",
        help="Override a Pending Execution Status block (requires --reason)",
    )
    impl_parser.add_argument(
        "--reason", help="Justification for --force (required alongside --force)"
    )
    impl_parser.add_argument(
        "--stage-only",
        action="store_true",
        help="Stage (not commit) an uncommitted source before the move",
    )

    close_batch_parser = subparsers.add_parser(
        "close-batch",
        help="Archive every procedure of a batch and mark its plan Completed",
    )
    close_batch_parser.add_argument(
        "batch_id",
        help="Batch id: a plan path or a bare YYYYMMDD-HHMMSS timestamp prefix",
    )
    close_batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned moves and edits without changing any file",
    )
    close_batch_parser.add_argument(
        "--stage-only",
        action="store_true",
        default=True,
        help="Stage (not commit) the archival moves; close-batch always stages so a "
        "batch's renames land in one real commit",
    )

    # set-status: update all rows' Status column
    set_status_parser = subparsers.add_parser(
        "set-status",
        help="Update the Execution Status table on an implementation-procedure or plan file",
    )
    set_status_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    set_status_parser.add_argument("path", help="Path to the file")
    set_status_parser.add_argument(
        "status",
        type=_valid_status_type,
        help="New status value for all rows (e.g. 'In Progress', 'InProgress', 'in_progress')",
    )
    set_status_parser.add_argument(
        "--notes",
        default=None,
        help="Optional notes text to append to each row's Notes column",
    )
    set_status_parser.add_argument(
        "--started",
        default=None,
        help="Optional Started timestamp to set on each row (overwrites, does not "
        "append) — pass the output of `date +%%Y%%m%%d-%%H%%M%%S`",
    )
    set_status_parser.add_argument(
        "--completed",
        default=None,
        help="Optional Completed timestamp to set on each row (overwrites, does not "
        "append) — pass the output of `date +%%Y%%m%%d-%%H%%M%%S`",
    )

    # set-step-status: update a single step's Status column
    set_step_parser = subparsers.add_parser(
        "set-step-status",
        help="Update the Status column of a specific step in the Execution Status table",
    )
    set_step_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    set_step_parser.add_argument("path", help="Path to the file")
    set_step_parser.add_argument(
        "--step",
        type=int,
        default=None,
        help="Step number to update (mutually exclusive with --description)",
    )
    set_step_parser.add_argument(
        "--description",
        default=None,
        help="Substring match against Description column (mutually exclusive with --step)",
    )
    set_step_parser.add_argument(
        "status",
        type=_valid_status_type,
        help="New status value for the matched row (e.g. 'In Progress', 'InProgress', 'in_progress')",
    )
    set_step_parser.add_argument(
        "--notes",
        default=None,
        help="Optional notes text to append to the matched row's Notes column",
    )
    set_step_parser.add_argument(
        "--started",
        default=None,
        help="Optional Started timestamp to set on the matched row (overwrites, "
        "does not append) — pass the output of `date +%%Y%%m%%d-%%H%%M%%S`",
    )
    set_step_parser.add_argument(
        "--completed",
        default=None,
        help="Optional Completed timestamp to set on the matched row (overwrites, "
        "does not append) — pass the output of `date +%%Y%%m%%d-%%H%%M%%S`",
    )

    # detect-stale: find stale workitems
    detect_parser = subparsers.add_parser(
        "detect-stale",
        help="Detect stale in-progress or pending workitems",
    )
    detect_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days since last modification to consider stale (default: 7)",
    )

    # detect-unexecuted-archive: report recently-archived procedures with open rows
    # (report-only; never moves or edits a work item).
    unexecuted_parser = subparsers.add_parser(
        "detect-unexecuted-archive",
        help="Report recently-archived procedures with open Execution Status rows "
        "(report-only; procedures with no archive-date commit are skipped)",
    )
    unexecuted_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days since archive to consider recent (default: 7)",
    )

    # list: list workitems by status/kind
    list_parser = subparsers.add_parser(
        "list",
        help="List workitems filtered by kind and/or status",
    )
    list_parser.add_argument(
        "--kind",
        choices=["implementation-procedure", "plan"],
        default=None,
        help="Filter by kind (omit to show both)",
    )
    list_parser.add_argument(
        "--status",
        type=_valid_status_type,
        default=None,
        help="Filter by status (omit to show all; e.g. 'In Progress', 'InProgress', 'in_progress')",
    )
    list_parser.add_argument(
        "--plan",
        default=None,
        help="With --order: the Plan whose procedures are listed (plans/ or plans/done/)",
    )
    list_parser.add_argument(
        "--order",
        action="store_true",
        help="With --plan: list that Plan's procedures grouped by Plan phase order",
    )

    # show: display Execution Status table
    show_parser = subparsers.add_parser(
        "show",
        help="Display the Execution Status table from a workitem file",
    )
    show_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    show_parser.add_argument("path", help="Path to the file")

    return parser


def _valid_status_type(value: str) -> str:
    """argparse ``type`` callback: validate + normalize a status argument."""
    try:
        return _normalize_status(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
