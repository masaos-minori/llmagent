## Goal

Prevent sensitive diagnostic fields (`artifacts` URIs, `rag_stage_outcomes`) from being
persisted unredacted in `session_diagnostics`, add an opt-in encryption layer for stored
diagnostic content, and automatically purge diagnostic records older than a configurable
retention period.

## Scope

**In-Scope:**
- Add `_filter_sensitive_fields()` to `DiagnosticStore`: redacts `artifacts` and
  `rag_stage_outcomes` from a diagnostic payload while preserving item counts.
- Add `_encrypt_content()` using Fernet symmetric encryption (from the already-vendored
  `cryptography` dependency), keyed from configuration.
- Extend `save()` with an `encrypt: bool = False` parameter that applies encryption when set.
- Add `_purge_old_diagnostics()` that deletes rows older than a configured retention period
  (default 30 days), invoked at the start of `save()`.

**Out-of-Scope:**
- Changing the signatures/behavior of the existing typed helper methods
  (`save_serialization_event`, `save_partial_completion`, `save_transport_failure`,
  `save_loop_guard_hint`) beyond however they route through `save()`.
- Encrypting conversation history or any non-diagnostic table.
- Schema changes beyond what retention purge requires (none — purge uses the existing
  `created_at` column).
- Wiring the new `encrypt=True` warning-log call in `repl.py` (tracked separately in
  `implementations/20260726-174737_repl.py.md`).

## Assumptions

1. Encryption is opt-in via a config flag/key (per plan Assumption 1) — `save()` defaults
   to `encrypt=False` so existing callers and existing unencrypted rows are unaffected.
2. Retention purge runs lazily inside `save()` rather than via a separate cron/scheduler
   (per plan Assumption 2); this matches the existing `sqlite_retention_max_age_days`
   pattern already used for session retention (`config/agent.toml:15`).
3. No encryption key/retention config currently exists for diagnostics — a new
   `DiagnosticsConfig` dataclass (or new fields on `ObservabilityConfig`,
   `scripts/agent/config_dataclasses.py:358`) must be introduced; this document assumes a
   new `[diagnostics]` TOML section with `encryption_key: str = ""` and
   `retention_days: int = 30`, consistent with existing nested-config access
   (`cfg.diagnostics.retention_days`).
4. `cryptography` is already a resolved dependency (present in `uv.lock`, not currently
   imported anywhere under `scripts/`), so `from cryptography.fernet import Fernet` adds
   no new third-party dependency.

## Design decisions

- Keep filtering and encryption as private helper methods on `DiagnosticStore` rather than
  a separate module, since both operate purely on the `content` string/dict already local
  to `save()` — matches the file's existing flat, single-class structure (147 lines total,
  confirmed via `wc -l`).
- Redact by replacing `artifacts` with `{"_redacted": True, "count": len(artifacts)}` and
  `rag_stage_outcomes` similarly, rather than deleting the keys outright, so downstream
  readers can distinguish "filtered" from "field never populated" (plan Assumption 3).
- Apply filtering unconditionally (not opt-in) since the plan scopes it as a default
  protection, while encryption stays opt-in (plan Assumption 1) — these are two
  independent knobs, not one combined flag.
- Purge inside `save()` (lazy, per plan Assumption 2) rather than adding a background task,
  to avoid introducing new lifecycle/scheduling surface into a currently synchronous,
  connection-per-call class.

## Alternatives considered

- Filtering at the call site (`repl.py::_persist_session_diagnostics`) instead of inside
  `DiagnosticStore.save()` — rejected: `save()` is the single choke point for all diagnostic
  writes (also used by `save_serialization_event` etc.), so filtering there protects every
  caller, not just the session-summary path.
- Encrypting the entire `session_diagnostics` row (including `kind`) — rejected: `kind` is
  used for `fetch_by_kind()` queries (`WHERE kind = ?`); encrypting it would break querying.
  Only `content` is encrypted.
- A dedicated cron/scheduled purge job — rejected per plan Assumption 2 (adds new
  infrastructure for a low-volume, non-time-critical cleanup task); lazy purge on `save()`
  is simpler and sufficient.

## Implementation

### Target file

`scripts/agent/diagnostic_store.py`

### Procedure

1. Add module-level import `from cryptography.fernet import Fernet` and
   `from datetime import datetime, timedelta, UTC` (or reuse existing `time`-based
   comparison via SQL, see Method below).
2. Add `_filter_sensitive_fields(self, content: str) -> str`: parse `content` with
   `orjson`/existing `dumps`/`json.loads` (module currently has no `json` import — check
   whether to reuse `shared.json_utils` symmetrically), redact `artifacts` and
   `rag_stage_outcomes` keys when present, re-serialize.
3. Add `_encrypt_content(self, content: str, key: str) -> str`: `Fernet(key).encrypt(...)`,
   return a `str` (decode from bytes); no-op / pass-through if `key` is empty.
4. Modify `save()` (current lines 26-42) to: call `_purge_old_diagnostics()` first, then
   `_filter_sensitive_fields(content)`, then conditionally `_encrypt_content(...)` when
   `encrypt=True` and a key is configured, before the existing `INSERT`.
5. Add `_purge_old_diagnostics(self) -> None`: `DELETE FROM session_diagnostics WHERE
   created_at < ?` using a cutoff computed from the configured retention days.
6. Run the standard validation sequence from `rules/toolchain.md` (ruff, mypy,
   lint-imports, ast-grep, bandit, targeted + full pytest) once implemented.

### Method

- Current `save()` (lines 26-42):
  ```python
  def save(
      self,
      session_id: int | None,
      kind: str,
      content: str,
      workflow_id: str | None = None,
      task_id: str | None = None,
  ) -> None:
      """Persist one diagnostic entry."""
      with SQLiteHelper("session").open(write_mode=True) as db:
          db.execute(
              "INSERT INTO session_diagnostics"
              " (session_id, kind, content, workflow_id, task_id)"
              " VALUES (?, ?, ?, ?, ?)",
              (session_id, kind, content, workflow_id, task_id),
          )
          db.commit()
  ```
  Add `encrypt: bool = False` parameter; before the `INSERT`, call
  `self._purge_old_diagnostics()`, then `content = self._filter_sensitive_fields(content)`,
  then `if encrypt: content = self._encrypt_content(content, key)`.
- `_filter_sensitive_fields` operates on the already-JSON-serialized `content` string (the
  callers, e.g. `repl.py:240`, pass `json.dumps(summary)`); it must parse-modify-reserialize
  rather than string-match, to correctly handle the `artifacts` list and
  `rag_stage_outcomes` list found in `repl.py:230-232`.
- `_purge_old_diagnostics` reuses the existing `SQLiteHelper("session").open(write_mode=True)`
  connection pattern already used in `save()` (line 35) — no new connection-handling code;
  `scripts/db/helper.py` is the pragma/connection reference cited in the plan, confirmed no
  diagnostics-specific handling exists there today (`grep -n "session_diagnostics"
  scripts/db/*.py` only matches `schema_sql.py`'s table definition).

### Details

- Confirmed via full read of `scripts/agent/diagnostic_store.py` (147 lines) that no
  filtering, encryption, or purge logic exists today — `save()` performs a direct,
  unmodified `INSERT` (lines 36-41), and no `Fernet`/`encrypt`/`retention`/`purge`/`redact`
  symbol appears anywhere in the file (`grep -n` returned no matches).
  This is a genuinely unimplemented feature, not a rename/relocation of existing logic.
- `session_diagnostics` schema (`scripts/db/schema_sql.py:123-131`) has columns
  `id, session_id, kind, content, workflow_id, task_id, created_at` — `created_at` defaults
  to `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`, an ISO-8601 UTC string directly comparable
  with a computed cutoff string, so `_purge_old_diagnostics` can use a plain string
  comparison in SQL without needing a schema change.
- `cryptography` is present in `uv.lock` (confirmed, e.g. `uv.lock:837` `name = "cryptography"`)
  but not currently imported by any file under `scripts/` (no existing precedent to follow
  for key-loading conventions in this codebase) — the config-key-loading approach is new
  and should follow the existing `AgentConfig` nested-dataclass pattern
  (`scripts/agent/config_dataclasses.py`) rather than an ad hoc env var.
- No existing `[diagnostics]` config section in `config/agent.toml` — confirmed via
  `grep -n "diagnostic" config/agent.toml` (no matches); a new config section/dataclass is
  required as part of this change (see Assumptions).

## Compatibility considerations

- Default `encrypt=False` and unconditional-but-additive filtering mean existing unencrypted
  rows remain readable; new rows have `artifacts`/`rag_stage_outcomes` redacted by default,
  which is a behavior change existing diagnostics consumers should expect (per plan's
  "Blast Radius" note) — flagged as a real, intended compatibility break for those two
  fields specifically, not a bug.
- Encrypted rows are unreadable without the configured key; `fetch()`/`fetch_by_kind()`/
  `fetch_all()` are out of scope for this document but will need a corresponding decrypt
  path before encrypted diagnostics are useful to any reader (tracked as a follow-on, not
  implemented here since the plan does not list a fetch-side change).
- No change to the `session_diagnostics` table schema — purge only deletes rows, no columns
  added or removed.

## Security considerations

- Redaction preserves counts, not raw values, per plan Assumption 3 — avoids leaking
  artifact URIs or RAG stage outcome contents into the diagnostics table by default.
- Fernet key must come from configuration, not be generated ad hoc per call (a fresh key
  per encryption would make stored data permanently undecryptable) — key lifecycle
  (rotation, loss) is flagged as a real risk in the source plan's Risks section and is not
  solved by this document beyond loading a configured key.
- `_purge_old_diagnostics` performs an unconditional `DELETE`; per the plan's Risks section,
  deletions should be logged (`logger.info` with row count) so retention-driven data loss is
  auditable.

## Rollback considerations

- Change is additive (new methods, new `save()` parameter with a safe default) — reverting
  is a standard `git checkout`/revert of `diagnostic_store.py` (and the new config fields).
- Rows already encrypted before a rollback become unreadable by the reverted code (no
  decrypt path existed before this change either, so this is a net-new one-way state, not a
  regression) — mitigate by not enabling `encrypt=True` in production config until the
  corresponding fetch/decrypt path is also implemented.
- Purge deletions are not reversible; rollback does not restore already-purged rows — the
  30-day default is chosen to make this an acceptable, expected steady-state loss (per plan
  Risks mitigation).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/diagnostic_store.py` | Unit: payload with `artifacts`/`rag_stage_outcomes` → `save()` → `fetch()` shows redacted form with count preserved | `uv run pytest tests/test_diagnostic_store.py -k sensitive -v` | Sensitive fields redacted, counts intact |
| `scripts/agent/diagnostic_store.py` | Unit: `save(..., encrypt=True)` with configured key → raw row content is not equal to plaintext; decrypting with the same key recovers it | `uv run pytest tests/test_diagnostic_store.py -k encrypt -v` | Ciphertext stored; correct key decrypts, wrong/missing key fails |
| `scripts/agent/diagnostic_store.py` | Unit: seed rows older than retention window → `save()` triggers purge → old rows gone, recent rows retained | `uv run pytest tests/test_diagnostic_store.py -k purge -v` | Old rows deleted, recent rows survive |
| Full suite | Regression | `uv run pytest -v` | No new failures |
| Standard toolchain | Lint/type/arch/security | `uv run ruff check scripts/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | All pass |

## Out of scope

- Adding decrypt-on-read support to `fetch()`/`fetch_by_kind()`/`fetch_all()`.
- The `repl.py` warning-log change (separate document,
  `implementations/20260726-174737_repl.py.md`).
- Key rotation/management tooling.
- Any change to conversation-history storage or encryption.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-160357_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-174644
- Related target files: scripts/agent/diagnostic_store.py
