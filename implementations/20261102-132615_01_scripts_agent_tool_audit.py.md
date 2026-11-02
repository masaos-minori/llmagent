# Replace the workflow-id asserts with skip-and-warn

## Goal

Remove all three `assert ctx.workflow.workflow_id` preconditions from
`scripts/agent/tool_audit.py` and replace them with a private helper that logs one warning and
signals skip, so a missing `workflow_id` after tool side effects never crashes the writer (Plan
REQ-001 skip-and-warn, REQ-002 existing guard order, REQ-005 `log_approval_decision` kept and fixed).

## Scope

- Add `import logging` and `logger = logging.getLogger(__name__)` (new module logger).
- Add `_workflow_id_or_skip(ctx, writer: str, tool: str) -> str | None` (new) private helper.
- Replace the asserts at `tool_audit.py:57` (`audit_approval`), `:84` (`log_approval_decision`),
  `:175` (`audit_tool_exec`) with helper calls in the same positions; use the returned id in the
  events instead of `ctx.workflow.workflow_id`.
- Signatures, docstring first lines, the no-`audit_logger` early returns, and `audit_tool_exec`'s
  `not mcp_request_id and not source` early return (before the workflow check) unchanged.

## Assumptions

- Verified 20261102: the three asserts are the only `assert` statements in the module (lines 57,
  84, 175); each is already preceded by a silent `audit_logger is None` return; `audit_tool_exec`
  also early-returns on empty `mcp_request_id`/`source` before its assert.
- Plan Decision 1 (skip, not raise): the chosen option of UNK-01 (skip-and-warn default) —
  `audit_tool_exec` runs after tool execution, so raising would abort post-side-effect.
- Plan Decision 2: helper returns `str | None` to remove the third copy of the guard text and keep
  `audit_tool_exec` complexity unchanged.
- Batch note: toolaudit001 (later in the batch) also edits this file; it targets the denial-path
  call wiring, not these lines (recorded adjudication D3: assertaudit lands first).

## Design decisions

- Warning text names the writer and the tool only — no argument values (REQ-001: warnings could
  otherwise carry unmasked secrets; the Plan explicitly says "without arguments").
- Module logger `agent.tool_audit` via `logging.getLogger(__name__)`, matching `tool_runner`
  (Plan Design, failure path).
- Helper cannot raise: plain attribute reads plus one `logger.warning` (Plan Design).

## Alternatives considered

- Raise an explicit exception (Plan Decision 1a) — rejected: reproduces the abort-after-side-effects
  bug in `audit_tool_exec`.
- Write the event with an empty `workflow_id` (1c) — rejected: persists the invalid record.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
Three edits plus the import/logger block.

### Method
```python
import logging
...
logger = logging.getLogger(__name__)


def _workflow_id_or_skip(ctx: AgentContext, writer: str, tool: str) -> str | None:
    """Return the workflow id, or None after logging a skip warning."""
    workflow_id = ctx.workflow.workflow_id
    if not workflow_id:
        logger.warning(
            "%s skipped: called outside workflow context (tool=%s)",
            writer,
            tool,
        )
        return None
    return workflow_id
```
At each former assert site (tool argument = `tool_name` in `audit_approval`, `outcome.tool_name`
in `log_approval_decision` — `ApprovalOutcome.tool_name` exists, `tool_models.py:48` — and the tool
name parameter in `audit_tool_exec`):
```python
    workflow_id = _workflow_id_or_skip(ctx, "audit_tool_exec", name)
    if workflow_id is None:
        return
```
and pass `workflow_id=workflow_id` to the event constructor (replacing
`ctx.workflow.workflow_id` at :74, :95, :194).

### Details
- Helper placement: module-private, after `_bounded_preview`/`_extract_resource_scope` helpers.
- Identical behavior under `python -O` follows automatically: no `assert` remains (AC-1, bandit
  B101 findings on this file drop 3 → 0).
- No change to `audit_workflow_start`, `audit_stage_completed`, `write_round_exec`.

## Compatibility considerations

- With a non-empty `workflow_id`, every path is value-identical; AC-2 regression modules
  (`test_tool_audit.py`, `test_audit_log_format.py`, `test_tool_approval_preflight.py`,
  `test_tool_runner.py`) must pass unchanged.
- Callers see no new exception type — the previously-crashing case now returns (REQ-002).

## Security considerations

- The warning carries no argument values, so it cannot leak unmasked secrets (REQ-001).

## Rollback considerations

- N/A: revert the commit; the asserts return with it.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py` — new tests (row 02) are red before this row.
- `uv run pytest tests/agent/test_audit_log_format.py tests/agent/test_tool_approval_preflight.py
  tests/agent/test_tool_runner.py` — unchanged (AC-2).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`
  (B101 on this file: 0), `uv run python tools/check_module_size.py`,
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`, `uv run lint-imports`.

## Completion criteria

- `rg "^\\s*assert" scripts/agent/tool_audit.py` returns nothing; each writer with `workflow_id`
  `None` or `""` logs exactly one warning naming writer and tool, writes nothing, raises nothing;
  all pre-existing tests pass unchanged.

## Out of Scope

- Tests (row 02); docs (rows 03-04); removing `log_approval_decision` (owner follow-up, UNK-02);
  toolaudit001's denial-path changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add logger + `_workflow_id_or_skip` (new); replace the three asserts | Pending | — | — | After row 02's red tests land (Plan Phase 1) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Deploy handoff is the Plan's Phase 4, user decision |

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
- **Requirement ID**: REQ-001 (no asserts, skip-and-warn), REQ-002 (guard order preserved), REQ-005 (log_approval_decision kept and fixed)
- **Source issue**: issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: scripts/agent/tool_audit.py
