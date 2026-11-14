## Goal

Make `DiagnosticStore` consume a validated, injected `DiagnosticsConfig` snapshot and make its persistence path fail closed: no original content is written when filtering fails, encryption is applied by policy instead of by caller choice, and retrieval reports the stored form (encrypted, redacted-plaintext, decrypt-failed) distinctly instead of presenting ciphertext as content. (`REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-009`)

## Scope
**Release unit**: `storage_format`(new) column + save()/fetch() write-and-read path

## Assumptions
- The `storage_format`(new) column is added by `scripts/db/schema_sql.py` (its own row) as a `TEXT NOT NULL DEFAULT 'plaintext'` column. This file only writes and reads it; the write path always sets it explicitly (`encrypted` when a key encrypts, otherwise `plaintext`). Because `session.sqlite` is recreate-only, no backfill is needed here.
- `diagnostics_cfg` is a **required** constructor argument. All producers construct the store from `ctx.cfg.diagnostics`; their wiring is out of scope for this file (see `orchestrator.py`, `repl.py`, `session.py`).
- Raising `RuntimeError` on filter failure degrades to a warning through the existing `session_persister.py` `RuntimeError` catch, so `AC-5` (a diagnostic save never crashes the turn) is preserved.
- `DiagnosticsConfig` exposes `encryption_key`, `retention_days`, `sensitive_fields` (a `frozenset[str]`); `save()`/`_filter_sensitive_fields()`/`_purge_old_diagnostics()` already read these from the config object passed in.

## Design decisions
- **Required `diagnostics_cfg` vs optional.** Make it required (`__init__(self, session_id, diagnostics_cfg)`). A store that cannot be constructed without a validated snapshot cannot fall back to a per-op `agent.toml` read, which is what makes `AC-6` hold. `session_id` keeps its existing `None` default.
- **Fail-closed on filter failure = reject (`raise RuntimeError`) vs fixed marker.** Choose reject. It matches the existing `detects_secrets` path (which raises `RuntimeError`) and the documented non-fatal contract (`session_persister.py` catches `RuntimeError`). The original content is never written either way; reject is the simpler, already-contracted behavior.

## Alternatives considered
- **Fixed marker on filter failure instead of raising.** Rejected: reject is consistent with the secret-detection `RuntimeError` and needs no sentinel-string convention for consumers.
- **Optional `diagnostics_cfg` with a lazy default.** Rejected: a lazy default reintroduces either a per-op config read (defeating `AC-6`) or a possibly-stale snapshot captured at import time.

## Implementation
### Target file
`scripts/agent/diagnostic_store.py`
### Procedure
1. `__init__`: add a required `diagnostics_cfg: DiagnosticsConfig` parameter and store it as `self.diagnostics_cfg`; keep `session_id: int | None = None`.
2. Delete `_load_diagnostics_config()` entirely (current lines 37-61).
3. `save()`: use `self.diagnostics_cfg` instead of calling `_load_diagnostics_config()`; remove the `encrypt: bool = False` parameter; fail closed on filter failure; encrypt by policy when a key is configured; populate `storage_format`(new) in the `INSERT`.
4. `fetch()`: use `self.diagnostics_cfg`; read `storage_format`(new); classify each row and never return ciphertext as `content`.
### Method
- **`__init__`** (current lines 33-35):
  - Change signature to `def __init__(self, session_id: int | None = None, diagnostics_cfg: DiagnosticsConfig) -> None:`.
  - Set `self.diagnostics_cfg = diagnostics_cfg` alongside `self.session_id = session_id`.
- **Delete** the `_load_diagnostics_config` method (lines 37-61) and its two call sites in `save()` (line 148) and `fetch()` (line 183).
- **`save()`** (current lines 132-179):
  - Remove `encrypt: bool = False` from the signature.
  - Replace `diagnostics_cfg = self._load_diagnostics_config()` with `diagnostics_cfg = self.diagnostics_cfg` (or reference `self.diagnostics_cfg` directly).
  - In the `try/except` around `_filter_sensitive_fields()`, change the `except` branch to **raise** instead of logging-and-proceeding:
    ```python
    except Exception:  # noqa: BLE001 — fail closed: never persist unredacted content
        raise RuntimeError(
            f"Redaction failed for {session_id} diagnostic (kind={kind}); refusing to persist."
        )
    ```
    Remove the `_filter_failed` flag and its downstream gating; there is no longer a "proceed without filtering" path.
  - Replace the secret-detection block (current lines 162-167) so it runs whenever no key is configured (no `_filter_failed` condition):
    ```python
    if not diagnostics_cfg.encryption_key:
        if detects_secrets(content):
            raise RuntimeError(
                "Sensitive information detected in diagnostic content without encryption enabled."
            )
    ```
  - Replace the conditional encryption (current lines 169-170) with encryption by policy:
    ```python
    if diagnostics_cfg.encryption_key:
        content = self._encrypt_content(content, diagnostics_cfg.encryption_key)
    storage_format = "encrypted" if diagnostics_cfg.encryption_key else "plaintext"
    ```
  - Update the `INSERT` to include `storage_format`(new):
    ```python
    "INSERT INTO session_diagnostics"
    " (session_id, kind, content, workflow_id, task_id, storage_format)"
    " VALUES (?, ?, ?, ?, ?, ?)",
    (session_id, kind, content, workflow_id, task_id, storage_format),
    ```
  - Update the `save()` docstring to drop the `encrypt=True` description and state that encryption is applied by policy and `storage_format`(new) is recorded.
- **`fetch()`** (current lines 181-212):
  - Replace `cfg = self._load_diagnostics_config()` with `cfg = self.diagnostics_cfg`.
  - Add `storage_format`(new) to the `SELECT` columns.
  - Classify by `storage_format`(new) instead of (or in addition to) the `gAAAAA` prefix heuristic:
    ```python
    fmt = entry.get("storage_format")
    content = entry["content"]
    if fmt == "encrypted" and cfg.encryption_key and content.startswith("gAAAAA"):
        try:
            entry["content"] = Fernet(cfg.encryption_key.encode("utf-8")).decrypt(...).decode("utf-8")
        except (ValueError, TypeError, InvalidToken):
            entry["storage_format"] = "decrypt_failed"
            entry["content"] = None  # never surface ciphertext as ordinary content
            logger.warning("Failed to decrypt diagnostic row %s for session %s", entry.get("id"), session_id)
    ```
    Rows whose `storage_format`(new) is `plaintext`/`redacted_plaintext`(new) are returned unchanged; `decrypt_failed`(new) rows carry `content=None` and the distinct format label.

### Details
- `save_serialization_event`, `save_partial_completion`, `save_transport_failure` call `self.save(...)` without `encrypt=`; they need no change but now inherit the fail-closed and by-policy-encryption behavior automatically.
- `_encrypt_content` currently passes through when `key` is empty; with encryption now gated on `diagnostics_cfg.encryption_key` before the call, the pass-through is dead but harmless — leave it.
- The `RuntimeError` raised on filter failure or secret detection is caught by `session_persister.py`'s existing handler, preserving the non-fatal, `asyncio.to_thread()` save contract (`REQ-009`, `AC-5`).

### Companion test files
- `tests/agent/test_diagnostic_store_security.py`
  - Procedure: regress `test_filter_failed_carve_out_preserved` (lines 451-493) to expect rejection on filter failure; update every `TestEncryptionStatus`/`TestSharedDetectorGuard` site that passes `encrypt=` to the fail-closed contract; drop the `patch(DiagnosticStore, "_load_diagnostics_config")` mocks (lines 194, 230, 306, 365, 436, 469).
  - Validation: `uv run pytest tests/agent/test_diagnostic_store_security.py` passes.
- `tests/agent/test_diagnostic_store.py`
  - Procedure: convert `TestEncryption` (~354-440), `test_save_rejects_sensitive_data_without_encryption` (~552), `TestFetchEncryptedRoundTrip` (~746) to injection + fail-closed behavior; replace direct `store._load_diagnostics_config()` calls (lines 302, 311, 319, 326, 334) with an injected `DiagnosticsConfig`.
  - Validation: `uv run pytest tests/agent/test_diagnostic_store.py` passes.

## Compatibility considerations
Removing the public `encrypt` argument changes `DiagnosticStore.save()`'s signature. No production caller passes `encrypt=True` (verified: only a docstring and a comment mention it). External callers are test files covered by the companions above plus the fallout rows that construct `DiagnosticStore()` without the new required argument.

## Security considerations
This is the security-sensitive change: the persistence path previously failed open on a redaction error. Fail-closed rejection guarantees no unredacted content (LLM partial text, transport-error details) reaches `session_diagnostics`. Encryption-by-policy removes the caller-choice gap (`UNK-01`) while preserving the accepted Option B redacted-plaintext baseline when no key is configured.

## Rollback considerations
Revert the commit to `scripts/agent/diagnostic_store.py` (and its companion test updates). The `storage_format`(new) column change also touches `scripts/db/schema_sql.py`; reverting only this file against the new DDL leaves `save()` inserting into a column the canonical DDL no longer lists — revert both together.

## Validation plan
- Unit: filter failure raises `RuntimeError` (reject); no-key redaction path still secret-checks; encryption applied without an `encrypt=` argument; decrypt-failed row reported distinctly with `content=None`; no `_load_diagnostics_config` remains.
- Command: `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_diagnostic_store.py`.
- Confirm `rg _load_diagnostics_config scripts/` returns no hits outside deleted code.

## Completion criteria
- `DiagnosticStore.__init__` requires `diagnostics_cfg`; `_load_diagnostics_config` no longer exists anywhere in `scripts/`.
- `save()` raises on filter failure and on secret detection without a key; encrypts by policy when a key is configured; writes an explicit `storage_format`(new).
- `fetch()` classifies rows by `storage_format`(new) and never returns ciphertext as `content`.
- Companion security/store tests pass; `mypy`, `ruff`, `bandit` clean.

## Out of Scope
- Constructing the store with the injected config in `orchestrator.py`, `repl.py`, `session.py` (their own rows).
- Adding the `storage_format`(new) DDL column (`scripts/db/schema_sql.py`, its own row).
- Transport-error detail bounding (`REQ-007`); see `diagnostic_store.py` Phase 4 step — out of scope for this document's fail-closed/injection focus unless included by the implementer.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companions cover this |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Compatibility notes only |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-009`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `scripts/agent/diagnostic_store.py`, `tests/agent/test_diagnostic_store_security.py`, `tests/agent/test_diagnostic_store.py`
