"""tests/mcp_servers/rag_pipeline/test_rag_security_validation.py

Tests for scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py: validate_rag_pipeline_security()
reports the RAG server's own configuration as a Security Posture, non_secret_view() carries no
Secret and no value a fingerprint may not hash, and no URL, path, or token value is echoed.
"""

from __future__ import annotations

from pathlib import Path

from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig
from mcp_servers.rag_pipeline.rag_pipeline_security import (
    validate_rag_pipeline_security,
)
from shared.security.posture_contract import (
    COMMON_CHECK_IDS,
    REQUIRED_CHECK_IDS,
    compute_config_fingerprint,
)
from shared.security.result_dto import (
    REASON_CONFIG_INVALID,
    REASON_CONFIG_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)
from shared.security.startup_flow import OWN_CONFIG_FILE_VIEW_KEY

RAG_CHECK_IDS = (
    "server.embed_url_configured",
    "server.llm_url_configured",
    "server.rag_db_path_configured",
    "server.sqlite_vec_available",
    "server.top_k_bounds",
    "server.min_score_valid",
    "server.refiner_limits",
)
SECRET_URL = "http://secret-host:9999/v1/embeddings"
SECRET_DB_PATH = "/opt/secret-host/rag.sqlite"
SECRET_VEC_PATH = "/opt/secret-host/vec0.so"
SECRET_TOKEN = "sk-secret-token-value"


def _cfg(**overrides: object) -> RagPipelineConfig:
    """A RAG config with only the fields a test cares about overridden."""
    return RagPipelineConfig(**{key: value for key, value in overrides.items()})


def _results(**overrides: object) -> dict[str, SecurityCheckResult]:
    """The RAG check results keyed by check id."""
    return {
        result.check_id: result
        for result in validate_rag_pipeline_security(_cfg(**overrides))
    }


def _sensitive_values() -> tuple[str, ...]:
    """Values that must never appear in a posture field or message."""
    return (SECRET_URL, SECRET_DB_PATH, SECRET_VEC_PATH, SECRET_TOKEN)


class TestNonSecretView:
    """The view is the fingerprint input, so it must be hashable and carry no Secret (REQ-002)."""

    def test_carries_the_own_config_file_key(self) -> None:
        view = _cfg().non_secret_view()
        assert view[OWN_CONFIG_FILE_VIEW_KEY] == "rag_pipeline_mcp_server.toml"

    def test_excludes_both_secret_fields(self) -> None:
        view = _cfg(
            auth_token=SECRET_TOKEN, rag_auth_token=SECRET_TOKEN
        ).non_secret_view()
        assert "auth_token" not in view
        assert "rag_auth_token" not in view
        assert SECRET_TOKEN not in view.values()

    def test_every_value_can_be_fingerprinted(self) -> None:
        cfg = _cfg(
            llm_url=SECRET_URL,
            embed_url=SECRET_URL,
            rag_db_path=SECRET_DB_PATH,
            sqlite_vec_so=SECRET_VEC_PATH,
            auth_token=SECRET_TOKEN,
            rag_auth_token=SECRET_TOKEN,
        )
        digest = compute_config_fingerprint(cfg.non_secret_view())
        assert len(digest) == 64
        assert all(char in "0123456789abcdef" for char in digest)

    def test_paths_and_urls_appear_only_as_presence(self) -> None:
        view = _cfg(
            llm_url=SECRET_URL,
            embed_url=SECRET_URL,
            rag_db_path=SECRET_DB_PATH,
            sqlite_vec_so=SECRET_VEC_PATH,
        ).non_secret_view()
        for value in view.values():
            assert value not in (SECRET_URL, SECRET_DB_PATH, SECRET_VEC_PATH)
        assert view["llm_url_present"] is True
        assert view["rag_db_path_present"] is True
        assert view["sqlite_vec_so_present"] is True

    def test_absent_setting_is_reported_as_absent(self) -> None:
        view = _cfg().non_secret_view()
        assert view["embed_url_present"] is False
        assert view["rag_db_path_present"] is False

    def test_builds_a_new_dict(self) -> None:
        cfg = _cfg(top_k_search=20)
        first = cfg.non_secret_view()
        first["top_k_search"] = 1
        assert cfg.top_k_search == 20

        cfg.top_k_search = 7
        assert first["top_k_search"] == 1

    def test_fingerprint_follows_a_changed_setting(self) -> None:
        before = compute_config_fingerprint(_cfg(top_k_search=20).non_secret_view())
        after = compute_config_fingerprint(_cfg(top_k_search=21).non_secret_view())
        assert before != after

    def test_fingerprint_does_not_hash_token_values(self) -> None:
        first = compute_config_fingerprint(
            _cfg(
                auth_token="sk-token-one", rag_auth_token="sk-token-one"
            ).non_secret_view()
        )
        second = compute_config_fingerprint(
            _cfg(auth_token=SECRET_TOKEN, rag_auth_token=SECRET_TOKEN).non_secret_view()
        )
        assert first == second


class TestUrlAndPathConfigured:
    """A required endpoint or database path that is empty is a startup failure (REQ-010)."""

    def test_missing_embed_url_fails(self) -> None:
        result = _results()["server.embed_url_configured"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_MISSING

    def test_configured_embed_url_is_ok(self) -> None:
        result = _results(embed_url=SECRET_URL)["server.embed_url_configured"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK

    def test_missing_rag_db_path_fails(self) -> None:
        result = _results()["server.rag_db_path_configured"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_MISSING

    def test_configured_rag_db_path_is_ok(self) -> None:
        result = _results(rag_db_path=SECRET_DB_PATH)["server.rag_db_path_configured"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestLlmUrlConfigured:
    """llm_url is only contacted on the rerank and refiner paths (REQ-010)."""

    def test_missing_llm_url_fails_when_rerank_is_enabled(self) -> None:
        result = _results(use_rerank=True)["server.llm_url_configured"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_MISSING

    def test_missing_llm_url_fails_when_refiner_is_enabled(self) -> None:
        result = _results(use_rerank=False, use_refiner=True)[
            "server.llm_url_configured"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_MISSING

    def test_missing_llm_url_is_not_applicable_when_both_are_disabled(self) -> None:
        result = _results(use_rerank=False, use_refiner=False)[
            "server.llm_url_configured"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_configured_llm_url_is_ok(self) -> None:
        result = _results(llm_url=SECRET_URL, use_rerank=True)[
            "server.llm_url_configured"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestSqliteVecAvailable:
    """Vector search cannot run without the sqlite-vec extension file (REQ-010)."""

    def test_missing_setting_fails(self) -> None:
        result = _results()["server.sqlite_vec_available"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_path_that_is_not_a_file_fails(self, tmp_path: Path) -> None:
        result = _results(sqlite_vec_so=str(tmp_path / "absent.so"))[
            "server.sqlite_vec_available"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_directory_instead_of_a_file_fails(self, tmp_path: Path) -> None:
        result = _results(sqlite_vec_so=str(tmp_path))["server.sqlite_vec_available"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_existing_file_is_ok(self, tmp_path: Path) -> None:
        extension = tmp_path / "vec0.so"
        extension.write_bytes(b"\x7fELF")
        result = _results(sqlite_vec_so=str(extension))["server.sqlite_vec_available"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestTopKBounds:
    """A non-positive or inverted top-k discards results the pipeline just produced (REQ-010)."""

    def test_zero_top_k_search_fails(self) -> None:
        result = _results(top_k_search=0)["server.top_k_bounds"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_negative_rag_top_k_fails(self) -> None:
        result = _results(rag_top_k=-1)["server.top_k_bounds"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_rag_top_k_above_top_k_rerank_fails(self) -> None:
        result = _results(top_k_rerank=5, rag_top_k=6)["server.top_k_bounds"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_ordered_positive_bounds_are_ok(self) -> None:
        result = _results(top_k_search=20, top_k_rerank=15, rag_top_k=5)[
            "server.top_k_bounds"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestMinScoreValid:
    """A negative distance threshold silently filters every hit (REQ-010)."""

    def test_negative_min_score_fails(self) -> None:
        result = _results(rag_min_score=-0.1)["server.min_score_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_zero_min_score_is_ok(self) -> None:
        result = _results(rag_min_score=0.0)["server.min_score_valid"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestRefinerLimits:
    """The refiner limits only matter on the path that uses the refiner (REQ-010)."""

    def test_disabled_refiner_is_not_applicable(self) -> None:
        result = _results(use_refiner=False, refiner_max_tokens=0)[
            "server.refiner_limits"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_zero_token_limit_fails(self) -> None:
        result = _results(use_refiner=True, refiner_max_tokens=0)[
            "server.refiner_limits"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_zero_char_limit_fails(self) -> None:
        result = _results(use_refiner=True, refiner_max_chars_per_chunk=0)[
            "server.refiner_limits"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_CONFIG_INVALID

    def test_positive_limits_are_ok(self) -> None:
        result = _results(
            use_refiner=True, refiner_max_tokens=1, refiner_max_chars_per_chunk=1
        )["server.refiner_limits"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestCheckSet:
    """The seven RAG checks are always present, in a fixed order (REQ-010)."""

    def test_ids_match_the_frozen_contract(self) -> None:
        expected = tuple(
            check_id
            for check_id in REQUIRED_CHECK_IDS["rag_pipeline"]
            if check_id not in COMMON_CHECK_IDS
        )
        produced = validate_rag_pipeline_security(_cfg())
        assert [result.check_id for result in produced] == list(expected)
        assert expected == RAG_CHECK_IDS

    def test_check_set_is_identical_across_configurations(self, tmp_path: Path) -> None:
        extension = tmp_path / "vec0.so"
        extension.write_bytes(b"\x7fELF")
        configurations = (
            {},
            {"embed_url": SECRET_URL, "rag_db_path": SECRET_DB_PATH},
            {"use_rerank": False, "use_refiner": False},
            {
                "use_refiner": True,
                "refiner_max_tokens": 0,
                "sqlite_vec_so": str(extension),
            },
            {"top_k_search": 0, "rag_min_score": -1.0},
        )
        for overrides in configurations:
            produced = validate_rag_pipeline_security(_cfg(**overrides))
            assert [result.check_id for result in produced] == list(RAG_CHECK_IDS)

    def test_never_raises_for_a_policy_violation(self) -> None:
        produced = validate_rag_pipeline_security(
            _cfg(top_k_search=0, rag_top_k=99, rag_min_score=-1.0, use_refiner=True)
        )
        assert all(isinstance(result, SecurityCheckResult) for result in produced)


class TestMessages:
    """URLs, paths, and token values stay out of the posture (REQ-002)."""

    def test_no_message_carries_a_url_a_path_or_a_token(self) -> None:
        produced = validate_rag_pipeline_security(
            _cfg(
                llm_url=SECRET_URL,
                embed_url=SECRET_URL,
                rag_db_path=SECRET_DB_PATH,
                sqlite_vec_so=SECRET_VEC_PATH,
                auth_token=SECRET_TOKEN,
                rag_auth_token=SECRET_TOKEN,
                top_k_search=0,
            )
        )
        for result in produced:
            for value in _sensitive_values():
                assert value not in result.message

    def test_failure_names_the_setting_and_not_the_value(self) -> None:
        result = _results(rag_db_path=SECRET_DB_PATH, embed_url="")[
            "server.embed_url_configured"
        ]
        assert "embed_url" in result.message
        assert SECRET_DB_PATH not in result.message
        assert SECRET_URL not in result.message
