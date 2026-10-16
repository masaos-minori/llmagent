## Goal

Remove the `security_audit` aggregation and its Readiness Summary line, so the summary stops reporting a
startup check that no longer runs (`REQ-017`, `AC-008`).

## Scope

- One modified module `scripts/agent/startup_reporter.py`: delete `_count_by_status(pipeline, "security_audit")`
  and the `Security audit:` line it feeds.
- No new summary line is added in this row.

## Assumptions

- Current module verified: `report_readiness()` builds the summary from four sources —
  `security_counts = _count_by_status(pipeline, "security_audit")`, `mcp_counts` (`"readiness"`),
  `tool_disc_counts` (`"mcp_tool_discovery"`), `rag_counts` (`"rag_consistency"`); the header
  `lines.append("Readiness Summary:")`; the `Security audit:` line is the first entry after the header
  and is the only consumer of `security_counts`.
- `_count_by_status()` returns `{"OK": n, "FATAL": n, "WARNING": n, "SKIPPED": n}` for a source name and
  returns all-zero counts for a source that never appears, so after row `22` the line would print
  `Security audit: FAIL (0 fatal, 0 warnings)` — a permanent false failure.
- `tests/agent/test_startup_reporter.py:52` asserts only `"Readiness Summary:" in message`; no test
  asserts the `Security audit:` line. The file's docstring at `:5` describes the summary behavior.
- Security visibility in the summary is preserved through the `Service readiness:` line, because row `18`
  routes posture failures through the `readiness` source.

## Design decisions

- Delete both the counter and the line. Keeping the counter would leave dead code; keeping the line with
  a different source name would silently relabel a check.
- Do not add a `Security posture:` line in this row. The Plan's frozen table assigns only removal to this
  row, and a posture line needs a pipeline source that row `18` deliberately does not create (it routes
  through `readiness`). **Needs confirmation** as a follow-up: whether the Readiness Summary should gain
  a dedicated posture line, which requires a new pipeline source in `startup_validation.py`.
- The remaining four summary entries keep their exact wording and order, because
  `tests/agent/test_startup.py` and operator expectations depend on the summary shape.
- `Unreachable servers:` and `Excluded tools (unavailable):` (`runtime_tools.unavailable_servers`) stay
  unchanged. Row `19` adds a separate `posture_excluded_servers` property; surfacing it here is a
  follow-up, not part of this row.

## Alternatives considered

- Replace the line with `Security posture: OK/FAIL` derived from `readiness` counts — rejected: it would
  duplicate the `Service readiness:` line and imply a separate check exists.
- Keep the line but print `n/a` — rejected: `REQ-017` removes the audit, and a permanent `n/a` line keeps
  a name that no longer describes anything.
- Suppress the line only when the source is absent — rejected: conditional rendering for a source that
  can never exist is dead logic.

## Implementation
### Target file

`scripts/agent/startup_reporter.py` (modify)

### Procedure

1. Delete the `security_counts = _count_by_status(pipeline, "security_audit")` assignment.
2. Delete the `Security audit: ...` entry from `lines`.
3. Keep the `Readiness Summary:` header, the `Service readiness:`, `Tool discovery:`, and
   `RAG consistency:` lines, the `unavailable_servers` block, the `degraded_keys` block, and the
   `Excluded tools (unavailable):` block unchanged.

### Method

- Land this row together with row `22`, which removes the source. Landing it earlier would remove a line
  that still reports a real check; landing it later produces the false `FAIL` described above.
- The final `logger.info("Readiness summary: %s", "; ".join(lines))` needs no change: it renders whatever
  lines exist.

### Details

- The summary drops from five entries to four.
- `McpServerHealthState` and the `health_registry` block are unrelated to the audit and stay.
- `tests/agent/test_startup_reporter.py` docstring at `:5` describes the summary; if it names the audit
  line, update the docstring text only (no assertion change).

## Compatibility considerations

- No test asserts the removed line, so `tests/agent/test_startup_reporter.py` keeps passing unchanged.
- `tests/agent/test_startup.py` startup-output assertions that scan the summary must be re-checked when
  row `30` lands; the summary header and the other three lines are unchanged.
- No `docs/*.md` change is in scope for this row; `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
  documents the Readiness Summary lines and is a follow-up.

## Security considerations

- Removing a false `FAIL` line matters: a summary that always reports failure trains operators to ignore
  it, which weakens the signal for real posture failures reported through `Service readiness:`.
- This row adds no security claim, so it cannot overstate the Agent's security state.

## Rollback considerations

- Revert this commit together with row `22`. Restoring the line without the audit step restores the
  permanent false `FAIL`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Summary header preserved | `uv run pytest tests/agent/test_startup_reporter.py` | passes, `"Readiness Summary:"` still present |
| Audit line absent | same existing test file (new case) | the rendered summary contains no `Security audit:` text |
| Other lines intact | same existing test file | `Service readiness:`, `Tool discovery:`, `RAG consistency:` still rendered |
| Startup integration | `uv run pytest tests/agent/test_startup.py` | passes after row `22` and row `30` |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/` | clean |

## Completion criteria

- Plan `AC-008` for the reporter: the Readiness Summary contains no `security_audit` aggregation and no
  `Security audit:` line.
- The header and the remaining three summary entries are unchanged.
- `tests/agent/test_startup_reporter.py` passes without assertion changes.

## Out of scope

- Removing the audit step (row `22`) or the audit modules (rows `20`-`21`).
- Adding a posture line to the summary (Needs-confirmation follow-up).
- Surfacing `posture_excluded_servers` (row `19`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the counter and the summary line | Pending | — | — | land with row `22` |
| 2 | Re-check the test file docstring | Pending | — | — | docstring-only change if needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-017` (remove Agent-side cross-config audit)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/startup_reporter.py`
