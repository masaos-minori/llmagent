#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_server_pull_requests.py

GitHub pull-request-operation router.

All six pull-request tools (list_pull_requests, get_pull_request,
create_pull_request, search_pull_requests, update_pull_request, merge_pull_request)
are dispatched through /v1/call_tool in github_server.py via the shared dispatch
table; this module keeps an empty APIRouter so github_server.py's _include_routers()
registers it unchanged.
"""

from fastapi import APIRouter

router = APIRouter()
