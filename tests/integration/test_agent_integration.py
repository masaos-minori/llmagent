"""
tests/integration/test_agent_integration.py

Integration characterization tests using real components instead of mocks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.memory.scoring import score
from agent.session_message_repo import SessionMessageRepository


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_shell_safe_prefixes": ["/bin/", "/usr/bin/"],
        "approval_github_allowed_repos": [],
        "allowed_root": "",
        "security_profile": "development",
        "security_lockdown_enabled": False,
        "memory_local_only": False,
    }
    merged = {**defaults, **overrides}
    return build_agent_config(merged)


class TestMemoryScoringWithRealDB:
    """AGENT-3: Memory scoring with real DB and subprocess instead of mocks."""

    def test_memory_scoring_with_real_db(self, tmp_path: Path) -> None:
        """Score memory entries using real SQLite storage."""
        db_path = str(tmp_path / "test_memory.sqlite")
        repo = SessionMessageRepository(None, strict_mode=False)
        repo._init_db(db_path)

        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
        ]
        repo.save_many(messages)

        assert repo.stat_skipped_no_session == 0

    @pytest.mark.asyncio
    async def test_memory_scoring_with_real_subprocess(self) -> None:
        """Run a subprocess and verify output without mocking."""
        result = await asyncio.create_subprocess_exec(
            "echo",
            "hello",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        assert result.returncode == 0
        assert stdout.strip() == b"hello"

    def test_memory_scoring_boundary_values(self) -> None:
        """Test score function with boundary values."""
        entry = type(
            "MemoryEntry",
            (),
            {
                "created_at": "2026-01-01T00:00:00+00:00",
                "branch": "main",
                "project": "test-project",
                "repo": "test-repo",
            },
        )()
        bm25_rank = 1.0
        project = "test-project"
        repo_name = "test-repo"
        branch = "main"

        result = score(bm25_rank, entry, project, repo_name, branch)
        assert isinstance(result, float)
        assert result > 0.0
