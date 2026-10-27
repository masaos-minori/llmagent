## Goal

Delete the never-called `ToolExecutor._check_startup_mode` method and the two leftover
references it alone justified (the `StartupMode` import and the redundant
`self._server_configs = server_configs` assignment) from `scripts/shared/tool_executor.py`,
leaving the inherited `ToolTransportInvoker` guards as the single enforcement point (REQ-001,
REQ-002, REQ-003, REQ-005).

## Scope

- Delete the `_check_startup_mode` method definition (current file L68-78).
- Remove `StartupMode` from the `from shared.mcp_config import (...)` block (current L23-26);
  `McpServerConfig` stays (used by other signatures).
- Remove `self._server_configs = server_configs` from `ToolExecutor.__init__` (current L60);
  the parent `ToolTransportInvoker.__init__` (scripts/shared/tool_transport_invoker.py L55)
  assigns the identical attribute from the identical argument.
- No test edits: no test references `_check_startup_mode` (verified repo-wide in this pass).

## Assumptions

- Fresh `rg -n _check_startup_mode scripts/ tests/ docs/` at implementation time still shows
  only the definition (re-verified at procedure-generation time: single hit, the definition at
  `scripts/shared/tool_executor.py:68`); the Phase-1 gate is re-run before the deletion.
- Private underscore method: not part of any documented public API, so no external caller is
  expected (plan UNK-01, non-blocking).
- `_error_result` and `ToolCallResult` remain used by the rest of the file after deletion, so
  their imports/members are untouched.

## Design decisions

- Pure deletion, no replacement guard: `ToolExecutor.execute()` already delegates to the
  inherited `_run_precall_gates()`, which rejects `startup_mode == StartupMode.NONE` servers at
  the shared boundary (verified: scripts/shared/tool_transport_invoker.py REQ-004 block);
  removing the shadow guard cannot weaken enforcement.
- The `_server_configs` assignment is in-scope as a leftover reference, not as cleanup: it
  existed to feed the dead method (`self._server_configs.get(server_key)` occurs in this file
  only inside `_check_startup_mode`).

## Alternatives considered

- Keeping the assignment as defensive redundancy: rejected — the parent assigns the same
  attribute from the same argument before `ToolExecutor.__init__` body runs; the duplicate is a
  reader trap (plan REQ-003 evidence).
- Keeping the method but adding a call site: rejected — the live boundary guard already covers
  the behavior; a second guard is the misleading pattern the issue flags.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Run the gate: `rg -n _check_startup_mode scripts/ tests/ docs/` — abort and report if any
   hit other than the definition appears.
2. Delete the whole `_check_startup_mode` method (definition line through the final
   `return None`, current L68-78), including its docstring.
3. Delete the `StartupMode,` line from the `from shared.mcp_config import (...)` block (current
   L23-26), leaving `McpServerConfig` imported.
4. Delete the `self._server_configs = server_configs` line in `__init__` (current L60); keep
   the `super().__init__(...)` call and `self._resolver = ToolRouteResolver()`.

### Method

Three deletions in one file; no signature, docstring (other than the deleted method's), or
region changes. The `concurrency_limits` docstring in `__init__` is owned by the mcpinv004 plan
and must not be touched here.

### Details

- After deletion the file must contain no `StartupMode` token at all (ruff F401 gate).
- Line numbers cited are pre-change; locate by structure.
- `httpx`, `ToolCallResult`, `ToolRouteResolver`, `LifecycleProtocol` imports are all still used
  elsewhere in the file; only the mcp_config block changes.

## Compatibility considerations

- Overlap with mcpinv004 plan (`plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md`)
  on the same file: recorded Compatible in both plans — mcpinv004 edits only the
  `concurrency_limits` docstring in `__init__`; this document's deletion region is disjoint;
  whichever implements second rebases on the first.
- Overlap on docs with mcpinv001 (`mcp_03_01`): disjoint sections; see
  `20261028-005859_03`.
- Tests `test_invoke_rejects_disabled_server` (tests/shared/test_tool_executor.py L586) and the
  order test that assigns `executor._server_configs = {}` directly
  (tests/shared/test_tool_executor_order.py L37) must pass unmodified — the inherited attribute
  and boundary guard keep them green (AC-2, AC-3).

## Security considerations

- None: deletion of an unreachable guard whose intended protection is already enforced at the
  live boundary; disabled-server rejection behavior is unchanged (REQ-005).

## Rollback considerations

- `git checkout -- scripts/shared/tool_executor.py` restores the method and leftovers; docs
  documents `20261028-005859_02`/`20261028-005859_03` revert in the same unit if rolled back
  together (their corrected text remains true of the live guard either way, so a docs-only
  retention is also safe).

## Validation plan

- `uv run pytest tests/shared/` then `uv run pytest tests/` — green, no test edits (AC-2/AC-3).
- `uv run ruff check scripts/` — no F401 (REQ-002).
- `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`,
  `PYTHONPATH=scripts uv run lint-imports` — clean.
- `rg -n _check_startup_mode scripts/ tests/ docs/` — zero hits after the change (AC-1).

## Completion criteria

- Method, import entry, and assignment all absent; `rg` gate zero hits.
- Full validation sequence passes with zero test-file diffs.
- `git diff --stat` for this document shows exactly one changed file.

## Out of Scope

- `scripts/shared/tool_transport_invoker.py` and `scripts/shared/mcp_config.py` (untouched per
  issue constraint).
- The `concurrency_limits` docstring (mcpinv004's region).
- Documentation corrections — covered by `20261028-005859_02` and `20261028-005859_03`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase-1 rg gate is step 1 of Procedure |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | See 20261028-005859_02/_03 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20261027-001347_mcpinv002_remove-dead-check-startup-mode-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103047_mcpinv002_remove-dead-check-startup-mode-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-005859
- **Related target files**: scripts/shared/tool_executor.py
