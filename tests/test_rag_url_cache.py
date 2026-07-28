"""Characterization tests for RAG URL cache behavior."""

from unittest.mock import MagicMock, patch

from rag.llm_client import _get_cached_embed_url, _get_cached_llm_url


class TestConfigFailureReturnsEmptyStringCache:
    """Verify config failure returns empty string cache."""

    def test_get_cached_llm_url_returns_empty_on_config_failure(self) -> None:
        """When config loading fails, _get_cached_llm_url returns empty string."""
        with patch("rag.llm_client.ConfigLoader") as mock_loader:
            mock_loader.return_value.load_all.side_effect = FileNotFoundError(
                "config missing"
            )
            # Clear the module-level cache before testing
            import rag.llm_client

            original = rag.llm_client._llm_url_cache
            rag.llm_client._llm_url_cache = None
            try:
                result = _get_cached_llm_url()
                assert result == ""
            finally:
                rag.llm_client._llm_url_cache = original

    def test_get_cached_embed_url_returns_empty_on_config_failure(self) -> None:
        """When config loading fails, _get_cached_embed_url returns empty string."""
        with patch("rag.llm_client.ConfigLoader") as mock_loader:
            mock_loader.return_value.load_all.side_effect = ValueError("bad config")
            import rag.llm_client

            original = rag.llm_client._embed_url_cache
            rag.llm_client._embed_url_cache = None
            try:
                result = _get_cached_embed_url()
                assert result == ""
            finally:
                rag.llm_client._embed_url_cache = original

    def test_get_cached_llm_url_returns_empty_on_value_error(self) -> None:
        """ValueError during config loading also results in empty string cache."""
        with patch("rag.llm_client.ConfigLoader") as mock_loader:
            mock_loader.return_value.load_all.side_effect = ValueError("invalid config")
            import rag.llm_client

            original = rag.llm_client._llm_url_cache
            rag.llm_client._llm_url_cache = None
            try:
                result = _get_cached_llm_url()
                assert result == ""
            finally:
                rag.llm_client._llm_url_cache = original


class TestCacheReuseOnHit:
    """Verify cache reuse on hit."""

    def test_llm_url_cache_reused_on_second_call(self) -> None:
        """Second call to _get_cached_llm_url returns cached value without reloading config."""
        import rag.llm_client

        original = rag.llm_client._llm_url_cache
        try:
            rag.llm_client._llm_url_cache = "http://cached-url:8080/v1"
            result1 = _get_cached_llm_url()
            result2 = _get_cached_llm_url()
            assert result1 == result2 == "http://cached-url:8080/v1"
        finally:
            rag.llm_client._llm_url_cache = original

    def test_embed_url_cache_reused_on_second_call(self) -> None:
        """Second call to _get_cached_embed_url returns cached value without reloading config."""
        import rag.llm_client

        original = rag.llm_client._embed_url_cache
        try:
            rag.llm_client._embed_url_cache = "http://embed-host:8080/embed"
            result1 = _get_cached_embed_url()
            result2 = _get_cached_embed_url()
            assert result1 == result2 == "http://embed-host:8080/embed"
        finally:
            rag.llm_client._embed_url_cache = original

    def test_cache_populated_after_first_load(self) -> None:
        """After first successful load, subsequent calls use cache."""
        import rag.llm_client

        original = rag.llm_client._llm_url_cache
        try:
            rag.llm_client._llm_url_cache = None
            mock_cfg = MagicMock()
            mock_cfg.get.return_value = "http://fresh-config:8080/v1"
            with patch("rag.llm_client.ConfigLoader") as mock_loader:
                mock_loader.return_value.load_all.return_value = mock_cfg
                result1 = _get_cached_llm_url()
                result2 = _get_cached_llm_url()
                assert result1 == result2
                assert mock_loader.return_value.load_all.call_count == 1
        finally:
            rag.llm_client._llm_url_cache = original
