"""Reader contract tests for ``agent.prompt_source`` (agentcfg005 row 12).

Covers the REQ-001 read boundary: the reader returns the frozen typed model,
the returned mapping is read-only and no mutable copy escapes it, name lookup
resolves ``default``, and the missing-file and missing-entry cases raise at the
read boundary with no silent default. Each case uses a temporary fixture
directory, not the committed ``registry/manifests/prompt_source.toml`` (that
inventory belongs to row 13).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from agent.prompt_source import PromptSource, PromptSourceError, load_prompt_source

# Fixture values copied from the current prompt content (AC-1: no prompt text
# is lost when the values move).
_DEFAULT_PROMPT = (
    "あなたは有能なエンジニアアシスタントです。必要に応じてツールを使って情報を収集し、"
    "正確に回答してください。"
)
_STRICT_PROMPT = (
    "あなたは厳格なエンジニアアシスタントです。事実のみを回答し、不確かな情報は「不明」と"
    "答えてください。ツールを積極的に使用して情報を確認してください。"
)
_CREATIVE_PROMPT = (
    "あなたは創造的なエンジニアアシスタントです。複数のアプローチや代替案を提案し、"
    "自由な発想で問題解決を支援してください。"
)


def _fixture_source(tmp_path: Path, entries: dict[str, str] | None = None) -> Path:
    """Write a prompt source under a temporary manifests/ directory."""
    content = (
        entries
        if entries is not None
        else {
            "default": _DEFAULT_PROMPT,
            "strict": _STRICT_PROMPT,
            "creative": _CREATIVE_PROMPT,
        }
    )
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    source = manifest_dir / "prompt_source.toml"
    source.write_text(
        "\n".join(f'{name} = "{value}"' for name, value in content.items()) + "\n",
        encoding="utf-8",
    )
    return source


class TestReaderContract:
    def test_reader_returns_frozen_typed_model(self, tmp_path: Path) -> None:
        source = load_prompt_source(_fixture_source(tmp_path))
        assert isinstance(source, PromptSource)
        assert dataclasses.is_dataclass(source)
        with pytest.raises(dataclasses.FrozenInstanceError):
            source.entries = {}  # type: ignore[misc]  # assignment must fail — proves the dataclass is frozen

    def test_returned_mapping_is_read_only(self, tmp_path: Path) -> None:
        source = load_prompt_source(_fixture_source(tmp_path))
        with pytest.raises(TypeError):
            source.entries["default"] = "mutated copy"

    def test_name_lookup_resolves_default(self, tmp_path: Path) -> None:
        source = load_prompt_source(_fixture_source(tmp_path))
        assert source.content("default") == _DEFAULT_PROMPT
        assert source.content("strict") == _STRICT_PROMPT
        assert source.content("creative") == _CREATIVE_PROMPT


class TestErrorBoundary:
    def test_missing_source_file_raises_at_read_boundary(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))
        with pytest.raises(PromptSourceError, match="not found"):
            load_prompt_source()

    def test_missing_default_entry_raises_with_no_silent_default(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture_source(tmp_path, {"strict": _STRICT_PROMPT})
        with pytest.raises(PromptSourceError, match="default"):
            load_prompt_source(fixture)


class TestPathResolution:
    def test_resolved_registry_directory_is_honoured(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """An explicit ``LLMAGENT_REGISTRY_DIR`` is honoured by the reader."""
        fixture = _fixture_source(tmp_path)
        monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))
        source = load_prompt_source()
        assert source.content("default") == _DEFAULT_PROMPT
        assert fixture.is_file()
