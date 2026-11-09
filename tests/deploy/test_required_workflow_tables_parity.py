"""Pin shell schema-gate table lists to the Python gate (wfaudit003).

The deploy scripts mirror REQUIRED_WORKFLOW_TABLES as a hardcoded space-separated
list. This test parses the shell constants textually (no script execution, no
deploy paths) and asserts set equality with the Python source of truth,
agent.services.workflow_schema.REQUIRED_WORKFLOW_TABLES keys.
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.services.workflow_schema import REQUIRED_WORKFLOW_TABLES

REPO_ROOT = Path(__file__).resolve().parents[2]

_SHELL_TARGETS = (
    REPO_ROOT / "deploy" / "init_db.sh",
    REPO_ROOT / "deploy" / "setup_services.sh",
)

_LIST_RE = re.compile(r'^REQUIRED_WORKFLOW_TABLES="([^"]+)"', re.MULTILINE)


def _parse_shell_list(script: Path) -> list[str]:
    match = _LIST_RE.search(script.read_text(encoding="utf-8"))
    assert match is not None, (
        f"REQUIRED_WORKFLOW_TABLES assignment not found in {script}"
    )
    return match.group(1).split()


class TestRequiredWorkflowTablesParity:
    def test_shell_lists_match_python_gate(self) -> None:
        python_tables = set(REQUIRED_WORKFLOW_TABLES)
        for script in _SHELL_TARGETS:
            shell_tables = set(_parse_shell_list(script))
            assert shell_tables == python_tables, (
                f"{script.relative_to(REPO_ROOT)} list {sorted(shell_tables)} "
                f"!= Python gate {sorted(python_tables)}"
            )

    def test_python_gate_has_five_tables(self) -> None:
        # Post-wfaudit010 five-table shape; execution_snapshots must not return.
        assert set(REQUIRED_WORKFLOW_TABLES) == {
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
            "tool_call_state",
        }
