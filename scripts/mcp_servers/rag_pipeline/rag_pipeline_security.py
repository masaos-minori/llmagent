#!/usr/bin/env python3
"""scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py

RAG Pipeline self-validation — validate_rag_pipeline_security() reports rag-pipeline-mcp's own
configuration as a Security Posture, so the server validates itself before HTTP bind instead of
being audited by the Agent.

Held in a sibling module rather than in rag_pipeline_models.py because that module carries the
pydantic request and response models and the config adapter, and the validator would carry it past
the 400-line split trigger in skills/DESIGN.md. The fingerprint input stays in the config model as
RagPipelineConfig.non_secret_view() so the view and the checks read the same fields.

Dependency direction: rag_pipeline_security → rag_pipeline_models
"""

from __future__ import annotations

from pathlib import Path

from shared.security.result_dto import (
    REASON_CONFIG_INVALID,
    REASON_CONFIG_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig


def validate_rag_pipeline_security(cfg: RagPipelineConfig) -> list[SecurityCheckResult]:
    """RAG pipeline's own configuration checks, in the order the posture contract expects.

    The function is pure: it stats sqlite_vec_so but never opens rag_db_path and never contacts
    llm_url or embed_url, so validation cannot issue an outbound request or touch a database. It
    never raises for a policy violation.

    No check inspects or reports a token value. Token presence is enforced by the server's auth
    middleware and by the Agent's mcp_auth check, and REQ-002 forbids carrying Secret values in the
    posture. URLs and paths are reported as configured or not configured, never by value.
    """
    return [
        _configured_check(
            "server.embed_url_configured", "embed_url", bool(cfg.embed_url)
        ),
        _llm_url_check(cfg),
        _configured_check(
            "server.rag_db_path_configured", "rag_db_path", bool(cfg.rag_db_path)
        ),
        _sqlite_vec_check(cfg),
        _top_k_bounds_check(cfg),
        _min_score_check(cfg),
        _refiner_limits_check(cfg),
    ]


def _configured_check(
    check_id: str, setting: str, present: bool
) -> SecurityCheckResult:
    """A required setting that is empty is a startup failure, not a degraded runtime."""
    if present:
        return SecurityCheckResult(
            check_id=check_id,
            status=SecurityCheckStatus.OK,
            reason_code=REASON_OK,
            message=f"{setting} is configured",
        )
    return SecurityCheckResult(
        check_id=check_id,
        status=SecurityCheckStatus.FAILED,
        reason_code=REASON_CONFIG_MISSING,
        message=f"{setting} is not configured",
    )


def _llm_url_check(cfg: RagPipelineConfig) -> SecurityCheckResult:
    """llm_url is only contacted on the rerank and refiner paths."""
    if not cfg.use_rerank and not cfg.use_refiner:
        return SecurityCheckResult(
            check_id="server.llm_url_configured",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="llm_url is unused because use_rerank and use_refiner are both disabled",
        )
    return _configured_check("server.llm_url_configured", "llm_url", bool(cfg.llm_url))


def _sqlite_vec_check(cfg: RagPipelineConfig) -> SecurityCheckResult:
    """Vector search cannot run without the sqlite-vec extension file."""
    if not cfg.sqlite_vec_so:
        return SecurityCheckResult(
            check_id="server.sqlite_vec_available",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_DEPENDENCY_UNREACHABLE,
            message="sqlite_vec_so is not configured",
        )
    if not Path(cfg.sqlite_vec_so).is_file():
        return SecurityCheckResult(
            check_id="server.sqlite_vec_available",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_DEPENDENCY_UNREACHABLE,
            message="sqlite_vec_so does not name an existing file",
        )
    return SecurityCheckResult(
        check_id="server.sqlite_vec_available",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="sqlite_vec_so names an existing file",
    )


def _top_k_bounds_check(cfg: RagPipelineConfig) -> SecurityCheckResult:
    """A non-positive or inverted top-k discards results the pipeline just produced."""
    if min(cfg.top_k_search, cfg.top_k_rerank, cfg.rag_top_k) <= 0:
        return SecurityCheckResult(
            check_id="server.top_k_bounds",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_CONFIG_INVALID,
            message="a top_k setting is not positive",
        )
    if cfg.rag_top_k > cfg.top_k_rerank:
        return SecurityCheckResult(
            check_id="server.top_k_bounds",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_CONFIG_INVALID,
            message="rag_top_k exceeds top_k_rerank",
        )
    return SecurityCheckResult(
        check_id="server.top_k_bounds",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="top_k settings are positive and ordered",
    )


def _min_score_check(cfg: RagPipelineConfig) -> SecurityCheckResult:
    """A negative distance threshold silently filters every hit."""
    if cfg.rag_min_score < 0:
        return SecurityCheckResult(
            check_id="server.min_score_valid",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_CONFIG_INVALID,
            message="rag_min_score is negative so every hit is filtered out",
        )
    return SecurityCheckResult(
        check_id="server.min_score_valid",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="rag_min_score is not negative",
    )


def _refiner_limits_check(cfg: RagPipelineConfig) -> SecurityCheckResult:
    """The refiner limits only matter on the path that uses the refiner."""
    if not cfg.use_refiner:
        return SecurityCheckResult(
            check_id="server.refiner_limits",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="use_refiner is disabled so the refiner limits are unused",
        )
    if cfg.refiner_max_tokens <= 0 or cfg.refiner_max_chars_per_chunk <= 0:
        return SecurityCheckResult(
            check_id="server.refiner_limits",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_CONFIG_INVALID,
            message="a refiner limit is not positive while use_refiner is enabled",
        )
    return SecurityCheckResult(
        check_id="server.refiner_limits",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="refiner limits are positive",
    )
