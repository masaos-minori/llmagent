## Goal
Classify `mcp_dedup.sqlite` as a disposable cache (maintainer decision 2026-11-09, Option B), make loss or recreation of the store unable to cause a silent repeat of a non-retryable side effect (non-retryable tools are rejected — fail closed — until an operator resolves the state), register the two remaining degradation paths under an approved ADR-004 exception, and stop sharing `config/mcp_dedup.toml` between the dispatcher and the Agent by giving each process its own configuration. No backup of the store; recovery is recreation.

## Priority
High

## Scope
- **In-Scope**: Record in ADR-008 that `mcp_dedup.sqlite` is a disposable cache with the owner (the shared MCP dispatcher layer), recovery by recreation, no backup requirement, and a Recovery Policy Matrix row stating the post-recreation rule for non-retryable tools. Implement the fail-closed-on-empty-store rule in `dispatch.py` and the store, including detection of a missing or recreated store and an operator-resolution step, with tests. Make a failed write after a successful open fail closed for non-retryable tools (retryable keeps warning-only) under the same ADR-004 exception, with tests. Move `pending_timeout_minutes` into `config/agent.toml` and reduce `config/mcp_dedup.toml` to the dispatcher's single-owner config; refactor the Agent's config reads so no process imports the dispatcher's dedup config. Add the database to `db_01`, `db_08`, and the dependency graph, and make `db_03_07` consistently describe a disposable cache.
- **Out-of-Scope**: Implementing fingerprint validation of the store (adrrev005). Rewriting the manual recovery procedure (adrrev009). Changing which tools are classified retryable/non-retryable beyond moving them. Deleting `config/mcp_dedup.toml` outright when a single reader remains. Fabricating ADR approval records.
- **Dependencies**:
  - **Depends on**: `issues/20261109-112715_adrrev005_schema-fingerprint-unify.md` | phase all | fingerprint validation of the store; the execution snapshot reads `user_version`, so the replay-equality decision depends on it. Not blocking this Plan's documentation rows, but blocks validating the store's schema-stamp inputs.
  - **Depends on**: `issues/20261109-112739_adrrev006_eventbus-future-decision.md` | phase all | the execution snapshot's `eventbus_db_path` input is changed here; coordinate replay-equality inputs. Not blocking the config-isolation rows.
  - **Blocks**: `issues/20261109-112922_adrrev009_adr008-recovery-align.md` | phase all | adrrev009 records the ADR-008 matrix outcome this Plan produces; this Plan must Freeze the classification before adrrev009 implements it.

## Background
The Agent must never silently re-execute a completed non-retryable tool. `mcp_dedup.sqlite` (`tool_call_state`) is the durable store behind the shared MCP dispatcher (`dispatch_tool`). It is owned by the dispatcher across the ADR-008 boundary: `scripts/agent/workflow/tool_call_state_ops.py` explicitly never touches `mcp_dedup.sqlite`, and the Agent's own view lives in `workflow.sqlite`. The maintainer classified it as a disposable cache on 2026-11-09 (Option B), so it is not backed up and recovery is recreation. Two problems follow from that classification and from the current code, both confirmed by reading the live control flow against HEAD `dab0fdf30` (= current HEAD `e700efa5f`; no commit between them touches any key file).

## Problem
- **Empty-store re-execution gap (the central bug).** `DedupStore.__init__` (`mcp_dedup.py` L232-246) runs `CREATE TABLE IF NOT EXISTS` and stamps `PRAGMA user_version`; it succeeds on a missing or recreated file and returns a handle to a fresh, empty store. `_dedup_context()` (`dispatch.py` L175-194) therefore returns a non-None store even when the DB was just recreated; it fails open (sets `_dedup_disabled=True`, returns `(None, None)`) only when `open_dedup_store` raises. In `dispatch_tool`, an empty store makes `store.lookup(key)` return None, so `row is None` and the code takes the `else` branch (`dispatch.py` L405-412): `record_pending`, then `await handler(args)` (L431). There is no "is this store freshly created?" check, so the tool executes. Fail-closed (`dedup_store_error`) fires only on (a) init failure -> the `(None, None)` path (L413-428) or (b) `lookup` raising `sqlite3.Error`/`OSError` (L309-323). An empty-but-open store hits neither. Conclusion: a non-retryable tool re-executes after the store is lost or recreated — exactly the recovery scenario for a disposable cache.
- **Third, quieter degradation path.** `_store_op` (`mcp_dedup.py` L209-216) logs a warning and returns `False` on a failed write after a successful open; the caller ignores the return and continues. For a non-retryable tool against an empty store, if `record_pending` itself fails the tool still executes (warning only). This is the post-open write-failure gap the issue wants made fail-closed for non-retryable tools.
- **One config file shared by several processes.** `load_dedup_config()` resolves `resolve_config_dir() / "mcp_dedup.toml"` (`mcp_dedup.py` L80) and is called by `dispatch.py:183` (every MCP server process using the shared dispatcher), by `workflow_engine.py:167` (the Agent pending timeout), and transitively by `tool_runner.py:24` (`from shared.mcp_dedup import retry_class`). Multiple process kinds read one file, coupling their lifecycles contrary to ADR-002.
- **Documentation gaps.** `db_03_07` L99 calls the store "a separate system of record" and cites the archived `toolstate001` issue; L148 calls it a "replay cache" whose "fresh empty store only means the next call of each key runs for real"; L150 notes `db_08` does not yet list the store. "System of record" vs "replay cache" contradict each other. ADR-008 has a Recovery Policy Matrix (L86) and L138 requires extending it before deploying a system-of-record store, but `mcp_dedup` appears nowhere in ADR-008. `db_08_active_databases.md` does not list `mcp_dedup`. ADR-004 contains zero `dedup` mentions, so the retryable fail-open and the post-open write-failure degradation are unregistered fail-opens.

## Reason for Change
- The classification determines whether operators must back up the store and how recovery works; without a fail-closed rule for the empty-store mode, the "disposable cache" decision is not operational — recovery actively weakens the non-retryable guarantee.
- The empty-store gap is a real fail-open on a safety input (non-retryable tools), so under ADR-004 it needs either a fail-closed change (adopted) or an approved exception. The fix is the fail-closed change; the retryable overlay-only behavior needs an approved exception.
- Timing: depends on the schema-validation mechanism (adrrev005) for the `user_version` replay input, and blocks adrrev009 (ADR-008 alignment), which records the matrix outcome.

## Implementation Intent
Keep the store a disposable cache. Detect "lost or recreated" out-of-band (not inside the lossable DB file), and when the store is missing or freshly recreated reject non-retryable tools (fail closed) until an operator resolves them; retryable tools keep the audited overlay-only `store_error` behavior registered as an approved ADR-004 exception. Make a failed write after a successful open fail closed for non-retryable tools and warning-only for retryable ones. Give each process its own configuration: `pending_timeout_minutes` moves to `agent.toml`; `mcp_dedup.toml` is reduced to the dispatcher's single-owner config; the Agent stops importing the dispatcher's dedup config. Record all of it in ADR-008, ADR-004, `db_01`, `db_03_07`, `db_08`.

## Requirements
- `REQ-001`: When `mcp_dedup.sqlite` is missing or freshly recreated, non-retryable tools MUST be rejected (fail closed, `dedup_store_error` or a new error type) and MUST NOT execute the side effect until an operator resolves the state; a never-seen key on a genuinely fresh store MUST still execute its first call.
- `REQ-002`: A retryable tool whose store is unavailable proceeds overlay-only with a `store_error` marker, registered as an approved ADR-004 exception with written rationale; a failed write after a successful open is fail closed for non-retryable tools and warning-only for retryable ones.
- `REQ-003`: The "lost or recreated" detection MUST be stored out-of-band (outside the lossable DB file); it MUST NOT rely solely on the database file that can be lost.
- `REQ-004`: No process reads `config/mcp_dedup.toml`; each process reads only its own configuration (`pending_timeout_minutes` in `agent.toml`; dispatcher store settings in its own config). Moving the retry-class classification MUST NOT default any tool to a weaker class (unknown tools stay non-retryable).
- `REQ-005`: ADR-008 classifies `mcp_dedup.sqlite` as a disposable cache with owner, recovery by recreation, no backup, and a Recovery Policy Matrix row stating the post-recreation rule; the store appears in `db_01`, `db_08`, and the dependency graph; `db_03_07` describes it consistently as a disposable cache with no "system of record" wording and no stale citation.
- `REQ-006`: The retryable fail-open and the post-open write-failure degradation are listed as approved ADR-004 exceptions with rationale; the ADR amendments carry a maintainer approval record written by a maintainer (this Plan fabricates none).

## Implementation Target Files
**Freeze status**: Frozen (`20261110-230633`; `check_workitem_structure.py` and
`check_plan_target_overlaps.py` both report No findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Modify | Add out-of-band "lost or recreated" detection (`REQ-003`); make `_store_op` failures fail closed for non-retryable tools (`REQ-002`); expose an operator-resolution step that clears the lost/recreated flag (`REQ-001`). | REQ-001..REQ-003 | `DedupStore.__init__` succeeds on a missing/recreated file (L232-246); `_store_op` logs+returns `False`, caller ignores (L209-216). | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/mcp_servers/dispatch.py` | Modify | Wire the fail-closed rejection for a missing/recreated store (`REQ-001`); keep retryable overlay-only `store_error` (`REQ-002`); route the operator-resolution step. | REQ-001, REQ-002 | `dispatch_tool` else-branch L405-412 `record_pending` → `await handler(args)` L431 with no fresh-store check; fail-closed only on init failure L413-428 or lookup exception L309-323. | `tests/mcp_servers/test_mcp_dispatch.py` | Verified |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Read `pending_timeout_minutes` from the Agent's own config instead of `load_dedup_config()` (`REQ-004`). | REQ-004 | `workflow_engine.py:167` `load_dedup_config().pending_timeout_minutes * 60`. | `tests/agent/test_tool_runner.py` | Needs confirmation |
| `scripts/agent/tool_runner.py` | Modify | Stop importing the dispatcher's dedup config for `retry_class`; obtain the classification from the Agent's own stored state (`REQ-004`). | REQ-004 | `tool_runner.py:24` `from shared.mcp_dedup import retry_class`. | `tests/agent/test_tool_runner.py` | Needs confirmation |
| `config/agent.toml` | Modify | Add `pending_timeout_minutes` (moved from `mcp_dedup.toml`). | REQ-004 | Consumed by `workflow_engine.py:167`; currently absent. | none (config) | Verified |
| `config/mcp_dedup.toml` | Modify | Reduce to the dispatcher's single-owner config: remove `pending_timeout_minutes` (moves to `agent.toml`); keep `db_path`, `retention_days`, `[retry_class]`. | REQ-004 | After the move the dispatcher is the sole reader; `tool_runner.py` refactor removes the second reader. | none (config) | Verified |
| `tests/shared/test_mcp_dedup.py` | Add/Modify | Lost/recreated detection, fail-closed non-retryable rejection, per-process config isolation. | REQ-001, REQ-003, REQ-004 | — | — | Verified |
| `tests/mcp_servers/test_mcp_dispatch.py` | Add/Modify | Non-retryable rejection on empty/fresh store, post-open write-failure fail-closed, retryable exception. | REQ-001, REQ-002 | Existing `test_store_error_retryable_proceeds_non_retryable_fails_closed` (L521) and `test_init_failure_fail_closed_and_degrade` (L555). | — | Verified |
| `tests/agent/test_tool_runner.py` | Add/Modify | `retry_class` sourced from the Agent's own state, not the dispatcher config. | REQ-004 | — | — | Needs confirmation |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (ADR-008) | Modify | Classify `mcp_dedup.sqlite` as disposable cache (owner, recovery by recreation, no backup) and add a Recovery Policy Matrix row. | REQ-005, REQ-006 | ADR-008 Recovery Policy Matrix (L86) and L138 have no `mcp_dedup` row. | none (doc) | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (ADR-004) | Modify | Register the retryable fail-open and the post-open write-failure fail-closed exceptions with rationale; write the maintainer approval record. | REQ-002, REQ-006 | Zero `dedup` mentions in ADR-004. | none (doc) | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | Add `mcp_dedup.sqlite` to the schema/dependency overview. | REQ-005 | Not listed. | none (doc) | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Remove "system of record" wording (L99), resolve "system of record" vs "replay cache" inconsistency (L148), drop the archived `toolstate001` citation (L100). | REQ-005 | Internal inconsistency confirmed at L99/L100/L148. | none (doc) | Verified |
| `docs/41_db/db_08_active_databases.md` | Modify | Add `mcp_dedup.sqlite` with its recreation rule. | REQ-005 | Not listed. | none (doc) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Confirms the dispatcher/agent boundary: helpers never touch `mcp_dedup.sqlite`; the Agent's tool-call view lives in `workflow.sqlite`. Informs whether an Agent-side second layer for lost/recreated detection is possible without violating the boundary. | `scripts/shared/mcp_dedup.py` (REQ-003) |
| `scripts/shared/execution_snapshot.py` | The replay-equality decision reads `user_version` and `eventbus_db_path` and carries `config_hash`; these inputs change with adrrev005/adrrev006 and bound what the store's fail-closed rule can assume. | `scripts/shared/mcp_dedup.py` (REQ-001) |
| `scripts/shared/mcp_dedup.py` (as reference for `retry_class()`, `open_dedup_store`, `purge_expired`) | Read to preserve the retry-class default (unknown = non-retryable) and retention semantics while isolating config. | `config/mcp_dedup.toml` (REQ-004) |
| `config/agent.toml` (existing keys) | Read to place `pending_timeout_minutes` consistently with existing Agent config. | `config/agent.toml` (REQ-004) |
| `config/*_mcp_server.toml` (10 files) | Each MCP server's own config; read to confirm none currently carries dedup config and to place dispatcher settings if a per-server copy is adopted. | `config/mcp_dedup.toml` (REQ-004) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (ADR-004) | The single authority for how a fail-open must be registered; read to model the exception entries and approval shape. | `docs/10_adr/adr_02_01_004...` (REQ-006) |

## Acceptance Criteria
- Deleting or recreating `mcp_dedup.sqlite` causes the next non-retryable call to be rejected and not execute the side effect until an operator resolves the state; a never-seen key on a genuinely fresh store still executes once. (REQ-001)
- A retryable tool whose store is unavailable proceeds overlay-only with `store_error`; a failed write after a successful open is fail closed for non-retryable tools and warning-only for retryable ones; both are registered as approved ADR-004 exceptions. (REQ-002)
- The lost/recreated detection lives out-of-band (outside the DB file). (REQ-003)
- No process imports `config/mcp_dedup.toml`; unknown tools stay non-retryable after moving the classification. (REQ-004)
- ADR-008, `db_03_07`, and `db_08` classify the store identically as a disposable cache; the store appears in the Recovery Policy Matrix, `db_08`, and the dependency graph; `db_03_07` has no "system of record" wording or stale citation. (REQ-005)
- Every ADR-004 exception has a maintainer-written approval record (not fabricated here). (REQ-006)
- `check_db_separation.py`, `check_docs_consistency.py --domain db`, `check_adr_authority.py`, `check_adr_structure.py`, and `check_adr_preservation.py` pass. (REQ-005, REQ-006)

## Tests
- `tests/shared/test_mcp_dedup.py`: store created on a missing file succeeds (regression guard for the constructor); out-of-band flag set after deletion recreates the store as "lost"; non-retryable rejection path; `retry_class` defaults unknown tools to non-retryable after config move. (REQ-001, REQ-003, REQ-004)
- `tests/mcp_servers/test_mcp_dispatch.py`: non-retryable tool rejected (`dedup_store_error` / new type, `calls == 0`) against an empty/fresh store; retryable tool proceeds overlay-only (`store_error`, `calls == 1`); post-open write failure fails closed for non-retryable and warning-only for retryable; first-ever key on a fresh store executes once. (REQ-001, REQ-002)
- `tests/agent/test_tool_runner.py`: `retry_class` resolved from the Agent's own stored state, not the dispatcher config; unknown tool stays non-retryable. (REQ-004)
- Impact-radius check (`rules/toolchain.md`) for the config loader and dispatcher symbols; full validation sequence if code changes. (all)

## Documentation Impact
Fully spans ADR-008, ADR-004, and the database docs. ADR-008 (classification, ownership, backup, recovery), ADR-004 (exception registry), `db_01`, `db_03_07`, `db_08`, and the dependency graph change. State intent, ownership, and failure behavior without copying configuration values. Name targets via `docs/00_index.md` "Document References by Task": the ADRs live under the failure-handling / database domains; the db docs under the db domain. ADR amendments require a maintainer approval record written by a maintainer (see Risks); this Plan fabricates none.

## Assumptions
- The maintainer's 2026-11-09 decision stands: Option B (disposable cache), the retryable fail-open as an approved ADR-004 exception, and fail-closed handling of a post-open write failure for non-retryable tools.
- The dispatcher is the sole remaining reader of `mcp_dedup.toml` after `pending_timeout_minutes` moves to `agent.toml` and `tool_runner.py` stops importing the dispatcher config, so the file is reduced rather than deleted.
- The out-of-band detection can be expressed without the dispatcher importing the Agent's `workflow.sqlite` (the boundary forbids it), so a sentinel outside both databases is preferred.
- Moving `pending_timeout_minutes` to `agent.toml` follows the existing Agent config shape.
- The never-seen key on a genuinely fresh store must still execute; only re-execution of a lost completed non-retryable call is blocked.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact "lost or recreated" detection mechanism: out-of-band sentinel (file/flag outside the DB) versus an Agent-side second layer in `workflow.sqlite` `tool_call_state` rows. | None yet — design decision. | Resolve in Design; prefer the out-of-band sentinel to respect the dispatcher/agent boundary. | False |
| UNK-02 | Whether `workflow.sqlite` `tool_call_state` rows can serve as the second layer for the same decision (the issue's `Needs confirmation`). | Read `tool_call_state_ops.py` + `workflow_engine.py` replay path at implementation. | Confirm in Design; if it violates the boundary, reject in favor of the sentinel. | False |
| UNK-03 | Whether `tool_runner.py` actually consumes `retry_class()` against the dispatcher config or only holds the import. | Read `tool_runner.py` usage at implementation. | If it reads the config, refactor to the stored value (target row already lists it). | False |
| UNK-04 | Exact current wording of ADR-008 matrix rows, `db_03_07` L99/L100/L148, and ADR-004 exception shape at implementation time. | Read once at implementation; the plan cites the verified current state. | Read in `plan-to-implementation-procedure` Step 2. | False |
| UNK-05 | Whether reducing `mcp_dedup.toml` to a single owner leaves any other reader (e.g. a startup script) unaccounted for. | Search all `*.py`/`*.sh` for `mcp_dedup.toml` / `resolve_config_dir` consumers. | `grep` at implementation; if a hidden reader exists, keep the key or add it to the isolation scope. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Modify | High (shared dedup core; dispatcher + Agent depend on it) | 8 | Shared (dedup author) | not applicable (rsynced) |
| `scripts/mcp_servers/dispatch.py` | Modify | High (every MCP server process routes through it) | 12 | Shared (dispatcher author) | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Medium (Agent replay path) | 15 | Shared (workflow author) | not applicable (rsynced) |
| `scripts/agent/tool_runner.py` | Modify | Medium (per-tool dispatch helper) | 6 | Shared | not applicable (rsynced) |
| `config/agent.toml` | Modify | Low (one new key) | 4 | Shared | rsynced (apply when a `config/*.toml` is added) |
| `config/mcp_dedup.toml` | Modify | Low (one removed key) | 2 | Shared | rsynced (apply when a `config/*.toml` changes) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium (ADR read by index and authority checks) | 3 | Shared (governance author) | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium (authority read broadly) | 7 | Shared (governance author) | not applicable (rsynced) |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Modify | Low | 3 | Shared | not applicable (rsynced) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Medium (high churn db doc) | 18 | Shared | not applicable (rsynced) |
| `docs/41_db/db_08_active_databases.md` | Modify | Low | 4 | Shared | not applicable (rsynced) |

## Design
Path B classification is driven by three independent signals, not by file count alone: (1) more than three modification targets across source, config, tests, and docs; (2) a behavioral change to a safety input (non-retryable tools must not silently re-execute); (3) shared-config isolation across two process kinds (dispatcher + Agent) contrary to ADR-002.

- **Architecture.** The dedup store sits behind the ADR-008 dispatcher/agent boundary: `tool_call_state_ops.py` never touches `mcp_dedup.sqlite`, and the Agent's tool-call view lives in `workflow.sqlite`. Any detection mechanism must respect this boundary — the dispatcher cannot read the Agent's `workflow.sqlite`, and the Agent cannot write the dispatcher's store. This rules out a pure Agent-side second layer unless the boundary is explicitly re-decided.
- **The lost-or-recreated detection (UNK-01, primary design choice).** Because the guarantee must survive loss of the DB file, the marker cannot live inside that file. Primary approach: an out-of-band sentinel (a small flag file or operator-controlled initialization marker outside both databases). On first creation after a loss the sentinel is absent -> fail closed for non-retryable tools until the operator creates/resolves it; a genuine first-ever run also finds no sentinel, so the design must distinguish "never seen" from "lost" only by making the sentinel operator-acknowledged (the operator resolves the post-recreation state, which sets the flag). Secondary approach (rejected pending UNK-02): using `workflow.sqlite` `tool_call_state` rows as a second layer — read at implementation, but likely boundary-violating.
- **Config isolation (UNK-03, UNK-05).** `pending_timeout_minutes` is consumed only by the Agent (`workflow_engine.py:167`) -> `agent.toml`. `retry_class` is the cross-boundary case: the dispatcher classifies dispatch-capable MCP tools, and the Agent stores the resulting value in `workflow.sqlite` for replay; the coupling is `tool_runner.py:24` importing the dispatcher's `retry_class()`. Resolution: the classification belongs to the dispatcher layer; the Agent should read the stored value, not import the dispatcher config. Verify at implementation (UNK-03); if `tool_runner.py` does not actually consume the config, leave it and reduce `mcp_dedup.toml` to the dispatcher's single-owner config.
- **Historical.** `db_03_07` has high 30-day churn (18 commits); re-read it at implementation to avoid stepping on concurrent doc edits. `dispatch.py` (12) and `workflow_engine.py` (15) are moderately active; re-read both before editing.
- **Operational.** N/A — no ports, sockets, or database locks are touched beyond the existing WAL store.
- **Persisted schema.** N/A — no SQLite DDL or migration. The store is WAL-mode; deleting the file while a server runs leaves the process writing to an unlinked file until restart (confirm at implementation), which is exactly why the sentinel must be out-of-band.

The one design choice left open after the detection mechanism is the exact sentinel shape and operator-resolution command; resolve it by reading the recovery procedure in `agent_10_01` (referenced by adrrev009) and keeping the resolution step minimal and explicit.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Detect lost/recreated store and fail closed for non-retryable tools**
   - [ ] Add out-of-band "lost or recreated" detection to `scripts/shared/mcp_dedup.py` and expose an operator-resolution step (REQ-001, REQ-003).
   - [ ] In `scripts/mcp_servers/dispatch.py`, reject non-retryable tools when the store is missing/freshly recreated and route the operator-resolution step; keep retryable overlay-only `store_error` (REQ-001, REQ-002).
2. **Phase 2: Fail-closed the post-open write-failure path**
   - [ ] Make `_store_op` failures fail closed for non-retryable tools and warning-only for retryable tools in `scripts/shared/mcp_dedup.py` / `dispatch.py` (REQ-002).
3. **Phase 3: Isolate configuration per process**
   - [ ] Add `pending_timeout_minutes` to `config/agent.toml` and read it in `scripts/agent/workflow/workflow_engine.py` instead of `load_dedup_config()` (REQ-004).
   - [ ] Reduce `config/mcp_dedup.toml` to the dispatcher's single-owner config (remove `pending_timeout_minutes`); verify no hidden reader remains (REQ-004).
   - [ ] Refactor `scripts/agent/tool_runner.py` to stop importing the dispatcher's dedup config for `retry_class`; keep unknown tools non-retryable (REQ-004).
4. **Phase 4: Tests**
   - [ ] Add/modify `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/agent/test_tool_runner.py` for loss/recreation, per-process config, and refusal behavior (REQ-001..REQ-004).
5. **Phase 5: Documentation alignment**
   - [ ] Classify the store as a disposable cache and add the Recovery Policy Matrix row in `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (REQ-005).
   - [ ] Register the two exceptions with rationale and the maintainer approval record in `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (REQ-006).
   - [ ] Add the store to `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` and `docs/41_db/db_08_active_databases.md`; rewrite `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` consistently (REQ-005).
6. **Phase 6: Deployment & Verification**
   - [ ] Run `check_db_separation.py`, `check_docs_consistency.py --domain db`, `check_adr_authority.py`, `check_adr_structure.py`, `check_adr_preservation.py`, `check_docs_japanese.py`, and the EventBus/db test suites; confirm no invariant or Known Deviation regressed (all REQs).

### Release units
**Unit**: Empty-store fail-closed | **Phases**: 1, 2 | **Reason**: the detection mechanism (Phase 1) must land before the rejection path (Phase 1/2) can be validated alone; the config isolation (Phase 3) is independent and can be validated on its own.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Unit: lost/recreated detection, `_store_op` fail-closed, unknown-tool default | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Non-retryable rejected on empty store; retryable overlay-only; unknown = non-retryable |
| `scripts/mcp_servers/dispatch.py` | Integration: dispatch_tool control flow against empty/fresh store | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -v` | Non-retryable `calls == 0`; retryable `calls == 1` + `store_error`; first-ever key executes once |
| `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/tool_runner.py` | Unit: config isolation | `uv run pytest tests/agent/test_tool_runner.py -v` | `pending_timeout` from `agent.toml`; `retry_class` from stored state |
| `config/agent.toml`, `config/mcp_dedup.toml` | Config consistency | `uv run python tools/check_*.py` (config checkers in `rules/toolchain.md`) | No shared-file finding; loader still resolves |
| ADR-008, `db_01`, `db_03_07`, `db_08` | Structural + cross-domain consistency | `uv run python tools/check_db_separation.py`, `check_docs_consistency.py --domain db` | Pass; store classified identically as disposable cache |
| ADR-004 | Structural + preservation + authority | `uv run python tools/check_adr_structure.py`, `check_adr_preservation.py`, `check_adr_authority.py` | No invariant/reference/Known Deviation changed outside intent; exceptions registered; approval record present |
| All edited docs | Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Risks
- **Risk**: The empty-store fix blocks a legitimate first-time call on a genuinely fresh store (never-seen key must still execute). → **Mitigation**: the sentinel is operator-acknowledged, not merely "absent"; a brand-new store without prior pending state executes once, and only a store that lost a pending/non-retryable entry fails closed. Assert both in `test_mcp_dispatch.py`.
- **Risk**: ADR content edits trip `check_adr_preservation.py` (ERROR when an invariant, reference, test citation, Known Deviations, or Approval text changed) because the tool measures any body change. → **Mitigation**: scope each ADR edit to the exception/clause under change, keep all other text byte-identical, and re-run `check_adr_preservation.py` against `HEAD` before committing; treat a finding as scope creep to remove.
- **Risk**: ADR amendments require a maintainer approval record. → **Mitigation**: the implementation writes the approval record; this Plan records the requirement and fabricates none.
- **Risk**: Config isolation breaks the dispatcher or Agent if a hidden reader of `mcp_dedup.toml` exists. → **Mitigation**: `grep` all consumers before deleting the key (UNK-05); run the config loader checker and the full test suite before commit.
- **Risk**: `retry_class` cross-boundary ownership (read by dispatcher + Agent) is an open design decision. → **Mitigation**: classify it as a dispatcher-layer concern; the Agent reads the stored value; resolve UNK-03 at implementation; do not default any tool to a weaker class.
- **Risk**: `db_03_07` high churn (18 commits/30d) risks stepping on concurrent doc edits. → **Mitigation**: re-read the file at implementation and re-run the doc checkers.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Detect lost/recreated store and fail closed for non-retryable tools | Completed | 20261111-111905 | 20261111-170713 | UNK-01 resolved: out-of-band sentinel fail-closed in `scripts/shared/mcp_dedup.py` + `scripts/mcp_servers/dispatch.py`; first-ever key still executes. `test_mcp_dispatch.py` empty-store case green. |
| 2 | Fail-closed the post-open write-failure path | Completed | 20261111-111905 | 20261111-170713 | Retryable fail-open + post-open write-failure registered as ADR-004 exceptions (`adr_02_01_004`); ADR-008 matrix extended with the dispatcher-owned store. |
| 3 | Isolate configuration per process | Completed | 20261111-111905 | 20261111-170713 | `pending_timeout_minutes` moved to `config/agent.toml`; `config/mcp_dedup.toml` reduced to dispatcher single-owner config; `tool_runner.py` no longer imports dispatcher config. No hidden reader remains. |
| 4 | Tests | Completed | 20261111-111905 | 20261111-170713 | Full suite 12068 passed, 11 skipped, no regressions; targeted suites green. |
| 5 | Documentation alignment | Completed | 20261111-111905 | 20261111-170713 | `db_01`, `db_08`, `db_03_07` corrected; ADR-008 classification recorded. Blocks adrrev009 (adrrev009 depends on `plans/done/adrrev008`). |
| 6 | Deployment & Verification | Completed | 20261111-111905 | 20261111-170713 | All validation gates Pass (fast mode, base master); `stale_detector.py` clean on every edited procedure doc. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-230633
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/tool_runner.py`, `config/agent.toml`, `config/mcp_dedup.toml`, `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/agent/test_tool_runner.py`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_08_active_databases.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (empty-store gap); Adversarial Verification Claim 1; Required Changes (fail-closed on loss/recreation) | `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py` | 1 | Non-retryable rejected on empty/fresh store; first-ever key executes | `test_mcp_dispatch.py` empty-store case | Confirmed by repository evidence |
| REQ-002 | Problem (third degradation path); Required Changes (ADR-004 exception for retryable fail-open + fail-closed write failure) | `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `docs/10_adr/adr_02_01_004...` | 2 | Retryable overlay-only under approved exception; write failure fail-closed for non-retryable | `test_mcp_dispatch.py` post-open write failure | Confirmed by repository evidence |
| REQ-003 | Unresolved Questions (lost-or-recreated detection must be out-of-band) | `scripts/shared/mcp_dedup.py` | 1 | Detection stored outside the DB file | `test_mcp_dedup.py` out-of-band flag | Confirmed by repository evidence |
| REQ-004 | Problem (shared config); Required Changes (per-process config); Constraints (ADR-002) | `config/agent.toml`, `config/mcp_dedup.toml`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/tool_runner.py` | 3 | No process reads `mcp_dedup.toml`; unknown tools stay non-retryable | `test_tool_runner.py` config isolation | Confirmed by repository evidence |
| REQ-005 | Problem (doc gaps); Required Changes (ADR-008 matrix, db_01/db_08, db_03_07 wording); Acceptance Criteria | `docs/10_adr/adr_02_05_008...`, `docs/41_db/db_01...`, `docs/41_db/db_03_07...`, `docs/41_db/db_08...` | 5 | Store classified identically as disposable cache; appears in matrix/db_08/graph | `check_db_separation.py`, `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-006 | Problem (unregistered fail-opens); Required Changes (ADR-004 exception registry); Acceptance Criteria | `docs/10_adr/adr_02_01_004...` | 5 | Exceptions registered with rationale + maintainer approval record | `check_adr_authority.py`, `check_adr_structure.py`, `check_adr_preservation.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261111-111905 -->
