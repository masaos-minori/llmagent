"""scripts/agent/diagnostic_store.py

DiagnosticStore — dedicated storage for runtime diagnostics.
Diagnostic data is stored in the session_diagnostics table,
separate from normal conversation messages.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import orjson
from cryptography.fernet import Fernet, InvalidToken
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader
from shared.json_utils import dumps

from agent.config_dataclasses import DiagnosticsConfig

logger = logging.getLogger(__name__)

# Payload keys redacted by _filter_sensitive_fields(); may carry raw artifact
# URIs or RAG stage outcome contents that should not be persisted unredacted.
_SENSITIVE_FIELDS: tuple[str, ...] = ("artifacts", "rag_stage_outcomes")

_SENSITIVE_PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|secret|token|password|access_token|auth_token|bearer|client_secret)['\"]?[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{16,})['\"]?"
    ),
]


class DiagnosticStore:
    """Dedicated store for diagnostic messages, separate from conversation history."""

    def __init__(self, session_id: int | None = None) -> None:
        """Initialize the diagnostic store with an optional session ID."""
        self.session_id = session_id

    def _load_diagnostics_config(self) -> DiagnosticsConfig:
        """Load diagnostics encryption/retention settings from agent.toml.

        Reads config directly via ConfigLoader rather than the full
        AgentConfig/build_agent_config() pipeline, since DiagnosticStore has
        no AgentContext reference to draw a shared config instance from —
        mirrors the RetentionConfig.from_config() pattern already used for
        session retention (db/maintenance.py).
        """
        raw_cfg = ConfigLoader().load("agent.toml")
        diagnostics_raw = raw_cfg.get("diagnostics", {})
        if not isinstance(diagnostics_raw, dict):
            diagnostics_raw = {}
        encryption_key = str(diagnostics_raw.get("encryption_key", ""))
        retention_days = int(diagnostics_raw.get("retention_days", 30))
        raw_sf = diagnostics_raw.get("sensitive_fields", [])
        if isinstance(raw_sf, list):
            sf = frozenset(raw_sf)
        else:
            sf = frozenset()
        return DiagnosticsConfig(
            encryption_key=encryption_key,
            retention_days=retention_days,
            sensitive_fields=sf,
        )

    def _filter_sensitive_fields(self, content: str) -> str:
        """Redact sensitive fields from a JSON diagnostic payload.

        Replaces sensitive field list values with
        {"_redacted": True, "count": <len>} so downstream readers can tell
        "filtered" apart from "field never populated", without leaking the
        raw artifact URIs or RAG stage outcome contents. Content that is not
        valid JSON, or not a JSON object, is returned unchanged.

        The set of sensitive fields is loaded from DiagnosticsConfig and merged
        with the hardcoded defaults (_SENSITIVE_FIELDS).
        """
        try:
            payload = orjson.loads(content)
        except orjson.JSONDecodeError:
            return content
        if not isinstance(payload, dict):
            return content
        redacted = False
        # Merge configured fields with hardcoded defaults
        effective_fields = frozenset(_SENSITIVE_FIELDS) | frozenset(
            self._load_diagnostics_config().sensitive_fields
        )
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

    def _purge_old_diagnostics(self) -> None:
        """Delete diagnostic rows older than the configured retention period."""
        retention_days = self._load_diagnostics_config().retention_days
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
        encrypt: bool = False,
    ) -> None:
        """Persist one diagnostic entry.

        Purges expired rows first, then redacts sensitive fields (`artifacts`,
        `rag_stage_outcomes`) from `content` unconditionally. When
        `encrypt=True` and an encryption key is configured, the redacted
        content is Fernet-encrypted before being written.
        """
        self._purge_old_diagnostics()
        content = self._filter_sensitive_fields(content)

        diagnostics_cfg = self._load_diagnostics_config()
        if not diagnostics_cfg.encryption_key:
            for pattern in _SENSITIVE_PATTERNS:
                if pattern.search(content):
                    raise RuntimeError(
                        "Sensitive information detected in diagnostic content without encryption enabled."
                    )

        if encrypt and diagnostics_cfg.encryption_key:
            content = self._encrypt_content(content, diagnostics_cfg.encryption_key)

        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "INSERT INTO session_diagnostics"
                " (session_id, kind, content, workflow_id, task_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (session_id, kind, content, workflow_id, task_id),
            )
            db.commit()

    def fetch(self, session_id: int) -> list[dict[str, Any]]:
        """Return all diagnostics for a session, newest first."""
        cfg = self._load_diagnostics_config()
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, created_at"
                " FROM session_diagnostics WHERE session_id = ?"
                " ORDER BY created_at DESC",
                (session_id,),
            )
        result = []
        for row in rows:
            entry = dict(row)
            content = entry["content"]
            # Decrypt if content appears to be a Fernet token
            if cfg.encryption_key and content.startswith("gAAAAA"):
                try:
                    decrypted = (
                        Fernet(cfg.encryption_key.encode("utf-8"))
                        .decrypt(content.encode("utf-8"))
                        .decode("utf-8")
                    )
                    entry["content"] = decrypted
                except (ValueError, TypeError, InvalidToken):
                    logger.warning(
                        "Failed to decrypt diagnostic row %s for session %s",
                        entry.get("id"),
                        session_id,
                    )
                    # Leave ciphertext as-is if decryption fails
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
