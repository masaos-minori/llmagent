## Goal

Split `check_empty_result_repeat()` into a non-recording threshold scan and the
existing recording wrapper, so the round can observe a mid-round trip without
writing a second `guard_hint` (`REQ-007`, `REQ-006`). The scan returns the
tripping `(tool_name, count)` or `None`; the recording method keeps its log line,
its `_save_guard_hint` payload, and its returned text byte-for-byte.

## Scope

`scripts/agent/tool_loop_guard.py` only. One method is split into a new private
`_scan_empty_result_repeat()` plus a thin recording wrapper `check_empty_result_repeat()`.
Reference reads: `scripts/agent/tool_runner.py` (the round that consults the scan,
row 1), `tests/agent/test_tool_loop_guard.py` (the 34 existing tests that must
keep passing). Dependent test: `tests/agent/test_tool_loop_guard.py`.

## Assumptions

- The scan reads only `self._empty_result_counts` and
  `ctx.cfg.tool.tool_empty_result_max_repeats` (`tool_loop_guard.py:172-175`), and
  the recording half is three statements (`:176-188`); they are separable
  statements within one method (`ASSUM-01`), so the split preserves observable
  output.
- With the shipped default (`tool_empty_result_max_repeats <= 0`, absent from
  `config/`, `scripts/agent/config_dataclasses.py:178`) the scan returns "no trip"
  exactly as `check_empty_result_repeat` does today (`:172-173`).

## Design decisions

- **The scan is non-recording.** `_scan_empty_result_repeat()` performs only the
  threshold loop (`:172-175`) and returns the tripping `(tool_name, count)` or
  `None`. It calls no logger and no `_save_guard_hint`. This is what makes one
  hint per trip possible (`DR-002`, `REQ-007`).
- **The recording stays at the existing post-round site.** `check_empty_result_repeat()`
  becomes: early-return on `<= 0`, then call `_scan_empty_result_repeat()`, and on
  a trip write the same log line, the same `_save_guard_hint` payload, and return
  the same text as today. Observable behavior of the turn-level check
  (`llm_turn_runner.py:125`) is unchanged.

## Alternatives considered

- Calling `check_empty_result_repeat()` from the engines directly — it logs and
  writes `guard_hint` on every trip (`:176-188`), so the same trip would be
  recorded twice and `docs/…/agent_03_02…:80-86` would become inaccurate (`DR-002`).
- Suppressing the post-round check after a mid-round trip — moves the answer text
  (`llm_turn_runner.py:126-128`) and violates `REQ-008`.

## Implementation

### Target file

`scripts/agent/tool_loop_guard.py`

### Procedure

1. Add `_scan_empty_result_repeat(self)` as a new method next to
   `check_empty_result_repeat()`. Copy the threshold scan verbatim from
   `check_empty_result_repeat` (`:172-175`): early-return `None` when
   `ctx.cfg.tool.tool_empty_result_max_repeats <= 0`; otherwise iterate
   `self._empty_result_counts.items()` and return the first `(tool_name, count)`
   with `count >= threshold`. Do NOT add a logger call or `_save_guard_hint` call.
2. Rewrite `check_empty_result_repeat()` (`:169-189`) as a thin wrapper:
   early-return `None` on `<= 0` (same guard), call
   `_scan_empty_result_repeat()`, and on the returned `(tool_name, count)` write
   the identical log line (`:176-180`), call the identical `_save_guard_hint`
   payload (`:181-187`), and return the identical text (`:188`). On `None` return
   `None`.
3. Add `TestNonRecordingScanIsEquivalentToTheCheck` and
   `TestDisabledOptionIsInert` to `tests/agent/test_tool_loop_guard.py`.

### Method

- Edit-based. The scan body is moved, not rewritten; the wrapper reuses it. Keep
  the method grouping comment `# ── Empty result repeat guard helpers ──`
  (`:143`) intact.

### Details

- `record_tool_result` (`:156-167`), `_is_empty_result` (`:146-154`), `check_all`
  (`:356-377`), and all thresholds are unchanged.
- Exactly one `guard_hint` write and one log line per trip (`REQ-007`, AC-5): the
  mid-round scan writes nothing; the post-round `check_empty_result_repeat()`
  writes exactly one.

## Compatibility considerations

### Corrections found while implementing

- The scan is public, `scan_empty_result_repeat()`, not `_scan_empty_result_repeat()`: `tool_runner.py` consults it from another module. `check_empty_result_repeat()` keeps the log line, the `guard_hint` payload and the returned text. The scan is a single `next(...)` over the counts; module size 16104 B.


- `check_empty_result_repeat()` keeps its signature, return type, logging, and
  diagnostic write. The turn-level check at `llm_turn_runner.py:125` is unchanged.

## Security considerations

- N/A: behavior-preserving extraction, no auth/permission path.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/tool_loop_guard.py`
  restores HEAD. Reversible; no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_tool_loop_guard.py -q --timeout=120` — the 34
  existing tests pass unchanged; `TestNonRecordingScanIsEquivalentToTheCheck`
  asserts `_scan_empty_result_repeat()` returns the same tripping pair and `None`
  for the same boundary cases and writes nothing to `ctx.diagnostics`, while
  `check_empty_result_repeat()` still logs, still writes one `guard_hint` with the
  same fields, and still returns the same text; `TestDisabledOptionIsInert`
  asserts `None` when `tool_empty_result_max_repeats <= 0`.
- `uv run ruff check scripts/`, `uv run ruff format --check scripts/`,
  `uv run mypy scripts/ --config-file scripts/mypy.ini`.
- `uv run python tools/check_module_size.py --top 5` reports no new violation, no
  new baseline (UNK-05; file is 15827 B against the 16384 B gate).

## Completion criteria

`_scan_empty_result_repeat()` returns the tripping `(tool_name, count)` or `None`
and writes nothing; `check_empty_result_repeat()` delegates to it and reproduces
the original log line, `_save_guard_hint` payload, and returned text; all 34
existing guard tests pass; no lint/type/size finding.

## Out of Scope

- Consulting the scan inside the round — `tool_runner.py` (row 1).
- Defining `ToolCallStopReason` — row 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract `_scan_empty_result_repeat()` (non-recording) from `check_empty_result_repeat()` (REQ-007) | Completed | 20261023-170138 | 20261023-170138 | Phase 2 implemented; full suite passed |
| 2 | Make `check_empty_result_repeat()` the recording wrapper over the scan (REQ-007) | Completed | 20261023-170138 | 20261023-170138 | Phase 2 |
| 3 | Add extraction-equivalence + disabled-option tests (REQ-006, REQ-007) | Completed | 20261023-170138 | 20261023-170138 | Phase 2 |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-170138 | 20261023-170138 |  |

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
- **Requirement ID**: REQ-006, REQ-007, REQ-013
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `scripts/agent/tool_loop_guard.py`