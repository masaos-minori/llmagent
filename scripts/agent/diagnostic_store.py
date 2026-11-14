"""scripts/agent/diagnostic_store.py

DiagnosticStore — dedicated storage for runtime diagnostics.
Diagnostic data is stored in the session_diagnostics table,
separate from normal conversation messages.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import orjson
from cryptography.fernet import Fernet, InvalidToken
from db.helper import SQLiteHelper
from shared.json_utils import dumps

from agent.config_dataclasses import DiagnosticsConfig
from agent.secrets_masker import detects_secrets

logger = logging.getLogger(__name__)

# Payload keys redacted by _filter_sensitive_fields(); may carry raw artifact
# URIs or RAG stage outcome contents that should not be persisted unredacted.
_SENSITIVE_FIELDS: tuple[str, ...] = ("artifacts", "rag_stage_outcomes")


class DiagnosticStore:
    """Dedicated store for diagnostic messages, separate from conversation history."""

    def __init__(
        self,
        diagnostics_cfg: DiagnosticsConfig,
        session_id: int | None = None,
    ) -> None:
        """Initialize the diagnostic store with a validated DiagnosticsConfig
        snapshot and an optional session ID.

        `diagnostics_cfg` is required (a store that cannot be constructed
        without a validated snapshot cannot fall back to a per-op agent.toml
        read, which is what keeps AC-6 in force). `session_id` keeps its
        existing `None` default.
        """
        self.diagnostics_cfg = diagnostics_cfg
        self.session_id = session_id

    def _filter_sensitive_fields(self, content: str, cfg: DiagnosticsConfig) -> str:
        """Redact sensitive fields from a JSON diagnostic payload.

        Replaces sensitive field list values with
        {"_redacted": True, "count": <len>} so downstream readers can tell
        "filtered" apart from "field never populated", without leaking the
        raw artifact URIs or RAG stage outcome contents. Content that is not
        valid JSON, or not a JSON object, is returned unchanged.

        The set of sensitive fields is provided by the caller's
        DiagnosticsConfig snapshot and merged with the hardcoded defaults
        (_SENSITIVE_FIELDS).
        """
        try:
            payload = orjson.loads(content)
        except orjson.JSONDecodeError:
            return content
        if not isinstance(payload, dict):
            return content
        redacted = False
        # Merge configured fields with hardcoded defaults
        effective_fields = frozenset(_SENSITIVE_FIELDS) | cfg.sensitive_fields
        for field_name in effective_fields:
            value = payload.get(field_name)
            if isinstance(value, list):
                payload[field_name] = {"_redacted": True, "count": len(value)}
                redacted = True
        if not redacted:
            return content
        return dumps(payload)

    def _encrypt_content(self, content: str, key: str) -> str:
        """Encrypt content with Fernet using the configured key.

        Pass-through (no-op) when key is empty, since encryption is opt-in
        and requires a configured key.
        """
        if not key:
            return content
        return (
            Fernet(key.encode("utf-8")).encrypt(content.encode("utf-8")).decode("utf-8")
        )

    def _purge_old_diagnostics(self, cfg: DiagnosticsConfig) -> None:
        """Delete diagnostic rows older than the configured retention period.

        The retention period is supplied by the caller's DiagnosticsConfig
        snapshot.
        """
        retention_days = cfg.retention_days
        if retention_days <= 0:
            return
        cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute(
                "DELETE FROM session_diagnostics WHERE created_at < ?",
                (cutoff,),
            )
            db.commit()
            deleted = cur.rowcount
        if deleted > 0:
            logger.info(
                "Purged %d diagnostic row(s) older than %d day(s)",
                deleted,
                retention_days,
            )

    def save(
        self,
        session_id: int | None,
        kind: str,
        content: str,
        workflow_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        """Persist one diagnostic entry.

        Purges expired rows first, then redacts sensitive fields (`artifacts`,
        `rag_stage_outcomes`) from `content`. Redaction fails closed: a
        `_filter_sensitive_fields` error raises `RuntimeError` rather than
        persisting unredacted content. When an encryption key is configured the
        redacted content is Fernet-encrypted by policy (not by a caller flag),
        and the resulting `storage_format` (`encrypted` or `plaintext`) is
        recorded alongside the row.
        """
        diagnostics_cfg = self.diagnostics_cfg
        self._purge_old_diagnostics(diagnostics_cfg)
        try:
            content = self._filter_sensitive_fields(content, diagnostics_cfg)
        except Exception:  # noqa: BLE001 — fail closed: never persist unredacted content
            raise RuntimeError(
                f"Redaction failed for {session_id} diagnostic (kind={kind}); refusing to persist."
            )

        if not diagnostics_cfg.encryption_key:
            if detects_secrets(content):
                raise RuntimeError(
                    "Sensitive information detected in diagnostic content without encryption enabled."
                )

        if diagnostics_cfg.encryption_key:
            content = self._encrypt_content(content, diagnostics_cfg.encryption_key)
        storage_format = "encrypted" if diagnostics_cfg.encryption_key else "plaintext"

        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "INSERT INTO session_diagnostics"
                " (session_id, kind, content, workflow_id, task_id, storage_format)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, kind, content, workflow_id, task_id, storage_format),
            )
            db.commit()

    def fetch(self, session_id: int) -> list[dict[str, Any]]:
        """Return all diagnostics for a session, newest first.

        Rows are classified by their stored `storage_format`: `encrypted` rows
        are Fernet-decrypted when the key still validates (a decrypt failure
        marks the row `decrypt_failed` with `content=None`); `plaintext` and
        `redacted_plaintext` rows are returned unchanged. Ciphertext is never
        surfaced as ordinary content.
        """
        cfg = self.diagnostics_cfg
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, storage_format, created_at"
                " FROM session_diagnostics WHERE session_id = ?"
                " ORDER BY created_at DESC",
                (session_id,),
            )
        result = []
        for row in rows:
            entry = dict(row)
            content = entry["content"]
            fmt = entry.get("storage_format")
            if (
                fmt == "encrypted"
                and cfg.encryption_key
                and content.startswith("gAAAAA")
            ):
                try:
                    entry["content"] = (
                        Fernet(cfg.encryption_key.encode("utf-8"))
                        .decrypt(content.encode("utf-8"))
                        .decode("utf-8")
                    )
                except (ValueError, TypeError, InvalidToken):
                    entry["storage_format"] = "decrypt_failed"
                    entry["content"] = (
                        None  # never surface ciphertext as ordinary content
                    )
                    logger.warning(
                        "Failed to decrypt diagnostic row %s for session %s",
                        entry.get("id"),
                        session_id,
                    )
            result.append(entry)
        return result

    def save_serialization_event(
        self,
        session_id: int | None,
        round_id: str,
        trigger_tool: str,
        affected_count: int,
        mode: str,
        elapsed_ms: float,
        reason: str,
    ) -> None:
        """Persist a round-level serialization event."""
        content = dumps(
            {
                "round_id": round_id,
                "trigger_tool": trigger_tool,
                "affected_count": affected_count,
                "mode": mode,
                "elapsed_ms": round(elapsed_ms, 1),
                "reason": reason,
            }
        )
        self.save(session_id=session_id, kind="serialization_event", content=content)

    def save_partial_completion(
        self,
        session_id: int | None,
        turn: int,
        reason: str,
        content_length: int,
    ) -> None:
        """Persist a partial LLM completion event to session_diagnostics."""
        content = dumps(
            {
                "turn": turn,
                "reason": reason,
                "content_length": content_length,
            }
        )
        self.save(session_id=session_id, kind="partial_completion", content=content)

    def save_transport_failure(
        self,
        session_id: int | None,
        tool_name: str,
        server_key: str,
        error_msg: str,
    ) -> None:
        """Persist a transport-level tool execution failure."""
        content = dumps(
            {
                "tool_name": tool_name,
                "server_key": server_key,
                "error": error_msg,
            }
        )
        self.save(session_id=session_id, kind="transport_failure", content=content)
