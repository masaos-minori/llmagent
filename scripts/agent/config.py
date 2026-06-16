"""agent/config.py -- Re-export stub for backward compatibility.

This module re-exports all public symbols from split sub-modules so that
existing imports continue to work without changes:

    from agent.config import AgentConfig, build_agent_config, LLMConfig, ...
    from agent.config import ConfigLoadError, load_config

New code should import directly from the sub-modules:

    from agent.config_dataclasses import AgentConfig, LLMConfig, RAGConfig, ...
    from agent.config_builders import build_agent_config, load_config, ConfigLoadError
"""

from __future__ import annotations

# Re-export builders + exception
from agent.config_builders import (  # noqa: F401
    _CONFIG_DIR,
    ConfigLoadError,
    _build_approval_config,
    _build_llm_config,
    _build_mcp_servers,
    _build_memory_config,
    _build_rag_config,
    _build_tool_config,
    build_agent_config,
    load_config,
)

# Re-export dataclasses
from agent.config_dataclasses import (  # noqa: F401
    AgentConfig,
    ApprovalConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
    ObservabilityConfig,
    RAGConfig,
    ToolConfig,
)

__all__ = [
    "AgentConfig",
    "ApprovalConfig",
    "LLMConfig",
    "MCPConfig",
    "MemoryConfig",
    "ObservabilityConfig",
    "RAGConfig",
    "ToolConfig",
    "_CONFIG_DIR",
    "_build_approval_config",
    "_build_llm_config",
    "_build_memory_config",
    "_build_mcp_servers",
    "_build_rag_config",
    "_build_tool_config",
    "build_agent_config",
    "ConfigLoadError",
    "load_config",
]
