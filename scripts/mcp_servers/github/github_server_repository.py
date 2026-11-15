#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_server_repository.py

GitHub repository-operation router.

All six repository tools (search_repositories, list_branches, create_branch,
list_commits, get_commit, search_code) are dispatched through /v1/call_tool in
github_server.py via the shared dispatch table; this module keeps an empty
APIRouter so github_server.py's _include_routers() registers it unchanged.
"""

from fastapi import APIRouter

router = APIRouter()
