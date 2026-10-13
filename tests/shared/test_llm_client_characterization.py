"""tests/shared/test_llm_client_characterization.py

Characterization tests for scripts/shared/llm_client.py paths not already covered by
tests/agent/test_llm_client.py: build_llm_url/build_embed_url edge cases, the
(the LLMClient.build_payload wrapper and request_with_retry were removed).

These tests exist to lock current behavior before a refactoring pass on
scripts/shared/llm_client.py (see prompts/04_refactor.md). They assert observed
behavior, not intended/ideal behavior.
"""

from __future__ import annotations

from shared.llm_client import build_embed_url, build_llm_url

# ── build_llm_url / build_embed_url ───────────────────────────────────────────


class TestBuildLlmUrl:
    def test_empty_base_returns_empty(self) -> None:
        assert build_llm_url("") == ""

    def test_appends_chat_completions_path(self) -> None:
        assert build_llm_url("http://llm:8000") == "http://llm:8000/v1/chat/completions"

    def test_strips_trailing_slash_before_append(self) -> None:
        assert (
            build_llm_url("http://llm:8000/") == "http://llm:8000/v1/chat/completions"
        )


class TestBuildEmbedUrl:
    def test_empty_base_returns_empty(self) -> None:
        assert build_embed_url("") == ""

    def test_appends_embedding_path(self) -> None:
        assert build_embed_url("http://llm:8000") == "http://llm:8000/embedding"

    def test_strips_trailing_slash_before_append(self) -> None:
        assert build_embed_url("http://llm:8000/") == "http://llm:8000/embedding"
