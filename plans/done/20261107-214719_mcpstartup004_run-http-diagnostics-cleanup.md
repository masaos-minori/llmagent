## Goal
Make the startup diagnostics in `MCPServer.run_http()` describe what the code actually does, without changing startup behavior. Correct three inaccuracies: the `except SystemExit` handler labels any exit from `server.run()` as a posture-gate failure, the loopback post-start check runs after the socket is already listening and silently skips when no server object exists, and a local `import logging` shadows the module-level import.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/mcp_servers/server.py` — `MCPServer.run_http` (the `except SystemExit` log message and the redundant function-local `import logging`) and `_LoopbackVerifyingServer.startup` (its docstring).
  - `tests/mcp_servers/test_mcp_server_base.py` — add or adjust one unit test asserting the corrected log message and re-raise for a `SystemExit` originating in `server.run()`.
- **Out-of-Scope**:
  - Changing the order of the loopback allow-list check, config-isolation check, posture gate, and socket creation.
  - Any change to `_enforce_startup_posture_gate` behavior or to the double-execution problem tracked in `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`.
  - Changing the loopback allow-list values (`127.0.0.1`, `::1`).
  - Changing uvicorn configuration or log levels.
  - Changing exit codes or the `sys.exit(1)` follow-up.
- **Dependencies**: Same file as `issues/20261107-132004_mcpstartup001_python-m-double-execution.md` and `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`; no required order, but sequence the edits to avoid conflicts in `scripts/mcp_servers/server.py`. Related archived: `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md`. No `Depends on` entries.

## Background
Evidence from `scripts/mcp_servers/server.py` at reviewed head `59dbae624`, still current (label: `Explicit in code`); file unchanged since that head. The posture gate runs before the `try`, and the `run_http` docstring says a gate `SystemExit` intentionally propagates uncaught. The remaining `except SystemExit` clause wraps only `server.run()` and logs "Posture-gate failure during startup" before re-raising. `_LoopbackVerifyingServer.startup()` calls `super().startup()` first and then inspects `srv.sockets`, so by then uvicorn has created the listening sockets; the earlier `http_host` allow-list check (L282) is what prevents a wrong bind. The method returns without checking anything when `self.should_exit` is set or `self.servers` is empty. `run_http` contains `import logging` and `import sys` inside the function although `logging` is already imported at module level (L16).

## Problem
No functional defect was found: the loopback allow-list and the config-isolation check run before any socket is created, and a failed lifespan startup leads to `sys.exit(1)`. The issue is diagnostic accuracy: an operator reading "Posture-gate failure" for an unrelated exit, or reading the post-start check as a pre-bind guarantee, is misled. Startup logs are the main evidence operators and the watchdog use when a server fails to come up. Confidence is High for the code facts and Low that any operator is currently affected.

## Reason for Change
Startup logs are the main evidence operators and the watchdog use when a server fails to come up. The change is cosmetic and low risk, and carries no urgency.

## Implementation Intent
Make the log message and the post-start check's docstring describe what the code actually does. Keep the pre-bind loopback allow-list as the authoritative guard and the post-start check as defense in depth. Do not alter the order of the loopback check, config isolation, posture gate, and socket creation. Reword or remove the `except SystemExit` log line so it does not claim a posture-gate failure for exits that originate in `server.run()`. Remove the redundant function-local `import logging`.

## Requirements
- `REQ-001`: A `SystemExit` raised from `server.run()` is re-raised with the same exit code and a log message that does not mention the posture gate.
- `REQ-002`: The docstring of `_LoopbackVerifyingServer.startup` states that the check runs after sockets are created and is skipped when startup was aborted (`self.should_exit`) or no server exists (`self.servers` empty).
- `REQ-003`: `ruff check` reports no unused or redefined import in `server.py` (the redundant `import logging` is removed).
- `REQ-004`: Existing tests in `tests/mcp_servers/test_mcp_server_base.py` pass, and a test asserts the corrected message and re-raise for a `SystemExit` from `server.run()`.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify | `run_http` `except SystemExit` (L329-331) logs "Posture-gate failure during startup" for any `SystemExit` from `server.run()`, which is not a posture-gate failure (the gate runs before the `try`); the function also carries a redundant local `import logging` (L277) shadowing the module-level import (L16); `_LoopbackVerifyingServer.startup` docstring (L302-308) does not state its post-bind timing or skip conditions. | `REQ-001`/`REQ-002`/`REQ-003` | `except SystemExit` L329; `"Posture-gate failure during startup"` L331; `import logging` L277; `startup` L307-312 (checked in Step 2) | `tests/mcp_servers/test_mcp_server_base.py` | `Verified` |
| `tests/mcp_servers/test_mcp_server_base.py` | Modify | Add or adjust one unit test asserting the corrected log message and re-raise for a `SystemExit` from `server.run()`. | `REQ-004` | existing `run_http` tests (checked in Step 2) | `tests/mcp_servers/test_mcp_server_base.py` | `Verified` |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/server.py` | Read in full to confirm the gate runs before the `try` and the loopback allow-list precedes socket creation before editing the message/docstring. | `scripts/mcp_servers/server.py` (`REQ-001`/`REQ-002`) |
| `tests/mcp_servers/test_mcp_server_base.py` | Existing `run_http` tests to extend without changing their assertions on startup ordering. | `tests/mcp_servers/test_mcp_server_base.py` (`REQ-004`) |

## Acceptance Criteria
- `REQ-001`: A `SystemExit` raised from `server.run()` is re-raised with the same exit code and a log message that does not mention the posture gate.
- `REQ-002`: The docstring of the post-start verification matches its actual timing (after sockets are created) and skip conditions (startup aborted or no server).
- `REQ-003`: `ruff check` reports no unused or redefined import in `server.py`.
- `REQ-004`: Existing tests in `tests/mcp_servers/test_mcp_server_base.py` pass, plus the new message/re-raise assertion.

## Tests
- Add or adjust one unit test asserting the log message and the re-raise for a `SystemExit` from `server.run()` (`REQ-004`).

## Documentation Impact
Not expected. If MCP lifecycle documentation quotes the log line, update it to the new wording and run the `docs/` checkers from `routing.md`. Otherwise `N/A: no doc quotes the changed log line`.

## Assumptions
- Rewording the message does not break any alerting or doc that matches on the exact string "Posture-gate failure during startup"; if it does, that match must be updated too (open question in the issue).
- The uvicorn paths that can raise `SystemExit` from `server.run()` in the pinned version do not include a legitimate posture-gate signal that must be preserved (not checked in this review; Low confidence, Low impact).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether any alerting or documentation matches on the exact "Posture-gate failure during startup" string before the wording changes | not checked in this review | search logs/alerts/docs for the string; update matches if found | `False` |
| `UNK-02` | which uvicorn paths can raise `SystemExit` from `server.run()` in the pinned version | not checked in this review | record in implementation procedure; Low impact either way | `False` |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify (message, docstring, import) | diagnostic output only; no behavior change | 7 | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_mcp_server_base.py` | Modify (add/adjust one test) | that test file only | N/A | N/A | not applicable (rsynced) |

## Design
This is a Path A (single-file, cosmetic) change. The three corrections are independent and localized:
- **Message (REQ-001):** Rephrase the `except SystemExit` log line so it attributes the exit to `server.run()` rather than the posture gate. Keep re-raising the `SystemExit` unchanged and keep the `sys.exit(1)` follow-up.
- **Docstring (REQ-002):** Update `_LoopbackVerifyingServer.startup` to state that the check runs after `super().startup()` creates the listening sockets and is skipped when `self.should_exit` is set or `self.servers` is empty. Keep the pre-bind `http_host` allow-list as the authoritative guard.
- **Import cleanup (REQ-003):** Remove the redundant function-local `import logging` (L277); the module-level import (L16) remains.

**Baseline (Step 5):** radon rates `run_http` B(6); `bandit -ll` reports no high/medium findings; `lint-imports` 6 kept / 0 broken; `server.py` churn 7 commits in 30 days (high-churn file — scope the edit tightly to message/docstring/import only).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Correct the `SystemExit` log message in `scripts/mcp_servers/server.py`.** Reword the `except SystemExit` handler so it does not claim a posture-gate failure for exits originating in `server.run()`; keep re-raise and `sys.exit(1)` unchanged (`REQ-001`).
2. **Phase 2: Update the `_LoopbackVerifyingServer.startup` docstring.** State the post-bind timing and skip conditions (`REQ-002`).
3. **Phase 3: Remove the redundant `import logging`.** Delete the function-local `import logging` at L277; keep the module-level import (`REQ-003`).
4. **Phase 4: Repair the tests.** Add or adjust one unit test in `tests/mcp_servers/test_mcp_server_base.py` asserting the corrected message and re-raise (`REQ-004`).
5. **Phase 5: Deployment & verification.** Run the validation commands below.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit | `uv run pytest tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_posture_gate_start_path.py` | pass; new assertion present |
| `scripts/mcp_servers/server.py` | Static | `uv run ruff check scripts/mcp_servers` | no unused/redefined import |
| `scripts/mcp_servers/server.py` | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | clean |

## Risks
- **Risk:** an alert or doc matches the exact "Posture-gate failure during startup" string and stops firing after rewording. → **Mitigation:** answer `UNK-01` by searching for the string; update any match.
- **Risk:** high 30-day churn (7 commits) on `server.py` means the file may have moved during planning. → **Mitigation:** re-verify the target sections at Step 8 freeze against current content.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the `SystemExit` log message | Completed | 20261108-170747 | 20261108-170747 | `run_http` `except SystemExit` now logs `"server.run() exited with SystemExit: %s"`; exit code re-raised intact. |
| 2 | Update the `_LoopbackVerifyingServer.startup` docstring | Completed | 20261108-170747 | 20261108-170747 | Docstring states post-bind timing and returns early when `self.should_exit` set or `self.servers` empty. |
| 3 | Remove the redundant `import logging` | Completed | 20261108-170747 | 20261108-170747 | Only module-level `import logging` remains; no function-local copy. |
| 4 | Repair the tests | Completed | 20261108-170747 | 20261108-170747 | Added `test_systemexit_from_server_run_reraised_with_new_message` asserting new wording + intact exit code. |
| 5 | Deployment & verification | Completed | 20261108-170747 | 20261108-170747 | ruff/bandit/radon/lint-imports clean; pytest 2586 passed, 5 skipped. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-085934_01_scripts_mcp_servers_server.py.md | 1, 2, 3, 4 | Procedure | Completed | 20261108-170747 | 20261108-170747 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-132117_mcpstartup004_run-http-diagnostics-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-214719
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_mcp_server_base.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-085934 -->
