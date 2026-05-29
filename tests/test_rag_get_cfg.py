"""tests/test_rag_get_cfg.py
Coverage for _get_cfg() error path in rag.pipeline and rag.llm.
"""

from unittest.mock import patch

from shared.config_loader import ConfigLoader


class TestRagPipelineGetCfg:
    def test_get_cfg_error_path(self, monkeypatch) -> None:
        """_get_cfg() returns {} when ConfigLoader raises."""
        import rag.pipeline as pipeline_mod

        monkeypatch.setattr(pipeline_mod, "_cfg", None)
        with patch.object(ConfigLoader, "load", side_effect=OSError("no file")):
            result = pipeline_mod._get_cfg()
        assert result == {}
        monkeypatch.setattr(pipeline_mod, "_cfg", None)


class TestRagLlmGetCfg:
    def test_get_cfg_error_path(self, monkeypatch) -> None:
        """_get_cfg() returns {} when ConfigLoader raises."""
        import rag.llm as llm_mod

        monkeypatch.setattr(llm_mod, "_cfg", None)
        with patch.object(ConfigLoader, "load", side_effect=OSError("no file")):
            result = llm_mod._get_cfg()
        assert result == {}
        monkeypatch.setattr(llm_mod, "_cfg", None)


class TestAgentConfigGetCfg:
    def test_get_cfg_error_path(self, monkeypatch) -> None:
        """_get_cfg() returns {} when ConfigLoader raises."""
        import agent.config as config_mod

        monkeypatch.setattr(config_mod, "_cfg", None)
        with patch.object(ConfigLoader, "load", side_effect=OSError("no file")):
            result = config_mod._get_cfg()
        assert result == {}
        monkeypatch.setattr(config_mod, "_cfg", None)


class TestDeleteModelsGetCfg:
    def test_get_cfg_error_path(self, monkeypatch) -> None:
        """_get_cfg() returns {} when ConfigLoader raises."""
        import mcp.file.delete_models as models_mod

        monkeypatch.setattr(models_mod, "_cfg", None)
        with patch.object(ConfigLoader, "load", side_effect=OSError("no file")):
            result = models_mod._get_cfg()
        assert result == {}
        monkeypatch.setattr(models_mod, "_cfg", None)
