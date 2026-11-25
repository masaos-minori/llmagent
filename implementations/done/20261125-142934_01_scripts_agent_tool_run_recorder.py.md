## Goal

Record the scheduling mode and write presence a round actually had in the `round_exec` audit event (REQ-001 mode from the plan, REQ-002 one shared derivation for `scheduling_mode`, REQ-003 side effect from `spec.is_write`), while keeping serialization events and counters as diagnostics (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- Changes only `_scheduling_mode` and `_record_round_exec` in `scripts/agent/tool_run_recorder.py`, plus one private helper (new), and its companion test file.
- `write_round_exec`, `_serialization_stats`, `get_serialization_stats`, `_record_serialization_stats`, and `_record_round_serialization_events` are not touched.

## Assumptions

- Mode vocabulary stays `parallel` / `serial` for `mode` and `dag_concurrent` / `dag_sequential` for `scheduling_mode` (Plan UNK-01, non-blocking; no repository consumer of the values was found).
- `approved_calls` holds `PreparedToolCall` objects, so `pc.spec.is_write` is the approved tool metadata (Plan Assumptions).
- The executor runs a batch's groups concurrently (`tool_runner.py::_run_plan_batches` gathers them) and a non-sequential group's calls concurrently (`_run_group_calls`), so a plan is concurrent when either holds with more than one participant. Checked against `scripts/agent/tool_runner.py` and `scripts/agent/tool_scheduler.py` for this procedure.
- No overlap with another Frozen Plan (`tools/check_plan_target_overlaps.py` reports none). The pending procedures of other Plans do not target this file (`rg -l tool_run_recorder implementations` lists only archived procedures and a mention in an unrelated tool_preparation procedure).

## Design decisions

- One private helper `_plan_runs_concurrently(batches)` (new) decides concurrency; both `mode` and `_scheduling_mode` read it, so the two cannot drift.
- `has_side_effect = any(pc.spec.is_write for pc in approved_calls)`; the serialization event contributes only `trigger_tool` and `serial_reason`.

## Alternatives considered

N/A: deriving `mode` from serialization events was rejected because it repeats the original inference; no other design was considered for this single-function change.

## Implementation
### Target file
`scripts/agent/tool_run_recorder.py`

### Procedure
Add the helper, rewrite `_scheduling_mode` to use it, and change `_record_round_exec` to derive `mode` and `has_side_effect` from the plan and the approved calls (REQ-001, REQ-002, REQ-003).

### Method
- Add `_plan_runs_concurrently(batches: tuple[ScheduledBatch, ...]) -> bool` (new) returning true when any batch has more than one group, or any group has `sequential` false and more than one call.
- `_scheduling_mode(batches)` returns `"dag_concurrent"` when the helper is true, else `"dag_sequential"`.
- In `_record_round_exec`, compute `concurrent = _plan_runs_concurrently(batches)` once, pass `mode="parallel" if concurrent else "serial"`, `scheduling_mode=_scheduling_mode(batches)`, and `has_side_effect=any(pc.spec.is_write for pc in approved_calls)`.

### Details
- Keep `first_event`, `trigger_tool`, `serial_reason`, `affected_tools`, `tool_count`, `round_id`, and `elapsed_ms` exactly as they are (REQ-004).
- Update the module docstring line for `_scheduling_mode` and `_record_round_exec` only if its wording becomes false; no other docstring or log change.
- An empty `batches` yields `serial` and `dag_sequential`; an empty `approved_calls` yields `has_side_effect` false.
- Line numbers cited by the Plan: `_scheduling_mode` at line 121 and `_record_round_exec` at line 128 (`mode="parallel"` at line 142, `has_side_effect` at line 143); re-read the file before editing.

### Companion test files
- `tests/agent/test_tool_run_recorder.py` (new)
  - Procedure: Write the four plan-shape tests first, against the real `build_execution_groups` and a mocked audit logger, reading the JSON that `_record_round_exec` logs: (1) several reads → `parallel`, `dag_concurrent`, `has_side_effect` false; (2) two conflicting writes in one sequential group → `serial`, `dag_sequential`, `has_side_effect` true; (3) one write with no conflict → `serial`, `has_side_effect` true, no serialization event; (4) forced-serial reads (`force_serial=True`) → `serial`, `has_side_effect` false. Add a mixed case (one write plus reads without scope conflict → `parallel`, `has_side_effect` true), an empty plan (`serial`, false), a consistency test over all shapes (`mode == "parallel"` exactly when `scheduling_mode == "dag_concurrent"`), and a counter test for `_record_serialization_stats` and `get_serialization_stats()` (REQ-001 to REQ-004).
  - Validation: `uv run pytest tests/agent/test_tool_run_recorder.py` fails on the old code for cases 1 to 3 and passes after the change.

## Compatibility considerations

N/A: payload keys of the `round_exec` event and the `write_round_exec` signature are unchanged; only the values become accurate. No repository consumer of `mode` or `has_side_effect` exists, and consumers outside the repository are unknown (Plan UNK-01).

## Security considerations

N/A: observability values only; no new data is logged and no input is parsed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Write the plan-shape tests first and confirm cases 1 to 3 fail on the current code (the expected failures prove the defect).
- `uv run pytest tests/agent/test_tool_run_recorder.py tests/agent/test_tool_runner.py tests/agent/test_tool_audit.py tests/agent/commands/test_cmd_mcp.py`.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`; then `uv run python tools/run_validation_gates.py --full` (diff-cover at least 90% on changed lines).

## Completion criteria

- A concurrent read-only plan is recorded `parallel` / `dag_concurrent` (AC-1); a sequential write plan is `serial` / `dag_sequential` (AC-2).
- A single unconflicted write is `has_side_effect` true (AC-3); a forced-serial read-only plan is `serial` and false (AC-4).
- `mode` is `parallel` exactly when `scheduling_mode` is `dag_concurrent`, and the counters and serialization events are unchanged (AC-5).
- Format, lint, type, architecture, and security gates pass; `tool_run_recorder.py` stays under the module size gate.

## Out of Scope

- `scripts/agent/tool_scheduler.py` behavior and resource scopes, and the debug label in `tool_runner.py::_run_plan_batches` (Plan UNK-02).
- `write_round_exec` in `scripts/agent/tool_audit.py` and any `docs/` page.
- Deploying: a hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the plan-shape tests first and confirm cases 1 to 3 fail on the current code | Completed | 20261125-150740 | 20261125-152409 | Added tests/agent/test_tool_run_recorder.py (new, 21 tests; companion). Written first: 20 failed on the old code (the constant mode made every plan shape fail, a wider failure set than cases 1 to 3), the counter test passed; all pass after the change. Targeted run: 217 passed. |
| 2 | Implement the helper, `_scheduling_mode`, and `_record_round_exec` changes | Completed | 20261125-150740 | 20261125-152409 | Changed: scripts/agent/tool_run_recorder.py (helper `_plan_runs_concurrently`, `_scheduling_mode`, `_record_round_exec`). Stale check clean at Step 2; claims re-verified, no correction. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-152409 | 20261125-152409 | ruff format/check, mypy, lint-imports, bandit, module size, fast gates Pass. Full suite: 14289 passed, 1 failed (tests/mcp_servers/git/test_mcp_git.py::test_check_repo_path_equivalence, hypothesis property test on PurePosixPath, unrelated to changed files; passes alone). diff-cover 100% (3 lines). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (mode from the plan), `REQ-002` (shared derivation), `REQ-003` (side effect from metadata), `REQ-004` (diagnostics and counters kept)
- **Source issue**: issues/20261119-140518_mcpai011_round-recording-accuracy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142517_mcpai011_round-recording-accuracy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-142934
- **Related target files**: `scripts/agent/tool_run_recorder.py`, `tests/agent/test_tool_run_recorder.py`