"""One-shot retarget of tests/agent/test_http_lifecycle_integration.py dict sites.

cliplc007 row 14: replace the removed _http_procs/_http_pgids/_failed_start_procs
fixtures and assertions with the ManagedProcessRecord registry. Mechanical
accessor substitutions only; semantic rewrites are done by hand afterwards.
"""

import pathlib
import re
import sys

PATH = pathlib.Path("tests/agent/test_http_lifecycle_integration.py")

# Longest patterns first so paired lines are consumed before their substrings.
REPLACEMENTS: list[tuple[str, str]] = [
    # imports
    (
        "from agent.http_lifecycle_errors import TerminationOutcome\n",
        "from agent.http_lifecycle_errors import TerminationOutcome\n"
        "from agent.http_lifecycle_process_record import ManagedProcessRecord\n"
        "from agent.lifecycle import LifecycleState\n",
    ),
    # fixture helper
    (
        '@pytest.fixture\ndef mgr() -> HttpServerLifecycleManager:\n    return HttpServerLifecycleManager()\n',
        '@pytest.fixture\ndef mgr() -> HttpServerLifecycleManager:\n'
        '    return HttpServerLifecycleManager()\n\n\n'
        'def _make_record(\n'
        '    proc: object,\n'
        '    pgid: int | None = None,\n'
        '    state: LifecycleState = LifecycleState.RUNNING,\n'
        '    failed_start: bool = False,\n'
        ') -> ManagedProcessRecord:\n'
        '    """Build a minimal ownership record for tests that seed the registry."""\n'
        '    return ManagedProcessRecord(  # type: ignore[arg-type] — test helper passes Mock process objects\n'
        '        process=proc,\n'
        '        pid=getattr(proc, "pid", 0),\n'
        '        pgid=pgid,\n'
        '        stderr_log=None,\n'
        '        state=state,\n'
        '        failed_start=failed_start,\n'
        '    )\n',
    ),
    # failed_start seeding (before generic proc fixtures)
    (
        'mgr._http_procs["test"] = stale_proc\n        mgr._http_pgids["test"] = 7777\n        mgr._failed_start_procs["test"] = stale_proc\n        mgr._stderr_files["test"] = fh',
        'mgr._records["test"] = _make_record(stale_proc, pgid=7777, failed_start=True)\n        mgr._stderr_files["test"] = fh',
    ),
    (
        'mgr._http_procs["test"] = stale_proc\n        mgr._http_pgids["test"] = 7777\n        mgr._failed_start_procs["test"] = stale_proc',
        'mgr._records["test"] = _make_record(stale_proc, pgid=7777, failed_start=True)',
    ),
    (
        'assert mgr._http_procs.get("test") is not stale_proc\n        assert mgr._http_pgids.get("test") is None\n        assert mgr._failed_start_procs.get("test") is None',
        'assert mgr._records.get("test") is None',
    ),
    (
        'assert mgr._http_procs.get("test") is stale_proc\n        assert mgr._http_pgids.get("test") == 7777\n        assert mgr._failed_start_procs.get("test") is stale_proc',
        'assert mgr._records["test"].process is stale_proc\n        assert mgr._records["test"].pgid == 7777\n        assert mgr._records["test"].failed_start is True',
    ),
    # paired proc+pgid fixtures
    (
        'manager._http_procs["test"] = proc_mock\n        manager._http_pgids["test"] = 1234',
        'manager._records["test"] = _make_record(proc_mock, pgid=1234)',
    ),
    (
        'mgr._http_procs["test"] = proc_mock\n        mgr._http_pgids["test"] = 9999',
        'mgr._records["test"] = _make_record(proc_mock, pgid=9999)',
    ),
    (
        'mgr._http_procs["test"] = proc_mock\n        mgr._http_pgids["test"] = 7777',
        'mgr._records["test"] = _make_record(proc_mock, pgid=7777)',
    ),
    (
        'mgr._http_procs["a"] = proc1\n        mgr._http_procs["b"] = proc2',
        'mgr._records["a"] = _make_record(proc1)\n        mgr._records["b"] = _make_record(proc2)',
    ),
    # paired release assertions
    (
        'assert mgr._http_procs.get("test") is None\n        assert mgr._http_pgids.get("test") is None',
        'assert mgr._records.get("test") is None',
    ),
    (
        'assert len(mgr._http_procs) == 0\n        assert len(mgr._http_pgids) == 0',
        'assert len(mgr._records) == 0',
    ),
    # generic fixtures
    (
        'manager._http_procs["test"] = Mock(poll=Mock(return_value=None))',
        'manager._records["test"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'mgr._http_procs["test"] = Mock(poll=Mock(return_value=None))',
        'mgr._records["test"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'mgr._http_procs["test2"] = Mock(poll=Mock(return_value=None))',
        'mgr._records["test2"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'mgr._http_procs["a"] = Mock(poll=Mock(return_value=None))',
        'mgr._records["a"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'mgr._http_procs["b"] = Mock(poll=Mock(return_value=None))',
        'mgr._records["b"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'mgr._http_procs["c"] = Mock(poll=Mock(return_value=None))',
        'mgr._records["c"] = _make_record(Mock(poll=Mock(return_value=None)))',
    ),
    (
        'manager._http_procs["test"] = Mock(poll=Mock(return_value=0))',
        'manager._records["test"] = _make_record(Mock(poll=Mock(return_value=0)))',
    ),
    (
        'mgr._http_procs["test"] = proc_mock',
        'mgr._records["test"] = _make_record(proc_mock)',
    ),
    (
        'mgr._http_procs["test"] = old_proc',
        'mgr._records["test"] = _make_record(old_proc)',
    ),
    # single-line assertions
    ('assert mgr._http_procs.get("test") is None', 'assert mgr._records.get("test") is None'),
    ('assert len(manager._http_procs) == 0', 'assert len(manager._records) == 0'),
    ('assert len(manager._http_pgids) == 0', 'assert len(manager._records) == 0'),
    ('assert mgr._http_procs.get("test") is proc_mock', 'assert mgr._records["test"].process is proc_mock'),
    ('assert mgr._http_pgids.get("test") == 7777', 'assert mgr._records["test"].pgid == 7777'),
    ('assert mgr._http_procs.get("test") is second_proc', 'assert mgr._records["test"].process is second_proc'),
    ('assert mgr._http_procs.get("test") is new_proc', 'assert mgr._records["test"].process is new_proc'),
    ('assert mgr._http_procs.get("test") is fresh_proc', 'assert mgr._records["test"].process is fresh_proc'),
    ('assert mgr._http_procs.get("test") is live_proc', 'assert mgr._records["test"].process is live_proc'),
]


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        n = text.count(old)
        text = text.replace(old, new)
        print(f"{n:3d}x {old.splitlines()[0][:60]!r}")
    leftover = re.findall(r"_http_procs|_http_pgids|_failed_start_procs", text)
    PATH.write_text(text, encoding="utf-8")
    print(f"leftover dict references: {len(leftover)}")
    return 0 if not leftover else 1


if __name__ == "__main__":
    sys.exit(main())
