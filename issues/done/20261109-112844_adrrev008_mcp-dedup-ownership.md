# Classify mcp_dedup.sqlite as a disposable cache, make its loss fail closed for non-retryable tools, and isolate its configuration

## Priority
High

## Summary
Classify `mcp_dedup.sqlite` as a disposable cache (maintainer decision of 2026-11-09, Option B), record it in ADR-008, make loss or recreation of the store unable to cause a silent repeat of a non-retryable side effect (non-retryable tools are rejected until an operator resolves the state), decide the treatment of the remaining degradation paths, and stop sharing one configuration file between several processes.

## Background
- Source: `memo-issue.md` item H-10, re-checked against current source on 2026-11-09.
- `Explicit in code`: `config/mcp_dedup.toml` holds the store path, retention, the pending timeout, and the per-tool retry classification; its loader lives in `scripts/shared/mcp_dedup.py` (`resolve_config_dir() / "mcp_dedup.toml"`), and the shared dispatcher `scripts/mcp_servers/dispatch.py` uses it. `scripts/agent/tool_runner.py` and `scripts/agent/workflow/` also reference the dedup store. `Explicit in code`: `load_dedup_config()` is called by `scripts/mcp_servers/dispatch.py` (every MCP server process that uses the shared dispatcher) and by `scripts/agent/workflow/workflow_engine.py` (the Agent, for the pending timeout), and `scripts/agent/tool_runner.py` uses `retry_class`. At least two process kinds therefore read the same file.
- `Explicit in code` (`scripts/mcp_servers/dispatch.py`, `dispatch_tool`; test `tests/mcp_servers/test_mcp_dispatch.py::test_init_failure_fail_closed_and_degrade` and `::test_store_error_retryable_proceeds_non_retryable_fails_closed`): when the store cannot be initialized or a lookup fails, non-retryable tools are refused (`dedup_store_error`) and retryable tools proceed overlay-only with a `store_error` marker. The only fail-open is therefore for retryable tools; the memo's first description is accurate and my earlier summary of an all-tool disable was wrong. A failed store write after a successful open (`_store_op`) only logs a warning and continues for every tool (`Explicit in code`), which is a third, quieter degradation path.
- `Explicit in documentation`: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` describes `mcp_dedup.sqlite` as a standalone durable store owned by the shared dispatcher. `Needs confirmation` against the memo's further claims: it calls the store a fifth database and a system of record while its recovery text says "recreate; an empty store simply lets the next call execute". A search of ADR-008 (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`), `db_01`, and `db_08_active_databases.md` found no mention of `mcp_dedup` (`Documentation only`).
- `Explicit in config`: `config/mcp_dedup.toml` states that unknown tools default to non-retryable.
- `Needs confirmation`: whether the fail-open is registered as an ADR-004 exception.
- Related archived: `toolexec001` issue and plan under `issues/done/` and `plans/done/` (origin of the store), `wfaudit002_tool-state-key-collisions`, `idemaudit001`, `inflightcancel001`.

## Problem
- If the store is lost or recreated while a non-retryable call is pending, the pending and completed state disappears, and the next identical call may execute again (`Needs confirmation`: the dispatcher's behavior against an empty or fresh store). That breaks the guarantee that a non-retryable tool is not silently re-executed, exactly when recovery is performed.
- The store is absent from the ADR-008 Recovery Policy Matrix and the active-database inventory, although ADR-008 requires the matrix to be extended before a new system-of-record store is deployed (`Documentation only`).
- One configuration file shared by several processes couples their lifecycles, contrary to ADR-002 (each process reads only its own configuration).
- The retryable fail-open needs an approved ADR-004 exception or a fail-closed change.

## Reason for Change
- The classification determines whether operators must back up the store and how recovery works; without a decision the recovery procedure is ambiguous.
- Timing: depends on the single schema-validation mechanism, and the ADR-008 alignment issue in this batch records the outcome.

## Implementation Intent
- The store is a disposable cache: it is not backed up and recovery is recreation. The non-retryable guarantee still holds in every case, including loss or recreation of the database, by rejecting non-retryable tools until an operator explicitly resolves the state. Ownership and recovery are defined in ADR-008, and each process reads only its own configuration.
- The mechanism that tells "first-ever creation" from "lost or recreated" apart is a design decision for the plan (see Unresolved Questions); it must not live only inside the database file that can be lost.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `scripts/agent/tool_runner.py`, `scripts/agent/workflow/tool_call_state_ops.py`
- `config/mcp_dedup.toml` and each `config/*_mcp_server.toml`, `config/agent.toml`
- Tests: `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/agent/test_tool_runner.py`
- Docs: ADR-008, ADR-004 (exception registry), `docs/41_db/db_01_*.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_08_active_databases.md`, dependency graphs

## Required Changes
- Record in ADR-008 that `mcp_dedup.sqlite` is a disposable cache (decided by the maintainer; the approval record is written by a maintainer):
  - Classification: derived/disposable store with the owner (the shared MCP dispatcher layer), recovery by recreation, no backup requirement, and a Recovery Policy Matrix row stating the post-recreation rule for non-retryable tools.
  - Behavior: when the store is missing or recreated, non-retryable tools are rejected (fail-closed) until an operator resolves them; define the operator procedure and how the rejection is reported (`dedup_store_error` or a new error type).
- Implement the rule above in `dispatch.py` and the store (detection of a missing or recreated store, rejection of non-retryable tools, operator resolution step), and add tests for it.
- Treat the two remaining degradation paths as decided by the maintainer on 2026-11-09 (recommendation adopted): (1) retryable tools proceeding overlay-only with a `store_error` marker when the store is unavailable is registered as an approved ADR-004 exception with a written rationale (retryable tools are safe to repeat, and the behavior stays audited through `dedup_state`); (2) a failed write after a successful open is made fail closed for non-retryable tools (the call is rejected instead of continuing with a warning), while retryable tools keep the warning-only behavior under the same exception. Add tests for both, and record the exception in ADR-004 (approval record written by a maintainer).
- Move the dedup settings each process needs into that process's own configuration (each server's `*_mcp_server.toml`, and a separate timeout key in `agent.toml`), and delete `config/mcp_dedup.toml` (or reduce it to one owner process if the plan shows a single reader).
- Add the database to `db_01`, `db_08`, and the dependency graph, and make `db_03_07` consistently describe a disposable cache (remove the "system of record" wording and the stale reference to the archived toolstate001 issue path).
- Coordinate with the schema-validation and Agent-side EventBus coupling issues in this batch, which change the `user_version` and `eventbus_db_path` inputs of the execution snapshot used for replay equality.

## Constraints
- ADR-002: each process reads only its own configuration file; ADR-004: every fail-open is an approved exception.
- The retry-class classification is a safety input; moving it must not default any tool to a weaker class (unknown tools stay non-retryable).
- `deploy/deploy.sh` and `rules/env.md` Architecture apply when a `config/*.toml` file is removed or added.
- Schema validation follows the single mechanism from the schema-validation issue in this batch.

## Acceptance Criteria
- Test: delete or recreate the database; the next non-retryable call is rejected and does not execute the side effect until an operator resolves the state; a retryable call behaves as recorded in ADR-004.
- No configuration file is read by more than one process.
- `db_03_07` and ADR-008 classify the store the same way (disposable cache), and the store appears in the Recovery Policy Matrix and `db_08` with its recreation rule.
- The retryable fail-open is listed as an approved ADR-004 exception with its rationale, and a failed write for a non-retryable tool is rejected (test proves it).
- `check_db_separation.py`, `check_docs_consistency.py --domain db`, `check_adr_authority.py`, and `check_adr_structure.py` pass.

## Testing Expectations
- New and updated tests in `tests/shared/`, `tests/mcp_servers/`, and `tests/agent/` for loss and recreation of the store, the per-process configuration, and the refusal behavior.
- Impact-radius check (`rules/toolchain.md`) for the config loader and dispatcher symbols; full validation sequence; documentation checkers listed above.

## Documentation Impact
- ADR-008 (classification, ownership, backup, recovery), ADR-004 (exception), `db_01`, `db_03_07`, `db_08`, and the dependency graph change. State intent, ownership, and failure behavior without copying configuration values.

## Out of Scope
- Fingerprint validation implementation (schema-validation issue in this batch).
- The manual recovery procedure rewrite (ADR-008 alignment issue in this batch).
- Changing which tools are classified retryable or non-retryable, unless the plan proves a misclassification.

## Dependencies
- Depends on: `issues/20261109-112715_adrrev005_schema-fingerprint-unify.md` (fingerprint validation of the store).
- Blocks: `issues/20261109-112922_adrrev009_adr008-recovery-align.md` (ADR-008 alignment), which records the matrix outcome.
- Related, recently archived: `wfaudit002_tool-state-key-collisions`, `idemaudit001_audit-idempotency-key-mismatch` under `issues/done/`.

## Unresolved Questions
- Decided by the maintainer on 2026-11-09: Option B (disposable cache), the retryable fail-open as an approved ADR-004 exception, and fail-closed handling of a post-open write failure for non-retryable tools.
- Design question for the plan: how to detect "lost or recreated" without relying on the lost file (for example an operator-controlled initialization marker outside the database, or a persisted epoch kept elsewhere). `Needs confirmation`: whether the Agent-side `tool_call_state` rows in workflow.sqlite can serve as the second layer for the same decision.
- `Needs confirmation`: what the dispatcher does against a missing or recreated store for a non-retryable tool with a prior pending entry. `Strongly implied by code`: `open_dedup_store` creates a new store and `lookup` then finds no row, so the call executes again; confirm by test.
- `Documentation only`: ADR-004 mentions no dedup-store exception (a search for "dedup" in ADR-004 found nothing), so the retryable fail-open and the write-failure degradation appear unregistered. `mcp_03_03` documents both behaviors in prose.
- `Explicit in code`: the dedup key is content-derived, `sha256(method, tool_name, canonical args, session uid)` (`derive_idempotency_key` in `scripts/shared/http_transport.py`), so the same content in the same session re-derives the same key across retries and restarts. Dedup applies only to side-effecting tools (`_write_tools`) and only when a key is sent. A completed row is served only when the stored execution snapshot equals the current one; the snapshot includes a hash of the whole `config/*.toml` tree, the deployed revision, and each database file's `user_version` (`scripts/shared/execution_snapshot.py`). Any config or revision change therefore forces a fresh attempt by design (`snapshot_mismatch`). Terminal rows are purged after the configured retention; pending rows are never purged. So the guarantee is bounded by retention, snapshot equality, and session scope, not absolute.
- `Explicit in code`: `DedupStore` bootstraps with `CREATE TABLE IF NOT EXISTS` and stamps `PRAGMA user_version`; it does no shape validation. The execution snapshot reads `user_version` and `eventbus_db_path`, so the schema-validation issue and the Agent-side EventBus coupling issue in this batch change inputs of the replay-equality decision and must be coordinated with this one.
- `Explicit in documentation`: `db_03_07` calls the store "a separate system of record" in one place and "a replay cache ... a fresh empty store only means the next call of each key runs for real" in another, and itself notes that `db_08_active_databases.md` does not list the store; it also still cites the now-archived `issues/20261031-175803_toolstate001_tool-call-state-producer.md`.
- `Strongly implied by code`: `DedupStore` holds one open connection per process; deleting the file while a server runs leaves the process writing to an unlinked file until restart, and a recreated file yields an empty store for new processes (confirm by test).

## Adversarial Verification Results

Verified against current source on 2026-11-10 (HEAD `dab0fdf30`). Each claim checked once
against live files; evidence cites file, line, and behavior.

### Claim 1 — store loss/recreation lets a non-retryable tool re-execute (Needs confirmation #81)

Status: **CONFIRMED by control-flow trace.**

- `DedupStore.__init__` (`mcp_dedup.py` L232-246) runs `CREATE TABLE IF NOT EXISTS` and stamps
  `PRAGMA user_version`; it succeeds on a missing or recreated file and returns a handle to a
  fresh, empty store.
- `_dedup_context()` (`dispatch.py` L175-194) therefore returns a non-None store even when the DB
  was just recreated; it only fails open (sets `_dedup_disabled=True`, returns `(None, None)`)
  when `open_dedup_store` raises.
- In `dispatch_tool`, an empty store makes `store.lookup(key)` return None, so `row is None`
  and the code takes the `else` branch (L405-412): `record_pending`, then `await handler(a)`
  (L431). There is no "is this store freshly created?" check, so the tool executes.
- Fail-closed (`dedup_store_error`) fires only on (a) init failure -> the `(None, None)` path
  (L413-428) or (b) `lookup` raising `sqlite3.Error`/`OSError` (L309-323). An empty-but-open
  store hits neither.
- Conclusion: a non-retryable tool re-executes after the store is lost or recreated. The
  guarantee breaks exactly during recovery. The issue's "strongly implied by code" note is
  correct and is now confirmed by reading the actual control flow.

### Claim 2 — current fail-open behavior (explicit in code)

Status: **CONFIRMED.**

- Init/lookup failure: retryable tools proceed overlay-only with `store_error`; non-retryable
  tools fail closed with `dedup_store_error`. Verified by
  `test_store_error_retryable_proceeds_non_retryable_fails_closed` (L521) and
  `test_init_failure_fail_closed_and_degrade` (L555), both asserting the described outcomes
  (`dedup_state == "store_error"` + `calls == 1` for retryable; `error_type ==
  "dedup_store_error"` + `calls == 0` for non-retryable).
- `_dedup_context()` fails open by design (L186 comment).
- `_store_op` (L209-216): a failed write after a successful open logs a warning and returns
  `False`; the caller ignores the return and continues. This is the third, quieter path. For a
  non-retryable tool against an empty store, if `record_pending` itself fails the tool still
  executes (warning only) -> the "post-open write failure" gap the issue wants made fail-closed
  for non-retryable tools.

### Claim 3 — one config file shared by several processes

Status: **CONFIRMED.** `load_dedup_config()` resolves `resolve_config_dir() / "mcp_dedup.toml"`
(`mcp_dedup.py` L80) and is called by `scripts/mcp_servers/dispatch.py:183` (every MCP server
process using the shared dispatcher) and `scripts/agent/workflow/workflow_engine.py:167` (the
Agent pending timeout); `tool_runner.py` reads `retry_class`. Multiple process kinds read one
file, coupling their lifecycles contrary to ADR-002.

### Claim 4 — dedup key and snapshot replay inputs

Status: **CONFIRMED.** `derive_idempotency_key` is
`sha256(method \n tool_name \n canonical-JSON(args) \n uid)` (`http_transport.py:62`). The
execution snapshot (`execution_snapshot.py`) carries `config_hash` (SHA-256 over the
`config/*.toml` tree), the deployed revision, and each DB's `user_version` header, and reads
`user_version` and `eventbus_db_path`. So the schema-validation and EventBus-coupling issues in
this batch change the replay-equality decision's inputs, as the issue states.

### Claim 5 — retention / purge

Status: **CONFIRMED.** `purge_expired` (`mcp_dedup.py` L351-376) deletes only terminal rows
older than retention; pending rows are never purged. The guarantee is bounded by retention,
snapshot equality, and session scope, not absolute.

### Claim 6 — db_03_07 wording

Status: **CONFIRMED internal inconsistency.** `db_03_07` L99 calls the store "a separate system
of record" and cites the archived `toolstate001` issue; L148 calls it a "replay cache" whose
"fresh empty store only means the next call of each key runs for real"; L150 notes `db_08` does
not yet list the store. "System of record" vs "replay cache" contradict each other.

### Claim 7 — ADR-008 matrix / db_08 / ADR-004 registration

Status: **CONFIRMED absence.**
- ADR-008 has a Recovery Policy Matrix (L86) and L138 requires extending it before deploying a
  system-of-record store, but `mcp_dedup` appears nowhere in ADR-008 -> not in the matrix.
- `db_08_active_databases.md` does not list `mcp_dedup`.
- ADR-004 contains no `dedup` mention -> the retryable fail-open and the post-open write-failure
  degradation are unregistered fail-opens.

### Overall

- The central problem is REAL and reproduced by code reading (and reproducible by test): the
  fail-closed guarantee holds for the two failure modes (init failure, lookup raises) but NOT
  for the empty-store mode, which is precisely the recovery scenario for a disposable cache.
  Classifying the store as a disposable cache (Option B) makes the gap operational, so the
  fail-closed-on-empty-store fix is warranted.
- Every "explicit in code" and "documentation only" claim checks against source; no
  contradiction with the issue's characterizations was found.
- Adversarial note for the plan: any fix must not block a legitimate first-time call on a fresh
  store (never-seen key must still execute). It must only block re-execution of a completed
  non-retryable call that was lost. Distinguishing "first-ever" from "recreated after loss" is
  the unresolved design question and must be resolved out-of-band (not inside the lossable DB
  file), as the issue states.
- Correctly left to the plan: the "lost or recreated" detection mechanism; maintainer approvals
  for the ADR-004/ADR-008 amendments (do not fabricate approval records).

## AI Implementation Instruction
- The classification is decided (disposable cache); do not implement Option A (backup and restore of the store). Implement the decided ADR-004 treatment (exception for the retryable fail-open, fail closed for non-retryable write failures); do not widen the exception to non-retryable tools.
- Never weaken a retry classification; keep unknown tools non-retryable.
- Do not touch retryable/non-retryable tool assignments beyond moving them.
- Write documentation in English, follow the docs content policy, and do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112844
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `scripts/agent/tool_runner.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `config/mcp_dedup.toml`, `config/agent.toml`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_08_active_databases.md`
