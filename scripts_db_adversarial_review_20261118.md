# Adversarial Review — `scripts/db` (18 modules)

Reviewed head: `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9` (working tree matched HEAD, no uncommitted edits).

## Review Scope

- Reviewed (core recovery): `recovery.py`, `recovery_restore.py`, `recovery_verification.py`, `recovery_drill.py`.
- Reviewed (maintenance/retention): `maintenance.py`, `artifact_retention.py`, `rotation.py`.
- Reviewed (connection/config/models): `helper.py`, `config.py`, `models.py`, `store_protocols.py`, `store_impl.py`.
- Reviewed (schema/consistency): `create_schema.py`, `schema_sql.py`, `rag_consistency.py`, `rag_consistency_queries.py`, `session_consistency.py`.
- Reviewed (shared backbone): `scripts/shared/schema_fingerprint.py`.
- Not reviewed: non-Python assets, shell/TOML, tests (no test-run phase beyond the existing suite), other top-level modules outside `scripts/db` and `scripts/shared/schema_fingerprint`.

Working tree vs reviewed head: matched at `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | `scripts/db/` | All checks passed |
| `mypy --no-namespace-packages` | `scripts/db/` | Success: no issues found (18 files) |
| `bandit -ll` | `scripts/db/` | Clean (B608 calls carry targeted `nosec` justifications) |
| `tools.check_db_separation` | — | Clean |
| `tools.check_module_size` | `scripts/` | ALL OK — every module ≤ 24576 B |
| `tools.generate_reference_table --check` | — | Clean |
| `pytest tests/db/` | full db suite | 498 passed |

## Summary

- Overall assessment: **Clean.** No correctness, concurrency, resource-lifecycle, error-handling, configuration, or security defect survives adversarial scrutiny across the recovery, maintenance, consistency, and connection layers. The code is defensively structured: restore is fail-closed (a staged candidate never touches the live DB until physically and logically verified), purge is transactional (any error rolls back the whole operation), naming is collision-safe (`resolve_unique_path`), sidecar quarantine reassembles the whole original unit on rollback, schema shape is enforced fail-closed via fingerprinting, and read-only opens use a `mode=ro` URI with residue cleanup.
- Highest-risk area: **none requiring action.** The corruption-restore state machine (`_restore_from_backup` → `_activate_candidate` → `_post_restore_failure` → `_rollback_or_non_serviceable`) and the retention-purge transaction were scrutinized most heavily; both behave as documented across the failure scenarios exercised below.
- Recommended next step: **proceed.** No fix required. The items below are all Low/Informational; each is either documented-and-intentional, a deliberate fail-closed tradeoff, or pure style. None warrants a tracked issue.

## Adversarial scenarios exercised

| Scenario | Path examined | Outcome |
|---|---|---|
| Two recoveries in the same second | `recovery_restore.build_restore_paths` + `resolve_unique_path` | Collision-safe; second run gets a counter suffix. |
| Backup is itself corrupt | `_backup_is_usable` integrity gate | `bad_backup`; no restore. |
| Backup belongs to another domain | `_verify_domain_identity` | `backup_wrong_domain`; no restore. |
| Activation succeeds, post-restore logical check fails | `_post_restore_failure` → `_rollback_or_non_serviceable` | Archived original restored, quarantined sidecars reassembled (`preserved_original`). |
| OSError mid-stage before `os.replace` | `except OSError` handler, `progress.replaced == False` | Quarantined originals reassembled; live file untouched. |
| OSError after `os.replace` (sidecar move fails) | `except OSError` handler, `progress.replaced == True` | Moved sidecars unlinked, archived original restored. |
| Read-only probe of a WAL-mode DB creates `-wal`/`-shm` | `_connect_read_only` + `close()` residue cleanup | Only sidecars this open created are removed; hot/pre-existing left alone. |
| Concurrent purge | `begin_immediate()` transaction | Serializes writers; any error rolls back the whole purge. |
| Schema drift on restored copy | `assert_matches` fingerprint | Raises `RuntimeError` → caught as `verification_unavailable` / refused. |

## Findings

No Medium-or-higher finding survived adversarial scrutiny. The three items below are all Low/Informational; each is either a deliberate fail-closed tradeoff, a cheap-but-real inefficiency, or pure style. None warrants a tracked issue.

### F-001 — `_delete_sessions_beyond_limit` materializes every session rowid

- Title: O(N) memory in the count-based session-retention delete.
- Severity: Low
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/db/maintenance.py::_delete_sessions_beyond_limit` fetches `SELECT session_id FROM sessions ORDER BY created_at DESC, session_id DESC` into a full list, then slices `rows[max_sessions:]` to build the delete set.
- Current behavior: All session ids are loaded into memory before the bounded delete runs.
- Impact: For a very large `sessions` table this is O(N) memory on a periodic maintenance op. Correct and simple; a streaming `DELETE ... LIMIT -1 OFFSET ?` subquery would avoid the materialization. Scale is unknown (不明), so practical risk is unconfirmed.
- Recommended action: None required unless the sessions table grows large enough to make the in-memory list a measured concern.

### F-002 — `checkpoint_wal` reloads `agent.toml` on every call

- Title: Config reloaded per checkpoint invocation.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `scripts/db/maintenance.py::checkpoint_wal` calls `_load_agent_config()` (`ConfigLoader().load("agent.toml")`) on every invocation when `mode` is `None`.
- Current behavior: The checkpoint mode is re-read from disk each call rather than cached.
- Impact: Negligible cost (small TOML parse); no correctness issue. Only relevant if `checkpoint_wal` is called in a tight loop.
- Recommended action: None. Cache only if profiling shows config load is on a hot path.

### F-003 — `resolve_unique_path` raises instead of backing off under contention

- Title: Hard `RuntimeError` on pathological name-contention.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `scripts/db/config.py::resolve_unique_path` scans up to 10000 counter suffixes, then raises `RuntimeError` if none is free.
- Current behavior: Sustained same-second contention exhausts the search and raises rather than sleeping and retrying.
- Impact: Intentional fail-closed guard (avoids unbounded loops); a raise is the correct signal that generation is unconttainable. Documented tradeoff, not a defect.
- Recommended action: None.

## Open Questions

- Question: Does `_delete_sessions_by_age` correctly depend on `created_at` lexical sortability?
- Why it matters: The age rule compares `created_at < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-N days')` as a string. This is correct only while `created_at` stays in the canonical ISO8601 UTC format the schema `DEFAULT` writes. Legacy rows or any non-conforming timestamp would misclassify age silently.
- Required confirmation: Confirm that all `created_at` values are guaranteed canonical (no legacy/mixed-format inserts). If guaranteed, risk is low; if not, the comparison should normalize format first.

## Suggested Tests

- Test target: `recovery.py::_restore_from_backup` OSError-after-activation branch.
- Behavior to verify: When `_activate_candidate` raises after `os.replace` succeeded, the archived original is restored, the already-moved sidecars are unlinked, and the result reports `active_db_state == "preserved_original"`.
- Failure mode: A regression that forgets to unlink the moved sidecars would leave a candidate-owned `-wal`/`-shm` behind the reactivated original, violating the whole-unit reassembly invariant (REQ-002).

## Documentation Notes

- Target document: the `recover_corruption` docstring `action` value table (already complete and accurate).
- Required update: none. The action vocabulary (`restored`, `restore_verify_failed`, `logical_verify_failed`, `verification_unavailable`, `rollback_failed`, `preserved_original`, `non_serviceable`, ...) is exhaustive and matches the implementation.

## Final Recommendation

**Proceed.** No Medium-or-higher finding survives adversarial scrutiny. The toolchain is green (ruff, mypy clean over 18 files; bandit only `nosec`-justified B608; module sizes within baseline; `check_db_separation` and `generate_reference_table --check` clean; 498 db tests pass). The three Low/Informational items are optional polish or deliberate design tradeoffs; none is actionable enough to warrant a tracked issue. The single Open Question (F-001 `created_at` format dependency) is confirmable without code change and does not block.
