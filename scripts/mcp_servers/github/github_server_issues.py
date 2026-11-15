#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_server_issues.py

GitHub issues-operation router.

All five issue tools (list_issues, get_issue, create_issue, search_issues,
add_issue_comment) are dispatched through /v1/call_tool in github_server.py via the
shared dispatch table; this module keeps an empty APIRouter so github_server.py's
_include_routers() registers it unchanged.
"""

from fastapi import APIRouter

router = APIRouter()
