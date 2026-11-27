## Goal
- Apply one redaction and diagnostic-display model across CLI output, lifecycle errors, internal logs, WAL and session-persistence logging, stderr log management, process snapshots, and Memory display, so normal CLI output is safe for terminal capture and screen sharing while raw details stay only in secret-masked internal logs.

## Priority
Medium

## Scope
- **In-Scope**: common redaction helper extensions (URL userinfo/query/fragment stripping, path-to-logical-identifier replacement, redact-before-truncate); safe public error summaries and stable error codes; masked internal logging; stderr log file mode `0o600`, configured size and generation retention enforcement, writer-compatible rotation; public process snapshots without internal log paths; CLI display policy for `/config`, `/mcp status`, and Memory display; documentation alignment.
- **Out-of-Scope**: process ownership and health semantics (issue `20261119-145305_cliplc007_mcp-process-ownership`, issue `20261119-145306_cliplc008_mcp-health-capability`); changing existing `_mask_secrets` masking behavior for current consumers.
- **Dependencies**: the five sibling issues listed in the source Issue are archived and their plans completed; only deployment-pending rows remain, which do not block this Plan.
  - **Depends on**: `plans/done/20261124-095950_cliplc004_bounded-shutdown-machine.md` | all | shutdown outcome strings feed public summaries; the final error model must exist before redaction is standardized on it
  - **Depends on**: `plans/done/20261124-110935_cliplc005_staged-reload-transaction.md` | all | pending-config display and the config display surface were finalized by that plan; display policy changes apply to its final shape
  - **Depends on**: `plans/done/20261125-111909_cliplc006_mcp-launch-spec-credentials.md` | all | launch-spec credential handling defines what must never reach error summaries
  - **Depends on**: `plans/done/20261125-232847_cliplc007_mcp-process-ownership.md` | all | process snapshot shape and termination-outcome display were frozen by that plan
  - **Depends on**: `plans/done/20261126-111451_cliplc008_mcp-health-capability.md` | all | health probe display (endpoint URL, reasons) was finalized by that plan

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 9). Related archived work: `issues/done/20261120-114212_agentcfg004_config-ownership-split.md` is unrelated; the related archived fix is `issues/done/20261118-025717_agentfd001_stderr-log-fd-leak.md`. Sensitive operational details currently reach CLI output and logs through several independent paths with no single redaction model.

## Problem
Verified against current source at `9ad65ba903373406c0f2c8809428e3e751f3facc`:

- `scripts/agent/http_lifecycle_stderr_log_manager.py` rotates by `os.rename()` (lines 111-135, not the Issue's stale 92-110). The rename moves the active file, so the subprocess writer fd keeps writing to the rotated file and `read_tail()` reads the new empty path — rotation is incompatible with an active writer. The Issue's "creates a new file" wording is wrong: no new file is created. `rotate_log()` has no production caller (tests only), which resolves the Issue's Unknown.
- Log directory is `tempfile.gettempdir()/mcp_server_logs/{server_key}` with the server key as the directory name; dir mode `0o700`; the log file is opened `open(path, "ab")` with no explicit `0o600` mode; no retention/generation purge exists. Configured limits (`max_stderr_log_size_mb`, `max_stderr_log_files`) exist in `scripts/shared/mcp_config.py` but are not enforced by `StderrLogManager`.
- `HttpStartupError.__str__` already masks the stderr tail via `_mask_secrets`, so the Issue's "raw exceptions" claim is partially disconfirmed; however `reason` strings can contain absolute log-dir paths (for example `Cannot create log directory '{log_dir}'`).
- `scripts/agent/http_lifecycle_health_checker.py` logs full URLs at debug level.
- `ProcessInfoSnapshot.stderr_log` carries the internal absolute log path (`scripts/agent/http_lifecycle.py` line 212).
- Memory display writes entry content unmasked (`scripts/agent/commands/memory_data_ops.py` line 357).
- `scripts/agent/secrets_masker.py` already masks URL userinfo (`user:password@host`) via the pattern at lines 39-43; the Plan's earlier "keyed secrets only" claim was stale. What is missing is query/fragment stripping and path redaction.
- `scripts/agent/wal_checkpoint_manager.py` (logging at lines 200-203 and 242-245, reached from the `sqlite3.Error` handlers at 196 and 230) and `scripts/agent/session_persister.py` (lines 204-205, 333) log raw `sqlite3.Error` messages.
- `/mcp status` shows the raw configured endpoint URL (`scripts/agent/services/mcp_status.py` line 199); `/config` shows `llm_url` and approval protected paths (`scripts/agent/commands/cmd_config_display.py` lines 43, 88-89).
- Documentation drift: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` line 73 documents the stderr log location as `<log_dir>/scripts/mcp_servers/{server_key}.stderr.log`, which does not match the actual location.

## Reason for Change
Information-disclosure risk. The dependency plans have landed their final state and error models, so the redaction model can now be fixed once against stable surfaces.

## Implementation Intent
Extend the existing common secret masker with URL and path redaction; route every public summary, CLI display line, and internal log message through it before truncation; make stderr log management enforce mode, retention, and writer-compatible rotation; replace internal log paths in public snapshots with logical identifiers; keep raw detail available only through the existing explicit verbose opt-in (`/debug verbose`).

## Requirements
- `REQ-001`: Extend the common redaction helper with URL redaction (strip userinfo, query, fragment) and path redaction (basename, root-relative id, or logical identifier); redaction applies before truncation.
- `REQ-002`: Stable public error codes and safe summaries; no absolute paths, raw config values, command paths, or token-derived details in public error text.
- `REQ-003`: Internal logs pass the common secret masker; health logging does not emit full credential-bearing URLs.
- `REQ-004`: SQLite error details in WAL checkpoint and session-persistence logging are reduced to error type plus masked message.
- `REQ-005`: Normal CLI output (`/config`, `/mcp status`, Memory display) contains no credential, absolute path, raw SQLite error, or credential-bearing URL; raw detail is available only via explicit verbose opt-in.
- `REQ-006`: Stderr logs use the validated server-key slug directory, file mode `0o600`, configured size and generation limits with expired-generation purge, and rotation compatible with the active writer (copy-and-truncate); writer and tail-reader paths stay consistent.
- `REQ-007`: Public process snapshots omit internal log paths; the snapshot field carries a logical identifier instead.
- `REQ-008`: Documentation states the public diagnostic policy, the actual stderr log location, retention, and verbose-mode rules.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed — see this Plan's Step 8 report in the workflow run).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Add `redact_url` (query/fragment stripping) and `redact_path` helpers; keep existing masking behavior unchanged | Common redaction model needs URL and path forms | REQ-001; AC-1, AC-2 | Corrected by Step 3a: URL userinfo masking already exists at `scripts/agent/secrets_masker.py` lines 39-43, so only query/fragment stripping and path redaction are new; keyed-secret patterns are lines 14-38 | `tests/agent/test_secrets_masker.py` | Verified |
| `scripts/agent/http_lifecycle_errors.py` | Safe public summaries and stable error codes; strip absolute paths from `reason` | `reason` can embed the absolute log dir path | REQ-002; AC-1 | `scripts/agent/http_lifecycle_stderr_log_manager.py` line 76 builds `Cannot create log directory '{log_dir}'`; `__str__` already masks the tail | `tests/agent/test_http_lifecycle.py` | Verified |
| `scripts/agent/http_lifecycle_health_checker.py` | Redact URLs before logging; redact before truncating | Full URLs logged at debug level | REQ-003; AC-2 | `scripts/agent/http_lifecycle_health_checker.py` debug lines log `%s` URLs | `tests/agent/test_http_lifecycle_health_check.py` | Verified |
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | File mode `0o600`; enforce configured size and generation limits with purge; writer-compatible copy-and-truncate rotation; consistent writer and tail-reader paths | Rename rotation breaks the active writer fd; no mode or retention enforcement | REQ-006; AC-3 | `scripts/agent/http_lifecycle_stderr_log_manager.py` lines 67-83 (dir `0o700`, `open(path, "ab")`), 111-135 (`os.rename`), no purge | `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Verified |
| `scripts/agent/http_lifecycle.py` | Snapshot builder emits a logical identifier instead of the internal log path | Snapshot carries the absolute path | REQ-007; AC-4 | `scripts/agent/http_lifecycle.py` line 212 | `tests/agent/test_http_lifecycle.py` | Verified |
| `scripts/agent/services/models.py` | `ProcessInfoSnapshot.stderr_log` field semantics: logical identifier, field name preserved | Public snapshot must omit internal paths | REQ-007; AC-4 | `scripts/agent/services/models.py` line 47 | `tests/agent/test_lifecycle.py` | Verified |
| `scripts/agent/services/mcp_status.py` | Redact the endpoint URL in the probe result | Raw configured URL reaches status display | REQ-005; AC-1 | `scripts/agent/services/mcp_status.py` line 199 | `tests/agent/services/test_agent_mcp_status.py` | Verified |
| `scripts/agent/commands/cmd_mcp.py` | Display policy: redacted endpoint, PID/PGID retained, no internal paths | `/mcp status` is normal CLI output | REQ-005; AC-1 | `scripts/agent/commands/cmd_mcp.py` formats `McpProbeResult` rows | `tests/agent/commands/test_cmd_mcp.py` | Verified |
| `scripts/agent/commands/cmd_config_display.py` | Display policy: redact `llm_url` userinfo and replace protected paths with logical identifiers | `/config` shows raw URL and configured paths | REQ-005; AC-1 | `scripts/agent/commands/cmd_config_display.py` lines 43, 88-89 | `tests/agent/commands/test_agent_cmd_config.py` | Verified |
| `scripts/agent/commands/memory_data_ops.py` | Memory display policy: mask entry content and summary through the common masker | Full content written unmasked | REQ-005; AC-1 | `scripts/agent/commands/memory_data_ops.py` line 357 | `tests/agent/commands/test_memory_data_ops.py` | Verified |
| `scripts/agent/wal_checkpoint_manager.py` | Reduce logged SQLite errors to type name plus masked message | Raw `sqlite3.Error` logged | REQ-004; AC-2 | `scripts/agent/wal_checkpoint_manager.py` lines 196, 230 | `tests/agent/test_wal_checkpoint_manager.py` | Verified |
| `scripts/agent/session_persister.py` | Mask SQLite error messages before logging | Raw `sqlite3.Error` logged | REQ-004; AC-2 | `scripts/agent/session_persister.py` lines 204-205, 333 | `tests/agent/test_session_persister.py` | Verified |
| `tests/agent/test_secrets_masker.py` | Redaction-leak tests for URL and path forms (added before editing consumers) | New helper functions need coverage | REQ-001; AC-1, AC-2 | Issue Testing Expectations | itself | Verified |
| `tests/agent/test_http_lifecycle.py` | Assert safe summaries and logical-identifier snapshots | Error and snapshot behavior change | REQ-002, REQ-007; AC-1, AC-4 | Existing error/snapshot assertions | itself | Verified |
| `tests/agent/test_lifecycle.py` | Snapshot dict expectations updated to the logical identifier | Field semantics change | REQ-007; AC-4 | `tests/agent/test_lifecycle.py` lines 973, 1380-1402, 1625 | itself | Verified |
| `tests/agent/test_http_lifecycle_health_check.py` | Assert logged URLs are redacted | Logging behavior change | REQ-003; AC-2 | Existing logging assertions | itself | Verified |
| `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Active-subprocess rotation test, file-mode `0o600`, retention purge tests | New behavior needs coverage | REQ-006; AC-3 | Issue Testing Expectations | itself | Verified |
| `tests/agent/test_wal_checkpoint_manager.py` | Assert masked SQLite error output | Logging behavior change | REQ-004; AC-2 | Existing logging assertions | itself | Verified |
| `tests/agent/test_session_persister.py` | Assert masked SQLite error output | Logging behavior change | REQ-004; AC-2 | Existing logging assertions | itself | Verified |
| `tests/agent/services/test_agent_mcp_status.py` | Assert redacted endpoint in probe result | Display data change | REQ-005; AC-1 | Existing probe assertions | itself | Verified |
| `tests/agent/commands/test_cmd_mcp.py` | Display-policy assertions; snapshot dict shape unchanged (field name preserved) | Display output change | REQ-005, REQ-007; AC-1, AC-4 | `tests/agent/commands/test_cmd_mcp.py` lines 347, 384 | itself | Verified |
| `tests/agent/commands/test_agent_cmd_config.py` | Display-policy assertions for URL and path forms | Display output change | REQ-005; AC-1 | Existing config-display assertions | itself | Verified |
| `tests/agent/commands/test_memory_data_ops.py` | Assert masked Memory content display | Display output change | REQ-005; AC-1 | Existing display assertions | itself | Verified |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Align documented stderr log location with the actual location; state retention and mode policy | Documented path does not match code | REQ-008; AC-2 | `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` line 73 | N/A: documentation check via `tools/check_workitem_structure.py` and `rules/tool-gates.md` doc gate | Verified |
| `docs/23_agent/agent_02_runtime-architecture.md` | State the public diagnostic display policy (PID/PGID retained, logical identifiers, verbose opt-in) | Snapshot and display semantics change | REQ-008; AC-1, AC-4 | `docs/23_agent/agent_02_runtime-architecture.md` line 173 describes the process record | N/A: documentation gate per `rules/tool-gates.md` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Regenerate the reference table after the `StderrLogManager` constructor change | Generated-reference domain hit by the predictable fallout check | REQ-006, REQ-008 | `docs/23_agent/agent_13_reference-api-generated.md` line 98 lists `StderrLogManager` | N/A: `generate_reference_table.py --check` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/mcp_config.py` | Configured `max_stderr_log_size_mb` and `max_stderr_log_files` already exist; values are passed as plain constructor values, not the config model | REQ-006 |
| `scripts/agent/lifecycle_router.py` | `ProcessInfoSnapshot` consumer; delegates the snapshot dict without field-specific code, so it is `not affected` beyond the field-semantics change | REQ-007 |
| `scripts/agent/diagnostic_store.py` | `_mask_secrets` consumer (`detects_secrets`); existing behavior preserved, `not affected` | REQ-001 |
| `scripts/agent/shared/retry_helper.py` | `_mask_secrets` consumer; `not affected` | REQ-001 |
| `scripts/agent/startup_mcp_starter.py` | `_mask_secrets` consumer; `not affected` | REQ-001 |
| `scripts/agent/tool_approval.py` | `_mask_secrets` consumer; `not affected` | REQ-001 |
| `scripts/agent/tool_output.py` | `_mask_secrets` consumer; `not affected` | REQ-001 |
| `scripts/agent/tool_result_formatter.py` | `_mask_secrets` consumer; `not affected` | REQ-001 |
| `scripts/agent/commands/cmd_debug.py` | Existing verbose opt-in (`/debug verbose`) is the verbose boundary this Plan reuses, not modifies | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-002, REQ-005): No credential, absolute path, raw SQLite error, or credential-bearing URL appears in normal CLI output; covered by redaction-leak tests for `/config`, `/mcp status`, Memory, and shutdown output.
- AC-2 (REQ-001, REQ-003, REQ-004): Internal logs pass the common secret masker; redaction happens before truncation.
- AC-3 (REQ-006): Stderr rotation preserves active writes and tail access (real-subprocess test); file mode `0o600` and configured retention are enforced with expired-generation purge.
- AC-4 (REQ-007): Public process snapshots omit internal log paths; the snapshot field carries a logical identifier.

## Tests
- Redaction-leak tests are added before editing consumers (Issue AI Implementation Instruction): error messages containing tokens, paths, URLs, and SQLite details (`tests/agent/test_secrets_masker.py`, `tests/agent/test_http_lifecycle.py`).
- Display tests: `/config`, `/mcp status`, Memory, and shutdown output (`tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_memory_data_ops.py`, `tests/agent/services/test_agent_mcp_status.py`).
- Active-subprocess log rotation with a real subprocess; retention and file-mode tests (`tests/agent/test_http_lifecycle_stderr_log_manager.py`).
- Snapshot expectations (`tests/agent/test_lifecycle.py`, `tests/agent/test_http_lifecycle.py`).
- Run ruff, mypy, import-linter, and the full test suite; diff-cover on the change.

## Documentation Impact
Yes. Public diagnostic policy, stderr log location, retention, and verbose-mode rules. Target docs via `docs/00_index.md` "Document References by Task": MCP server spec (stderr location and retention, REQ-006, REQ-008) and Agent spec (display policy, REQ-005, REQ-008); the generated reference table is regenerated for the changed public API (REQ-006). The three `docs/` rows in `Implementation Target Files` record the concrete files.

## Assumptions
- The existing verbose opt-in (`/debug verbose`, `scripts/agent/commands/cmd_debug.py`) is the accepted verbose boundary; no new opt-in mechanism is added.
- PID and PGID are operational identifiers, not secrets, and remain displayed in normal output (Design D5); only internal paths are replaced with logical identifiers.
- The `ProcessInfoSnapshot.stderr_log` field name is preserved; only its value semantics change, so dict-shape consumers and pinned tests are unaffected.
- Configured stderr limits are passed to `StderrLogManager` as plain values at construction; no agent module imports MCP server config models (import-linter contract `No agent module imports MCP server config models` stays KEPT).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the stderr log root should become a configurable deployment log directory; today it is hardcoded to `tempfile.gettempdir()` | No deployment configuration exists in `config/` for the log root | User/deployment decision; this Plan keeps the current root and aligns the docs to it | False |
| UNK-02 | Stable public error-code vocabulary for lifecycle errors: reuse the existing `StrEnum` values or introduce a dedicated code enum | The Issue requires "stable public error codes" but names no vocabulary | Decide at implementation against `scripts/agent/http_lifecycle_errors.py`; keep existing values as the code set unless a collision is found | False |

Resolved during verification (formerly the Issue's `不明`): the production call site of `rotate_log()` — none exists, tests only; the retention cleanup implementation — none exists, this Plan adds it; the PID/PGID/log-path display policy — decided as D5.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Add URL/path redaction helpers | 21 consumer candidates via `tools/scan_change_consumers.py` (additive; existing behavior preserved) | 4 | N/A: `git-fame` unavailable in this environment | N/A: no deploy change |
| `scripts/agent/http_lifecycle_errors.py` | Safe summaries, stable codes | 30+ references across `scripts/agent` lifecycle modules | 3 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/http_lifecycle_health_checker.py` | URL redaction before logging | Single lifecycle consumer | 6 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Mode, retention, writer-safe rotation | `scripts/agent/http_lifecycle.py` plus subprocess writer fds | 2 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/http_lifecycle.py` | Snapshot builder emits logical identifier | 4 `ProcessInfoSnapshot` consumer files | 6 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/services/models.py` | Field semantics change | 4 consumer files (`scripts/agent/http_lifecycle.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/services/mcp_status.py`, `tests/agent/test_lifecycle.py`) | 10 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/services/mcp_status.py` | Endpoint URL redaction | `/mcp status` display path | N/A: not measured separately | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_mcp.py` | Display policy | CLI display only | 5 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/cmd_config_display.py` | Display policy | CLI display only | 5 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/commands/memory_data_ops.py` | Masked Memory display | CLI display only | 4 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/wal_checkpoint_manager.py` | Masked SQLite error logging | Shutdown path logging only | 2 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/session_persister.py` | Masked SQLite error logging | Diagnostics path logging only | 5 | N/A: `git-fame` unavailable | N/A: no deploy change |

## Design
Grounded in the Path B analyses at HEAD `9ad65ba903373406c0f2c8809428e3e751f3facc`.

Validation quality baseline:
- radon: all target source files are complexity grade A (no hotspots).
- vulture: no dead code in the target files.
- bandit: one pre-existing Low finding (`B404` subprocess import in `scripts/agent/http_lifecycle_health_checker.py`); no new findings expected.
- diff-cover: no diff against `master` at HEAD, so the baseline is empty; coverage is measured on the change itself.
- import-linter: 6 contracts KEPT at HEAD; the design preserves `No agent module imports MCP server config models`.
- Historical analysis: churn per file recorded in `Affected areas`; `git-fame` (bus factor) unavailable in this environment.
- **Overlap check disposition (Step 8b)**: `tools/check_plan_target_overlaps.py` reported 2 findings, both between pre-existing plans `plans/20261126-072155_mcpai012_mcp-design-docs-update.md` and `plans/20261126-073010_mcpai013_github-resource-scope-refine.md` (`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`), and `plans/20261126-072155_mcpai012_mcp-design-docs-update.md` and `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` (`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`). None involves any row of this Plan: `not affected: external overlap between other Plans, no shared target path with this Plan`.

Consumer scan results (`tools/scan_change_consumers.py`):
- Seed `_mask_secrets` (21 candidates): target rows `scripts/agent/secrets_masker.py`, `scripts/agent/http_lifecycle_errors.py`, `scripts/agent/http_lifecycle_health_checker.py`; reference rows for `scripts/agent/diagnostic_store.py`, `scripts/agent/shared/retry_helper.py`, `scripts/agent/startup_mcp_starter.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_output.py`, `scripts/agent/tool_result_formatter.py`; all `not affected: existing masking behavior is preserved, new helpers are additive`.
- Seed `ProcessInfoSnapshot`: target rows `scripts/agent/services/models.py`, `scripts/agent/http_lifecycle.py`, `tests/agent/test_lifecycle.py`; `scripts/agent/lifecycle_router.py` is a reference row (`not affected: delegates the snapshot dict without field-specific code`).

Predictable fallout check:
- Module size gate (24576 B): all target files are below the gate today; `scripts/agent/http_lifecycle.py` (20449 B) is closest — its change is limited to the snapshot builder; if implementation pushes it over the gate, a split row is required (recorded as a Risk).
- Pinned counts: `tests/agent/commands/test_cmd_mcp.py` lines 347 and 384 pin the snapshot dict shape including `stderr_log`; the field name is preserved, so these are `not affected` beyond value expectations. No test pins a field count.
- Tool inventory: N/A: no tool added or removed.
- Generated blocks: `docs/23_agent/agent_13_reference-api-generated.md` lists `StderrLogManager`; the constructor change requires regeneration (`generate_reference_table.py --check`) — recorded as a target row.

Design decisions (Path B):
- D1 — Common redaction helper location: extend `scripts/agent/secrets_masker.py` with `redact_url` and `redact_path`. Alternative: a new `agent/redaction.py` module; rejected because the masker is already the common secret masker with 10 consumers, and a second boundary would split the redaction model. Compatibility impact: none for existing consumers (additive functions).
- D2 — Rotation strategy: copy the active file's content to the rotated generation, then truncate the active file, so the writer fd and `read_tail()` remain consistent. Alternative: rotate only on restart; rejected because long-running subprocesses would grow unbounded. Purge expired generations per `max_stderr_log_files`.
- D3 — File creation mode: create the stderr log with mode `0o600` (`os.open` flags); directory stays `0o700`.
- D4 — Snapshot field: keep `ProcessInfoSnapshot.stderr_log` as the field name, change its value to a logical identifier (the `stderr.log` basename or a root-relative id). Preserves dict-shape consumers.
- D5 — Display policy: PID and PGID remain displayed in normal output (operational identifiers needed for the documented manual-cleanup path); internal paths are replaced with logical identifiers; Memory content display is masked through the common masker; raw detail is available only via the existing `/debug verbose` opt-in. Alternative: hide PID/PGID; rejected as it breaks the documented operator path.
- D6 — Configured-limit wiring: pass `max_stderr_log_size_mb` and `max_stderr_log_files` as plain values to `StderrLogManager` at construction; do not import the config model, preserving the import-linter contract.

## Implementation steps
1. **Phase 1: Common redaction helper**
   - [ ] Add `redact_url` and `redact_path` to `scripts/agent/secrets_masker.py` (REQ-001)
   - [ ] Add redaction-leak tests before editing consumers in `tests/agent/test_secrets_masker.py` (REQ-001; AC-1, AC-2)
2. **Phase 2: Error and internal-log redaction**
   - [ ] Safe public summaries and stable error codes in `scripts/agent/http_lifecycle_errors.py` (REQ-002; AC-1)
   - [ ] URL redaction before logging in `scripts/agent/http_lifecycle_health_checker.py` (REQ-003; AC-2)
   - [ ] Masked SQLite error logging in `scripts/agent/wal_checkpoint_manager.py` (REQ-004; AC-2)
   - [ ] Masked SQLite error logging in `scripts/agent/session_persister.py` (REQ-004; AC-2)
   - [ ] Update assertions in `tests/agent/test_http_lifecycle.py`, `tests/agent/test_http_lifecycle_health_check.py`, `tests/agent/test_wal_checkpoint_manager.py`, `tests/agent/test_session_persister.py`
3. **Phase 3: Stderr log management**
   - [ ] File mode `0o600`, configured size and generation limits with purge, copy-and-truncate rotation in `scripts/agent/http_lifecycle_stderr_log_manager.py` (REQ-006; AC-3)
   - [ ] Wire configured values as plain constructor arguments (D6; REQ-006)
   - [ ] Active-subprocess rotation, mode, and retention tests in `tests/agent/test_http_lifecycle_stderr_log_manager.py` (REQ-006; AC-3)
4. **Phase 4: Display surfaces and snapshot policy**
   - [ ] Logical identifier in the snapshot builder in `scripts/agent/http_lifecycle.py` and field semantics in `scripts/agent/services/models.py` (REQ-007; AC-4)
   - [ ] Endpoint URL redaction in `scripts/agent/services/mcp_status.py` (REQ-005; AC-1)
   - [ ] Display policy in `scripts/agent/commands/cmd_mcp.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/commands/memory_data_ops.py` (REQ-005; AC-1)
   - [ ] Update assertions in `tests/agent/test_lifecycle.py`, `tests/agent/services/test_agent_mcp_status.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/commands/test_memory_data_ops.py`
5. **Phase 5: Documentation, deployment check, and full validation**
   - [ ] Align stderr log location, retention, and mode policy in `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` (REQ-008)
   - [ ] State the display policy in `docs/23_agent/agent_02_runtime-architecture.md` (REQ-008)
   - [ ] Regenerate `docs/23_agent/agent_13_reference-api-generated.md` via `generate_reference_table.py --check` (REQ-006, REQ-008)
   - [ ] Deployment validation/scripts check: no deploy.sh change; confirm the deployed venv files are current per `skills/deploy/SKILL.md` after commit and push (user's decision to deploy)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Unit: URL and path redaction, redact-before-truncate | `uv run pytest tests/agent/test_secrets_masker.py` | New helper tests pass |
| `scripts/agent/http_lifecycle_errors.py` | Unit: safe summaries, stable codes | `uv run pytest tests/agent/test_http_lifecycle.py` | No absolute paths in public error text |
| `scripts/agent/http_lifecycle_health_checker.py` | Unit: redacted log records | `uv run pytest tests/agent/test_http_lifecycle_health_check.py` | Logged URLs carry no userinfo/query/fragment |
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Unit + integration: real subprocess rotation, mode, retention | `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py` | Writer fd stays valid across rotation; `0o600`; purge enforced |
| `scripts/agent/services/models.py` + `scripts/agent/http_lifecycle.py` | Unit: snapshot value is a logical identifier | `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle.py` | Snapshot omits internal paths |
| Display surfaces | Unit: CLI output redaction | `uv run pytest tests/agent/services/test_agent_mcp_status.py tests/agent/commands/test_cmd_mcp.py tests/agent/commands/test_agent_cmd_config.py tests/agent/commands/test_memory_data_ops.py` | Normal output contains no credentials, absolute paths, raw SQLite errors, or credential-bearing URLs |
| Whole change | Full suite + static gates | `uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`, diff-cover | All pass; contracts KEPT; regenerated reference table current |

## Risks
- **Risk**: `scripts/agent/http_lifecycle.py` (20449 B) is close to the 24576 B module-size gate; snapshot changes could push it over → **Mitigation**: keep the change limited to the snapshot builder; if the gate is exceeded, add a split row per `rules/tool-gates.md`.
- **Risk**: the redaction helper could change other components' output through shared consumers → **Mitigation**: helpers are additive only; the Issue's AI instruction requires stopping and reporting if consumer output changes; consumer scan reference rows lock the unaffected set.
- **Risk**: copy-and-truncate rotation changes crash-recovery semantics (content copied, then truncated) → **Mitigation**: the tail reader and writer paths remain consistent; retention purge is bounded by `max_stderr_log_files`; covered by the real-subprocess rotation test.
- **Risk**: display-policy changes could break pinned display expectations → **Mitigation**: field names preserved; pinned dict-shape tests at `tests/agent/commands/test_cmd_mcp.py` lines 347, 384 verified as value-only changes.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Common redaction helper | Completed | — | 20261127-095232 |  |
| 2 | Phase 2: Error and internal-log redaction | Completed | — | 20261127-095232 |  |
| 3 | Phase 3: Stderr log management | Completed | — | 20261127-095232 |  |
| 4 | Phase 4: Display surfaces and snapshot policy | Completed | — | 20261127-095232 |  |
| 5 | Phase 5: Documentation, deployment check, and full validation | In Progress | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-225455_01_scripts_agent_secrets_masker.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261126-225455_02_scripts_agent_http_lifecycle_errors.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-225455_03_scripts_agent_http_lifecycle_health_checker.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-225455_04_scripts_agent_http_lifecycle_stderr_log_manager.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261126-225455_05_scripts_agent_http_lifecycle.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_06_scripts_agent_services_models.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_07_scripts_agent_services_mcp_status.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_08_scripts_agent_commands_cmd_mcp.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_09_scripts_agent_commands_cmd_config_display.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_10_scripts_agent_commands_memory_data_ops.py.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261126-225455_11_scripts_agent_wal_checkpoint_manager.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-225455_12_scripts_agent_session_persister.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-225455_14_tests_agent_test_http_lifecycle.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261126-225455_24_docs_22_mcp_mcp_03_04_tool-call-tracing-and-lifecycle.md.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261126-225455_25_docs_23_agent_agent_02_runtime-architecture.md.md` | 5 | Procedure | Completed | — | — |
| `implementations/20261126-225455_26_docs_23_agent_agent_13_reference-api-generated.md.md` | 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-210258
- **Evidence revision**: 9ad65ba903373406c0f2c8809428e3e751f3facc
- **Related target files**: `scripts/agent/secrets_masker.py`, `scripts/agent/http_lifecycle_errors.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/http_lifecycle_stderr_log_manager.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/services/models.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/commands/cmd_mcp.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/commands/memory_data_ops.py`, `scripts/agent/wal_checkpoint_manager.py`, `scripts/agent/session_persister.py`, `tests/agent/test_secrets_masker.py`, `tests/agent/test_http_lifecycle.py`, `tests/agent/test_lifecycle.py`, `tests/agent/test_http_lifecycle_health_check.py`, `tests/agent/test_http_lifecycle_stderr_log_manager.py`, `tests/agent/test_wal_checkpoint_manager.py`, `tests/agent/test_session_persister.py`, `tests/agent/services/test_agent_mcp_status.py`, `tests/agent/commands/test_cmd_mcp.py`, `tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/commands/test_memory_data_ops.py`, `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`, `docs/23_agent/agent_02_runtime-architecture.md`, `docs/23_agent/agent_13_reference-api-generated.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `scripts/agent/secrets_masker.py` current patterns (keyed secrets lines 14-38, URL userinfo lines 39-43) | `scripts/agent/secrets_masker.py` | Phase 1 | AC-1, AC-2 | `tests/agent/test_secrets_masker.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `scripts/agent/http_lifecycle_stderr_log_manager.py` line 76 reason path | `scripts/agent/http_lifecycle_errors.py` | Phase 2 | AC-1 | `tests/agent/test_http_lifecycle.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; full-URL debug logging | `scripts/agent/http_lifecycle_health_checker.py` | Phase 2 | AC-2 | `tests/agent/test_http_lifecycle_health_check.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; raw SQLite error logging | `scripts/agent/wal_checkpoint_manager.py` | Phase 2 | AC-2 | `tests/agent/test_wal_checkpoint_manager.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; raw SQLite error logging | `scripts/agent/session_persister.py` | Phase 2 | AC-2 | `tests/agent/test_session_persister.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; display policy; `scripts/agent/services/mcp_status.py` line 199 | `scripts/agent/services/mcp_status.py` | Phase 4 | AC-1 | `tests/agent/services/test_agent_mcp_status.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; display policy | `scripts/agent/commands/cmd_mcp.py` | Phase 4 | AC-1 | `tests/agent/commands/test_cmd_mcp.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; display policy; `scripts/agent/commands/cmd_config_display.py` lines 43, 88-89 | `scripts/agent/commands/cmd_config_display.py` | Phase 4 | AC-1 | `tests/agent/commands/test_agent_cmd_config.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; Memory content disclosure; `scripts/agent/commands/memory_data_ops.py` line 357 | `scripts/agent/commands/memory_data_ops.py` | Phase 4 | AC-1 | `tests/agent/commands/test_memory_data_ops.py` | Confirmed by repository evidence |
| REQ-006 | Explicit in code (rotation by rename, corrected); `scripts/agent/http_lifecycle_stderr_log_manager.py` lines 67-83, 111-135 | `scripts/agent/http_lifecycle_stderr_log_manager.py` | Phase 3 | AC-3 | `tests/agent/test_http_lifecycle_stderr_log_manager.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; `scripts/agent/http_lifecycle.py` line 212 | `scripts/agent/http_lifecycle.py` | Phase 4 | AC-4 | `tests/agent/test_http_lifecycle.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; `scripts/agent/services/models.py` line 47 | `scripts/agent/services/models.py` | Phase 4 | AC-4 | `tests/agent/test_lifecycle.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` line 73 drift | `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Phase 5 | AC-2 | N/A: documentation gate per `rules/tool-gates.md` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; display policy | `docs/23_agent/agent_02_runtime-architecture.md` | Phase 5 | AC-1, AC-4 | N/A: documentation gate per `rules/tool-gates.md` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; generated reference row for `StderrLogManager` | `docs/23_agent/agent_13_reference-api-generated.md` | Phase 5 | AC-2 | `generate_reference_table.py --check` | Confirmed by repository evidence |
