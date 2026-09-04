"""
Shared pytest fixtures for the llmagent test suite.
Adds scripts/ to sys.path so all project modules are importable without installation.
"""

import os
import sys
from pathlib import Path

# scripts/ and tools/ are not installed packages; add them to sys.path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# git/cicd/web_search MCP servers load their standalone *_mcp_server.toml at
# module import time, and those files reference ${ENV:...}-style auth tokens
# (mcpauth, 2026-09-04). resolve_env_ref() only requires the variable to be
# *set*, not non-empty -- default to "" (not a real token) so import doesn't
# fail during test collection, while preserving these servers' pre-existing
# empty-token accept-all behavior that many tests rely on.
os.environ.setdefault("MCP_GIT_AUTH_TOKEN", "")
os.environ.setdefault("MCP_CICD_AUTH_TOKEN", "")
os.environ.setdefault("MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN", "")
